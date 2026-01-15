"""
View para receber webhooks da AbacatePay (PAGAMENTOS)

Implementação conforme documentação oficial:
https://docs.abacatepay.com/pages/webhooks
"""

import json
import hmac
import hashlib
import base64
import logging
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.http import JsonResponse
from django.conf import settings

from ..models import AbacatePayBilling, AbacatePayPayment

logger = logging.getLogger(__name__)

# Chave pública HMAC da AbacatePay (conforme documentação)
# Carregada do settings (que vem de .env/secrets)
ABACATEPAY_PUBLIC_KEY = getattr(settings, "ABACATEPAY_PUBLIC_KEY", None) or ""

ABACATEPAY_WEBHOOK_SECRET = getattr(settings, "ABACATEPAY_WEBHOOK_SECRET", "")


def verify_webhook_signature(raw_body: str, signature_from_header: str) -> bool:
    """
    Verifica a assinatura HMAC do webhook usando a chave pública.

    Implementação exata conforme documentação da AbacatePay:
    https://docs.abacatepay.com/pages/webhooks

    Args:
        raw_body: Corpo bruto da requisição como string (utf-8)
        signature_from_header: Assinatura recebida no header X-Webhook-Signature (base64)

    Returns:
        True se a assinatura for válida
    """
    if not ABACATEPAY_PUBLIC_KEY:
        logger.error(
            "ABACATEPAY_PUBLIC_KEY não configurada. Configure a variável de ambiente ABACATEPAY_PUBLIC_KEY"
        )
        return False

    if not signature_from_header:
        logger.warning("Assinatura não fornecida no header")
        return False

    try:
        # Converte o corpo para buffer (conforme documentação Node.js)
        body_buffer = raw_body.encode("utf-8")

        # Calcula HMAC-SHA256 do body_buffer usando a chave pública
        # Conforme documentação: createHmac("sha256", ABACATEPAY_PUBLIC_KEY).update(bodyBuffer).digest("base64")
        hmac_digest = hmac.new(
            ABACATEPAY_PUBLIC_KEY.encode("utf-8"),
            body_buffer,
            hashlib.sha256,
        ).digest()

        # Converte para base64 (conforme documentação)
        expected_sig = base64.b64encode(hmac_digest).decode("utf-8")

        # Converte para bytes para comparação timing-safe
        expected_bytes = expected_sig.encode("utf-8")
        received_bytes = signature_from_header.encode("utf-8")

        # Compara usando timing-safe comparison (conforme documentação)
        if len(expected_bytes) != len(received_bytes):
            return False

        return hmac.compare_digest(expected_bytes, received_bytes)
    except Exception as e:
        logger.error(f"Erro ao verificar assinatura: {e}", exc_info=True)
        return False


def verify_webhook_secret(request) -> bool:
    """
    Verifica o secret do webhook via query parameter (método alternativo)

    Args:
        request: Objeto request do Django

    Returns:
        True se o secret for válido
    """
    if not ABACATEPAY_WEBHOOK_SECRET:
        logger.warning("ABACATEPAY_WEBHOOK_SECRET não configurado")
        return True

    webhook_secret = request.GET.get("webhookSecret")
    if not webhook_secret:
        return False

    return hmac.compare_digest(webhook_secret, ABACATEPAY_WEBHOOK_SECRET)


@csrf_exempt
@require_POST
def AbacatePayWebhookView(request):
    """
    Endpoint para receber webhooks da AbacatePay

    Implementação conforme documentação:
    https://docs.abacatepay.com/pages/webhooks

    Segurança:
    - Validação via secret na URL (webhookSecret query parameter)
    - Validação via assinatura HMAC no header X-Webhook-Signature

    Eventos suportados:
    - billing.paid: Cobrança foi paga
    - withdraw.done: Saque concluído
    - withdraw.failed: Saque falhou

    IMPORTANTE: O corpo bruto deve ser lido antes de qualquer parsing.
    O Django já faz isso automaticamente com request.body.
    """
    try:
        # Lê o corpo bruto como string (importante para HMAC)
        raw_body_str = request.body.decode("utf-8")
        signature = request.headers.get("X-Webhook-Signature", "")

        # Validação em duas camadas (conforme documentação):
        # 1. Secret na URL (método simples)
        # 2. Assinatura HMAC no header (integridade do corpo)
        signature_valid = False

        # Se houver assinatura no header, valida via HMAC
        if signature:
            signature_valid = verify_webhook_signature(raw_body_str, signature)
            if not signature_valid:
                logger.warning("Assinatura HMAC inválida")
        else:
            # Se não houver assinatura, valida via secret na URL
            signature_valid = verify_webhook_secret(request)
            if not signature_valid:
                logger.warning("Secret do webhook inválido ou ausente")

        if not signature_valid:
            logger.warning(
                f"Webhook rejeitado - IP: {request.META.get('REMOTE_ADDR')}, "
                f"Signature presente: {bool(signature)}"
            )
            return JsonResponse({"error": "Invalid signature"}, status=401)

        # Parse do JSON após validação
        data = json.loads(raw_body_str)
        event_type = data.get("event")
        event_data = data.get("data", {})
        dev_mode = data.get("devMode", False)
        log_id = data.get("id", "")

        logger.info(
            f"Webhook recebido: event={event_type}, id={log_id}, devMode={dev_mode}"
        )

        if event_type == "billing.paid":
            """
            Evento: billing.paid
            Disparado quando um pagamento é confirmado.

            O payload varia dependendo da origem:
            - PIX QR Code: contém pixQrCode
            - Cobrança: contém billing com billing_id

            Payload exemplo (PIX):
            {
                "id": "log_12345abcdef",
                "data": {
                    "payment": {"amount": 1000, "fee": 80, "method": "PIX"},
                    "pixQrCode": {
                        "amount": 1000,
                        "id": "pix_char_mXTWdj6sABWnc4uL2Rh1r6tb",
                        "kind": "PIX",
                        "status": "PAID"
                    }
                },
                "devMode": false,
                "event": "billing.paid"
            }

            Payload exemplo (Cobrança):
            {
                "id": "log_12345abcdef",
                "data": {
                    "payment": {"amount": 1000, "fee": 80, "method": "PIX"},
                    "billing": {
                        "id": "bill_QgW1BT3uzaDGR3ANKgmmmabZ",
                        "amount": 1000,
                        "status": "PAID",
                        ...
                    }
                },
                "devMode": false,
                "event": "billing.paid"
            }
            """
            pix_qrcode = event_data.get("pixQrCode", {})
            billing_data = event_data.get("billing", {})
            payment = event_data.get("payment", {})

            payment_amount_cents = payment.get("amount", 0) if payment else 0
            pix_id = pix_qrcode.get("id") if pix_qrcode else None
            billing_id = billing_data.get("id") if billing_data else None

            logger.info(
                f"Processando billing.paid - Billing ID: {billing_id}, "
                f"PIX ID: {pix_id}, Amount: {payment_amount_cents}"
            )

            from decimal import Decimal

            billing_found = None

            # Primeiro, tenta encontrar pelo billing_id se presente
            if billing_id:
                try:
                    billing_found = AbacatePayBilling.objects.get(billing_id=billing_id)
                    logger.info(
                        f"Encontrada cobrança pelo billing_id: {billing_found.billing_id}"
                    )
                except AbacatePayBilling.DoesNotExist:
                    logger.warning(
                        f"Billing ID {billing_id} não encontrado no banco de dados"
                    )

            # Se não encontrou pelo billing_id e há valor, tenta pelo valor
            if not billing_found and payment_amount_cents > 0:
                payment_amount = Decimal(payment_amount_cents) / 100

                pending_billings = AbacatePayBilling.objects.filter(
                    status="PENDING", amount=payment_amount
                ).order_by("-created_at")

                if pending_billings.count() == 1:
                    billing_found = pending_billings.first()
                    logger.info(
                        f"Encontrada cobrança única: {billing_found.billing_id}"
                    )
                elif pending_billings.count() > 1:
                    from ..services import AbacatePayService

                    list_response = AbacatePayService.list_billings()

                    if not list_response.get("error"):
                        api_billings = list_response.get("data", [])
                        for api_billing in api_billings:
                            api_billing_id = api_billing.get("id")
                            api_status = api_billing.get("status")
                            api_amount = api_billing.get("amount", 0)

                            if (
                                api_status == "PAID"
                                and api_amount == payment_amount_cents
                            ):
                                try:
                                    billing_found = AbacatePayBilling.objects.get(
                                        billing_id=api_billing_id
                                    )
                                    logger.info(
                                        f"Encontrada cobrança paga na API: {billing_found.billing_id}"
                                    )
                                    break
                                except AbacatePayBilling.DoesNotExist:
                                    continue

                    if not billing_found:
                        billing_found = pending_billings.first()
                        logger.info(
                            f"Usando cobrança mais recente: {billing_found.billing_id}"
                        )

            if not billing_found:
                logger.warning(
                    f"Cobrança não encontrada para o webhook. "
                    f"Log ID: {log_id}, Amount: {payment_amount_cents}, PIX ID: {pix_id}"
                )
                return JsonResponse(
                    {
                        "status": "ok",
                        "message": "Billing not found but webhook processed",
                    }
                )

            billing = billing_found

            billing.status = "PAID"
            billing.save()

            if billing.order.status != "paid":
                billing.order.status = "paid"
                billing.order.paid_at = timezone.now()
                billing.order.save()
                logger.info(f"Pedido {billing.order.order_id} marcado como pago")

            payment_obj = billing.payments.first()
            if not payment_obj:
                payment_amount = (
                    Decimal(payment.get("amount", 0)) / 100
                    if payment
                    else billing.amount
                )
                payment_obj = AbacatePayPayment.objects.create(
                    billing=billing,
                    order=billing.order,
                    amount=payment_amount,
                    status="PAID",
                    payment_method=payment.get("method", "PIX") if payment else "PIX",
                    paid_at=timezone.now(),
                )
            else:
                payment_obj.status = "PAID"
                payment_obj.paid_at = timezone.now()
                payment_obj.payment_method = (
                    payment.get("method", "PIX")
                    if payment
                    else payment_obj.payment_method or "PIX"
                )
                payment_obj.save()

            logger.info(f"Cobrança {billing.billing_id} marcada como paga via webhook")

        elif event_type == "withdraw.done":
            """
            Evento: withdraw.done
            Disparado quando um saque é concluído com sucesso.

            Payload:
            {
                "id": "log_12345abcdef",
                "data": {
                    "transaction": {
                        "id": "tran_123456",
                        "status": "COMPLETE",
                        "devMode": false,
                        "receiptUrl": "https://abacatepay.com/receipt/tran_123456",
                        "kind": "WITHDRAW",
                        "amount": 5000,  // em centavos
                        "platformFee": 80,
                        "externalId": "withdraw-1234",
                        "createdAt": "2025-03-24T21:50:20.772Z",
                        "updatedAt": "2025-03-24T21:55:20.772Z"
                    }
                },
                "devMode": false,
                "event": "withdraw.done"
            }
            """
            transaction = event_data.get("transaction", {})
            transaction_id = transaction.get("id")
            external_id = transaction.get("externalId")
            amount_cents = transaction.get("amount", 0)
            status = transaction.get("status")

            logger.info(
                f"Saque concluído: transaction_id={transaction_id}, "
                f"external_id={external_id}, amount={amount_cents}, status={status}"
            )

            # TODO: Implementar lógica de processamento do saque concluído
            # Exemplo: atualizar status de saque no banco de dados, notificar usuário, etc.

        elif event_type == "withdraw.failed":
            """
            Evento: withdraw.failed
            Disparado quando um saque não é concluído.

            Payload:
            {
                "id": "log_12345abcdef",
                "data": {
                    "transaction": {
                        "id": "tran_789012",
                        "status": "CANCELLED",
                        "devMode": false,
                        "receiptUrl": "https://abacatepay.com/receipt/tran_789012",
                        "kind": "WITHDRAW",
                        "amount": 3000,  // em centavos
                        "platformFee": 0,
                        "externalId": "withdraw-5678",
                        "createdAt": "2025-03-24T22:00:20.772Z",
                        "updatedAt": "2025-03-24T22:05:20.772Z"
                    }
                },
                "devMode": false,
                "event": "withdraw.failed"
            }
            """
            transaction = event_data.get("transaction", {})
            transaction_id = transaction.get("id")
            external_id = transaction.get("externalId")
            amount_cents = transaction.get("amount", 0)
            status = transaction.get("status")

            logger.warning(
                f"Saque falhado: transaction_id={transaction_id}, "
                f"external_id={external_id}, amount={amount_cents}, status={status}"
            )

            # TODO: Implementar lógica de processamento do saque falhado
            # Exemplo: atualizar status de saque no banco de dados, notificar usuário, reverter saldo, etc.

        else:
            logger.warning(f"Tipo de evento não reconhecido: {event_type}")

        return JsonResponse({"status": "ok", "received": True})

    except json.JSONDecodeError as e:
        logger.error(f"Erro ao fazer parse do JSON do webhook: {e}")
        return JsonResponse({"error": "Invalid JSON"}, status=400)

    except Exception as e:
        logger.error(f"Erro ao processar webhook: {e}", exc_info=True)
        return JsonResponse({"error": "Internal server error"}, status=500)
