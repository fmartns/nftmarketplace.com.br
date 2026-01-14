"""
Modelos para o sistema de pedidos
"""

from django.db import models
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.conf import settings
from django.core.validators import MinValueValidator
from decimal import Decimal

from .utils import generate_order_id


class Coupon(models.Model):
    """
    Modelo para cupons de desconto
    """

    code = models.CharField(
        max_length=50,
        unique=True,
        db_index=True,
        help_text="Código do cupom (ex: DESCONTO20)",
    )
    description = models.TextField(
        blank=True,
        help_text="Descrição do cupom",
    )

    DISCOUNT_TYPE_CHOICES = [
        ("percentage", "Percentual"),
        ("fixed", "Valor fixo"),
    ]

    discount_type = models.CharField(
        max_length=20,
        choices=DISCOUNT_TYPE_CHOICES,
        default="percentage",
        help_text="Tipo de desconto",
    )

    discount_value = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.01"))],
        help_text="Valor do desconto (percentual ou valor fixo)",
    )

    min_purchase_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal("0.00"),
        validators=[MinValueValidator(Decimal("0.00"))],
        help_text="Valor mínimo de compra para usar o cupom",
    )

    max_discount_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(Decimal("0.01"))],
        help_text="Valor máximo de desconto (apenas para percentual, opcional)",
    )

    max_uses = models.IntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(1)],
        help_text="Número máximo de usos (null = ilimitado)",
    )

    uses_count = models.IntegerField(
        default=0,
        help_text="Número de vezes que o cupom foi usado",
    )

    is_active = models.BooleanField(
        default=True,
        help_text="Se o cupom está ativo",
    )

    valid_from = models.DateTimeField(
        help_text="Data/hora de início da validade",
    )

    valid_until = models.DateTimeField(
        help_text="Data/hora de fim da validade",
    )

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="created_coupons",
        help_text="Usuário que criou o cupom",
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Cupom"
        verbose_name_plural = "Cupons"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["code"]),
            models.Index(fields=["is_active"]),
        ]

    def __str__(self):
        return f"{self.code} ({self.discount_value}%{'OFF' if self.discount_type == 'percentage' else 'R$'})"

    def is_valid(self):
        """Verifica se o cupom é válido (ativo, dentro do prazo e não excedeu usos)"""
        from django.utils import timezone

        if not self.is_active:
            return False

        now = timezone.now()
        if now < self.valid_from or now > self.valid_until:
            return False

        if self.max_uses is not None and self.uses_count >= self.max_uses:
            return False

        return True

    def calculate_discount(self, amount: Decimal) -> Decimal:
        """
        Calcula o desconto aplicado ao valor
        Retorna o valor do desconto
        """
        if not self.is_valid():
            return Decimal("0.00")

        if amount < self.min_purchase_amount:
            return Decimal("0.00")

        if self.discount_type == "percentage":
            discount = amount * (self.discount_value / Decimal("100.00"))
            if self.max_discount_amount:
                discount = min(discount, self.max_discount_amount)
        else:  # fixed
            discount = min(self.discount_value, amount)

        return discount.quantize(Decimal("0.01"))


class Order(models.Model):
    """
    Modelo principal para pedidos
    """

    order_id = models.CharField(
        max_length=10,
        unique=True,
        db_index=True,
        help_text="ID único do pedido (ex: #KFNSFG)",
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="orders",
        help_text="Usuário que fez o pedido",
    )

    STATUS_CHOICES = [
        ("pending", "Pendente"),
        ("paid", "Pago"),
        ("processing", "Processando"),
        ("delivered", "Entregue"),
        ("cancelled", "Cancelado"),
        ("refunded", "Reembolsado"),
    ]

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="pending",
        db_index=True,
        help_text="Status do pedido",
    )

    subtotal = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.01"))],
        help_text="Subtotal dos itens (sem desconto)",
    )

    discount_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal("0.00"),
        validators=[MinValueValidator(Decimal("0.00"))],
        help_text="Valor do desconto aplicado",
    )

    total = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.01"))],
        help_text="Valor total do pedido (subtotal - desconto)",
    )

    coupon = models.ForeignKey(
        Coupon,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="orders",
        help_text="Cupom aplicado (se houver)",
    )

    paid_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Data/hora em que o pedido foi pago",
    )

    delivered = models.BooleanField(
        default=False,
        db_index=True,
        help_text="Se o pedido foi entregue pelo administrador",
    )

    delivered_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Data/hora em que o pedido foi entregue",
    )

    delivered_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="delivered_orders",
        help_text="Administrador que entregou o pedido",
    )

    notes = models.TextField(
        blank=True,
        help_text="Observações do pedido",
    )

    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Pedido"
        verbose_name_plural = "Pedidos"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["order_id"]),
            models.Index(fields=["status"]),
            models.Index(fields=["user"]),
            models.Index(fields=["delivered"]),
        ]

    def __str__(self):
        return f"Pedido {self.order_id} - {self.user.username} - {self.get_status_display()}"

    def save(self, *args, **kwargs):
        """Gera order_id automaticamente se não existir"""
        if not self.order_id:
            while True:
                order_id = generate_order_id()
                if not Order.objects.filter(order_id=order_id).exists():
                    self.order_id = order_id
                    break
        super().save(*args, **kwargs)

    def mark_as_delivered(self, admin_user):
        """Marca o pedido como entregue"""
        from django.utils import timezone

        self.delivered = True
        self.delivered_at = timezone.now()
        self.delivered_by = admin_user
        if self.status == "paid":
            self.status = "delivered"
        self.save()


class OrderItem(models.Model):
    """
    Modelo para itens de um pedido
    Suporta tanto legacy.Item quanto nft.NFTItem usando GenericForeignKey
    """

    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name="items",
        help_text="Pedido ao qual este item pertence",
    )

    content_type = models.ForeignKey(
        ContentType,
        on_delete=models.PROTECT,
        help_text="Tipo do item (legacy.Item ou nft.NFTItem)",
    )

    object_id = models.PositiveIntegerField(
        help_text="ID do item",
    )

    item = GenericForeignKey("content_type", "object_id")

    quantity = models.IntegerField(
        default=1,
        validators=[MinValueValidator(1)],
        help_text="Quantidade do item",
    )

    unit_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.01"))],
        help_text="Preço unitário do item no momento da compra",
    )

    total_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.01"))],
        help_text="Preço total (unitário * quantidade)",
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Item do Pedido"
        verbose_name_plural = "Itens do Pedido"
        ordering = ["order", "created_at"]
        indexes = [
            models.Index(fields=["order"]),
            models.Index(fields=["content_type", "object_id"]),
        ]

    def __str__(self):
        return f"{self.order.order_id} - {self.item} x{self.quantity}"

    def save(self, *args, **kwargs):
        """Calcula total_price automaticamente"""
        self.total_price = self.unit_price * self.quantity
        super().save(*args, **kwargs)
