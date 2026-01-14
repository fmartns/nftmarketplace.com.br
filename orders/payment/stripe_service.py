"""
Serviço de integração com Stripe para processamento de pagamentos
"""

import stripe
import logging
from decimal import Decimal
from typing import Optional, Dict, Any
from django.conf import settings

logger = logging.getLogger(__name__)

# Configuração do Stripe
stripe.api_key = getattr(settings, "STRIPE_SECRET_KEY", "")


class StripeService:
    """
    Serviço para gerenciar pagamentos com Stripe
    """

    @staticmethod
    def create_payment_intent(
        amount: Decimal,
        currency: str = "brl",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Cria um PaymentIntent no Stripe

        Args:
            amount: Valor em centavos (ou menor unidade da moeda)
            currency: Moeda (padrão: 'brl')
            metadata: Metadados adicionais (ex: order_id)

        Returns:
            Dict com payment_intent_id e client_secret
        """
        try:
            # Converte Decimal para centavos (int)
            amount_cents = int(amount * 100)

            payment_intent = stripe.PaymentIntent.create(
                amount=amount_cents,
                currency=currency.lower(),
                metadata=metadata or {},
                automatic_payment_methods={
                    "enabled": True,
                },
            )

            return {
                "payment_intent_id": payment_intent.id,
                "client_secret": payment_intent.client_secret,
                "status": payment_intent.status,
            }

        except stripe.error.StripeError as e:
            logger.error(f"Erro ao criar PaymentIntent no Stripe: {e}")
            raise

    @staticmethod
    def retrieve_payment_intent(payment_intent_id: str) -> Dict[str, Any]:
        """
        Recupera informações de um PaymentIntent

        Args:
            payment_intent_id: ID do PaymentIntent

        Returns:
            Dict com informações do PaymentIntent
        """
        try:
            payment_intent = stripe.PaymentIntent.retrieve(payment_intent_id)

            return {
                "id": payment_intent.id,
                "status": payment_intent.status,
                "amount": payment_intent.amount
                / 100,  # Converte centavos para valor real
                "currency": payment_intent.currency,
                "metadata": payment_intent.metadata,
            }

        except stripe.error.StripeError as e:
            logger.error(f"Erro ao recuperar PaymentIntent no Stripe: {e}")
            raise

    @staticmethod
    def cancel_payment_intent(payment_intent_id: str) -> Dict[str, Any]:
        """
        Cancela um PaymentIntent

        Args:
            payment_intent_id: ID do PaymentIntent

        Returns:
            Dict com informações do PaymentIntent cancelado
        """
        try:
            payment_intent = stripe.PaymentIntent.cancel(payment_intent_id)

            return {
                "id": payment_intent.id,
                "status": payment_intent.status,
            }

        except stripe.error.StripeError as e:
            logger.error(f"Erro ao cancelar PaymentIntent no Stripe: {e}")
            raise

    @staticmethod
    def create_refund(
        payment_intent_id: str,
        amount: Optional[Decimal] = None,
        reason: str = "requested_by_customer",
    ) -> Dict[str, Any]:
        """
        Cria um reembolso

        Args:
            payment_intent_id: ID do PaymentIntent
            amount: Valor a reembolsar (None = reembolso total)
            reason: Motivo do reembolso

        Returns:
            Dict com informações do reembolso
        """
        try:
            refund_data = {
                "payment_intent": payment_intent_id,
                "reason": reason,
            }

            if amount:
                refund_data["amount"] = int(amount * 100)  # Converte para centavos

            refund = stripe.Refund.create(**refund_data)

            return {
                "id": refund.id,
                "amount": refund.amount / 100,  # Converte centavos para valor real
                "status": refund.status,
            }

        except stripe.error.StripeError as e:
            logger.error(f"Erro ao criar reembolso no Stripe: {e}")
            raise
