"""
Comando para verificar e reprocessar status de pagamentos no AbacatePay
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from payments.models import AbacatePayBilling, AbacatePayPayment
from payments.services import AbacatePayService
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Verifica e atualiza o status de pagamentos no AbacatePay"

    def add_arguments(self, parser):
        parser.add_argument(
            "--billing-id",
            type=str,
            help="ID da cobrança (billing_id) para verificar um pagamento específico",
        )
        parser.add_argument(
            "--order-id",
            type=str,
            help="ID do pedido (order_id) para verificar um pagamento específico",
        )
        parser.add_argument(
            "--all-pending",
            action="store_true",
            help="Verifica todos os pagamentos pendentes",
        )

    def handle(self, *args, **options):
        billing_id = options.get("billing_id")
        order_id = options.get("order_id")
        all_pending = options.get("all_pending")

        if billing_id:
            self.check_single_billing(billing_id)
        elif order_id:
            self.check_by_order_id(order_id)
        elif all_pending:
            self.check_all_pending()
        else:
            self.stdout.write(
                self.style.ERROR(
                    "Você deve fornecer --billing-id, --order-id ou --all-pending"
                )
            )
            self.stdout.write("\nExemplos:")
            self.stdout.write("  python manage.py check_payment --billing-id BILLING123")
            self.stdout.write("  python manage.py check_payment --order-id #ABC123")
            self.stdout.write("  python manage.py check_payment --all-pending")

    def check_single_billing(self, billing_id: str):
        """Verifica um pagamento específico por billing_id"""
        self.stdout.write(f"Verificando cobrança: {billing_id}")

        try:
            billing = AbacatePayBilling.objects.get(billing_id=billing_id)
        except AbacatePayBilling.DoesNotExist:
            self.stdout.write(
                self.style.ERROR(f"Cobrança não encontrada: {billing_id}")
            )
            return

        self.update_billing_status(billing)

    def check_by_order_id(self, order_id: str):
        """Verifica um pagamento específico por order_id"""
        self.stdout.write(f"Verificando pedido: {order_id}")

        try:
            from orders.models import Order
            order = Order.objects.get(order_id=order_id)
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"Pedido não encontrado: {order_id} - {e}")
            )
            return

        try:
            billing = AbacatePayBilling.objects.get(order=order)
        except AbacatePayBilling.DoesNotExist:
            self.stdout.write(
                self.style.ERROR(f"Nenhuma cobrança encontrada para o pedido: {order_id}")
            )
            return
        except AbacatePayBilling.MultipleObjectsReturned:
            self.stdout.write(
                self.style.WARNING(
                    f"Múltiplas cobranças encontradas para o pedido: {order_id}"
                )
            )
            billings = AbacatePayBilling.objects.filter(order=order)
            for billing in billings:
                self.update_billing_status(billing)
            return

        self.update_billing_status(billing)

    def check_all_pending(self):
        """Verifica todos os pagamentos pendentes"""
        self.stdout.write("Verificando todos os pagamentos pendentes...")

        pending_billings = AbacatePayBilling.objects.filter(
            status__in=["PENDING", "EXPIRED"]
        )

        count = pending_billings.count()
        self.stdout.write(f"Encontrados {count} pagamentos pendentes")

        updated = 0
        for billing in pending_billings:
            if self.update_billing_status(billing, verbose=False):
                updated += 1

        self.stdout.write(
            self.style.SUCCESS(f"\nAtualizados {updated} de {count} pagamentos")
        )

    def update_billing_status(self, billing: AbacatePayBilling, verbose: bool = True) -> bool:
        """Atualiza o status de uma cobrança consultando a API"""
        if verbose:
            self.stdout.write(
                f"\nCobrança: {billing.billing_id} | Status atual: {billing.status}"
            )

        # Tenta usar /pix/check primeiro (endpoint que funciona)
        status_response = AbacatePayService.check_pix_status(billing.billing_id)

        # Se /pix/check falhar, tenta /billing/get como fallback
        if status_response.get("error"):
            if verbose:
                self.stdout.write(
                    self.style.WARNING(
                        f"Tentando método alternativo para verificar status..."
                    )
                )
            status_response = AbacatePayService.get_billing_status(billing.billing_id)

        if status_response.get("error"):
            error_msg = status_response["error"].get("message", "Erro desconhecido")
            if verbose:
                self.stdout.write(
                    self.style.ERROR(f"Erro ao consultar API: {error_msg}")
                )
            return False

        status_data = status_response.get("data", {})
        new_status = status_data.get("status", billing.status)

        if verbose:
            self.stdout.write(f"Status na API: {new_status}")

        # Atualiza o status se mudou
        if new_status != billing.status:
            old_status = billing.status
            billing.status = new_status
            billing.save()

            if verbose:
                self.stdout.write(
                    self.style.SUCCESS(
                        f"Status atualizado: {old_status} → {new_status}"
                    )
                )

            # Se foi pago, atualiza o pedido
            if new_status == "PAID" and billing.order.status != "paid":
                billing.order.status = "paid"
                billing.order.paid_at = timezone.now()
                billing.order.save()

                # Atualiza o pagamento associado
                payment = billing.payments.first()
                if payment:
                    payment.status = "PAID"
                    payment.paid_at = timezone.now()
                    payment.save()

                if verbose:
                    self.stdout.write(
                        self.style.SUCCESS(
                            f"Pedido {billing.order.order_id} marcado como pago!"
                        )
                    )

            return True
        else:
            if verbose:
                self.stdout.write("Status já está atualizado")
            return False
