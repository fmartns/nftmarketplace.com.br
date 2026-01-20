"""
Views para pedidos
"""

from decimal import Decimal
from rest_framework import status, generics
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from ..models import Order, OrderItem, Coupon
from ..serializers import OrderSerializer, OrderCreateSerializer
from ..docs import (
    orders_list_schema,
    orders_create_schema,
    orders_detail_schema,
)


class OrderListCreateView(generics.ListCreateAPIView):
    """
    View para listar e criar pedidos
    """

    permission_classes = [IsAuthenticated]
    serializer_class = OrderSerializer

    def get_queryset(self):
        """Retorna apenas os pedidos do usuário autenticado"""
        # Prevent error when user is AnonymousUser during schema generation
        if getattr(self, "swagger_fake_view", False):
            return Order.objects.none()
        if not self.request.user.is_authenticated:
            return Order.objects.none()
        return (
            Order.objects.filter(user=self.request.user)
            .prefetch_related("items", "coupon")
            .order_by("-created_at")
        )

    @orders_list_schema
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    @orders_create_schema
    def post(self, request, *args, **kwargs):
        """Cria um novo pedido"""
        serializer = OrderCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        validated_data = serializer.validated_data

        items_data = validated_data["items"]
        coupon_code = validated_data.get("coupon_code")
        notes = validated_data.get("notes", "")

        # Segunda validação: recalcula preços dos itens para garantir que estão atualizados
        import logging

        logger = logging.getLogger(__name__)

        for item_data in items_data:
            original_price = item_data["unit_price"]

            # Recalcula o preço atual do item
            if item_data["content_type"].model == "nftitem":
                # Para NFTs, busca o preço atualizado da API
                try:
                    from nft.models import NFTItem
                    from nft.services import fetch_min_listing_prices

                    nft_item = NFTItem.objects.get(id=item_data["object_id"])
                    if nft_item.product_code:
                        # Busca o preço mínimo atualizado
                        current_prices = fetch_min_listing_prices(nft_item.product_code)
                        if current_prices:
                            _, _, current_price_brl = current_prices
                            # Arredonda para 2 casas decimais (igual ao last_price_brl do modelo)
                            # Isso garante que o preço seja exatamente o mesmo exibido no frontend
                            from decimal import ROUND_HALF_UP

                            current_price_brl_rounded = current_price_brl.quantize(
                                Decimal("0.01"), rounding=ROUND_HALF_UP
                            )
                            # Atualiza o preço no item_data com o preço recalculado e arredondado
                            item_data["unit_price"] = current_price_brl_rounded

                            # Log se houver diferença significativa (mais de 1%)
                            # Usa o valor arredondado para comparação
                            price_diff = abs(
                                float(current_price_brl_rounded - original_price)
                            )
                            if price_diff > float(original_price * Decimal("0.01")):
                                logger.warning(
                                    f"Preço recalculado para NFT {nft_item.product_code}: "
                                    f"Original: R$ {original_price}, Atualizado: R$ {current_price_brl_rounded}, "
                                    f"Diferença: R$ {price_diff:.2f}"
                                )
                        else:
                            # Se não conseguir buscar preço atualizado, mantém o do banco
                            logger.warning(
                                f"Não foi possível recalcular preço para NFT {nft_item.product_code}, "
                                f"usando preço do banco: R$ {original_price}"
                            )
                except Exception as e:
                    logger.error(
                        f"Erro ao recalcular preço do NFT {item_data['object_id']}: {e}",
                        exc_info=True,
                    )
                    # Em caso de erro, mantém o preço original
            elif item_data["content_type"].model == "item":
                # Para itens legacy, apenas verifica se o preço no banco está atualizado
                try:
                    from legacy.models import Item

                    legacy_item = Item.objects.get(id=item_data["object_id"])
                    current_price = legacy_item.last_price
                    if current_price != original_price:
                        item_data["unit_price"] = current_price
                        logger.warning(
                            f"Preço atualizado para item legacy {legacy_item.id}: "
                            f"Original: R$ {original_price}, Atualizado: R$ {current_price}"
                        )
                except Exception as e:
                    logger.error(
                        f"Erro ao verificar preço do item legacy {item_data['object_id']}: {e}",
                        exc_info=True,
                    )

        # Calcula subtotal com os preços recalculados
        subtotal = Decimal("0.00")
        for item_data in items_data:
            unit_price = item_data["unit_price"]
            quantity = item_data["quantity"]
            subtotal += unit_price * quantity

        # Aplica cupom se fornecido
        coupon = None
        discount_amount = Decimal("0.00")
        if coupon_code:
            try:
                coupon = Coupon.objects.get(code=coupon_code)
                discount_amount = coupon.calculate_discount(subtotal)
                # Incrementa contador de usos
                coupon.uses_count += 1
                coupon.save()
            except Coupon.DoesNotExist:
                pass

        # Calcula total
        total = subtotal - discount_amount
        if total < Decimal("0.01"):
            return Response(
                {"error": "Valor total do pedido deve ser maior que R$ 0,01."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Cria o pedido
        order = Order.objects.create(
            user=request.user,
            subtotal=subtotal,
            discount_amount=discount_amount,
            total=total,
            coupon=coupon,
            notes=notes,
            status="pending",
        )

        # Cria os itens do pedido
        for item_data in items_data:
            OrderItem.objects.create(
                order=order,
                content_type=item_data["content_type"],
                object_id=item_data["object_id"],
                quantity=item_data["quantity"],
                unit_price=item_data["unit_price"],
            )

        # Agenda task para verificar e cancelar pedido se não for pago em 5 minutos
        from ..tasks import check_and_cancel_order

        check_and_cancel_order.apply_async(
            args=[order.id],
            countdown=60 * 5,  # Executa após 5 minutos (300 segundos)
        )

        # Envia email de pedido criado
        from ..emails import send_order_created_email

        send_order_created_email(order)

        # Pagamento será processado via AbacatePay (criar billing separadamente)

        # Retorna o pedido criado
        response_serializer = OrderSerializer(order)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)


class OrderDetailView(generics.RetrieveAPIView):
    """
    View para detalhes de um pedido
    """

    permission_classes = [IsAuthenticated]
    serializer_class = OrderSerializer
    lookup_field = "order_id"
    lookup_url_kwarg = "order_id"

    def get_queryset(self):
        """Retorna apenas os pedidos do usuário autenticado"""
        return Order.objects.filter(user=self.request.user).prefetch_related(
            "items", "coupon"
        )

    def get_object(self):
        """
        Override para decodificar o order_id da URL corretamente
        """
        from urllib.parse import unquote
        from rest_framework.exceptions import NotFound

        order_id = self.kwargs.get(self.lookup_url_kwarg)

        if order_id:
            order_id = unquote(order_id)
            if not order_id.startswith("#"):
                order_id = f"#{order_id}"

        queryset = self.get_queryset()
        try:
            obj = queryset.get(order_id=order_id)
            return obj
        except Order.DoesNotExist:
            raise NotFound(f"Pedido com ID '{order_id}' não encontrado.")

    @orders_detail_schema
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)
