"""
View para receber webhooks da AbacatePay (PAGAMENTOS)
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

ABACATEPAY_PUBLIC_KEY = getattr(settings, "ABACATEPAY_PUBLIC_KEY", None)

ABACATEPAY_WEBHOOK_SECRET = getattr(settings, "ABACATEPAY_WEBHOOK_SECRET", "")


def verify_webhook_signature(raw_body: bytes, signature_from_header: str) -> bool:
    """
    Verifica a assinatura HMAC do webhook usando a chave pública.

    Implementação conforme documentação da AbacatePay:
    - Calcula HMAC-SHA256 do raw_body usando a chave pública
    - Converte para base64
    - Compara com a assinatura recebida usando timing-safe comparison

    Args:
        raw_body: Corpo bruto da requisição em bytes
        signature_from_header: Assinatura recebida no header X-Webhook-Signature (já em base64)

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
        # Calcula HMAC-SHA256 do raw_body usando a chave pública
        # Conforme documentação: createHmac("sha256", ABACATEPAY_PUBLIC_KEY).update(bodyBuffer).digest("base64")
        expected_sig = hmac.new(
            ABACATEPAY_PUBLIC_KEY.encode(),
            raw_body,
            hashlib.sha256,
        ).digest()

        # Converte para base64 (conforme documentação)
        expected_sig_b64 = base64.b64encode(expected_sig).decode()

        # Compara usando timing-safe comparison (conforme documentação)
        # A assinatura recebida já está em base64 como string
        if len(expected_sig_b64) != len(signature_from_header):
            return False

        # Converte ambas para bytes para comparação segura (timing-safe)
        expected_bytes = expected_sig_b64.encode("utf-8")
        received_bytes = signature_from_header.encode("utf-8")

        return hmac.compare_digest(expected_bytes, received_bytes)
    except Exception as e:
        logger.error(f"Erro ao verificar assinatura: {e}")
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

    Eventos suportados:
    - billing.paid: Cobrança foi paga
    - withdraw.done: Saque concluído
    - withdraw.failed: Saque falhou
    """
    try:
        raw_body = request.body
        signature = request.headers.get("X-Webhook-Signature", "")

        signature_valid = False
        if signature:
            signature_valid = verify_webhook_signature(raw_body, signature)
        else:
            signature_valid = verify_webhook_secret(request)

        if not signature_valid:
            logger.warning("Assinatura de webhook inválida")
            return JsonResponse({"error": "Invalid signature"}, status=401)

        data = json.loads(raw_body.decode("utf-8"))
        event_type = data.get("event")
        event_data = data.get("data", {})
        dev_mode = data.get("devMode", False)
        log_id = data.get("id", "")

        logger.info(
            f"Webhook recebido: event={event_type}, id={log_id}, devMode={dev_mode}"
        )

        if event_type == "billing.paid":
            pix_qrcode = event_data.get("pixQrCode", {})
            payment = event_data.get("payment", {})

            payment_amount_cents = payment.get("amount", 0) if payment else 0
            pix_id = pix_qrcode.get("id") if pix_qrcode else None

            logger.info(
                f"Processando billing.paid - PIX ID: {pix_id}, Amount: {payment_amount_cents}"
            )

            from decimal import Decimal

            billing_found = None

            if payment_amount_cents > 0:
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
            transaction = event_data.get("transaction", {})
            logger.info(f"Saque concluído: {transaction.get('id')}")

        elif event_type == "withdraw.failed":
            transaction = event_data.get("transaction", {})
            logger.info(f"Saque falhado: {transaction.get('id')}")

        else:
            logger.warning(f"Tipo de evento não reconhecido: {event_type}")

        return JsonResponse({"status": "ok", "received": True})

    except json.JSONDecodeError as e:
        logger.error(f"Erro ao fazer parse do JSON do webhook: {e}")
        return JsonResponse({"error": "Invalid JSON"}, status=400)

    except Exception as e:
        logger.error(f"Erro ao processar webhook: {e}", exc_info=True)
        return JsonResponse({"error": "Internal server error"}, status=500)
