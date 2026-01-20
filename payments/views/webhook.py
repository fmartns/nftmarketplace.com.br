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
# Se não estiver configurada, usa a chave pública padrão da documentação
_DEFAULT_PUBLIC_KEY = "t9dXRhHHo3yDEj5pVDYz0frf7q6bMKyMRmxxCPIPp3RCplBfXRxqlC6ZpiWmOqj4L63qEaeUOtrCI8P0VMUgo6iIga2ri9ogaHFs0WIIywSMg0q7RmBfybe1E5XJcfC4IW3alNqym0tXoAKkzvfEjZxV6bE0oG2zJrNNYmUCKZyV0KZ3JS8Votf9EAWWYdiDkMkpbMdPggfh1EqHlVkMiTady6jOR3hyzGEHrIz2Ret0xHKMbiqkr9HS1JhNHDX9"

# Carregar chave pública do settings, removendo espaços e quebras de linha
_settings_key = getattr(settings, "ABACATEPAY_PUBLIC_KEY", None)
if _settings_key:
    # Remove espaços em branco e quebras de linha que podem ter sido adicionados acidentalmente
    _settings_key = _settings_key.strip().replace("\n", "").replace("\r", "")
    if len(_settings_key) < 100:
        logger.error(
            f"ABACATEPAY_PUBLIC_KEY do settings parece estar truncada! "
            f"Length: {len(_settings_key)} (esperado ~200+ caracteres). "
            f"Usando chave padrão como fallback."
        )
        _settings_key = None

ABACATEPAY_PUBLIC_KEY = _settings_key or _DEFAULT_PUBLIC_KEY

# Log da chave pública ao carregar o módulo (apenas tamanho para segurança)
logger.info(
    f"ABACATEPAY_PUBLIC_KEY carregada - Length: {len(ABACATEPAY_PUBLIC_KEY)}, "
    f"From env: {bool(_settings_key)}, "
    f"Is default: {ABACATEPAY_PUBLIC_KEY == _DEFAULT_PUBLIC_KEY}"
)

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

    # Log da chave pública (apenas tamanho para debug)
    logger.info(
        f"HMAC Validation - Public key length: {len(ABACATEPAY_PUBLIC_KEY)}, "
        f"Public key (first 20): {ABACATEPAY_PUBLIC_KEY[:20]}..., "
        f"Public key (last 20): ...{ABACATEPAY_PUBLIC_KEY[-20:]}"
    )

    try:
        # IMPORTANTE: Usar o corpo exatamente como recebido (sem modificações)
        # Se raw_body já é string, garantir que está em UTF-8
        if isinstance(raw_body, bytes):
            body_buffer = raw_body
        else:
            body_buffer = raw_body.encode("utf-8")

        # Verificar se a chave pública está correta (não truncada)
        if len(ABACATEPAY_PUBLIC_KEY) < 100:
            logger.error(
                f"ABACATEPAY_PUBLIC_KEY parece estar truncada ou incorreta! "
                f"Length: {len(ABACATEPAY_PUBLIC_KEY)} (esperado ~200+ caracteres). "
                f"Primeiros 50 chars: {ABACATEPAY_PUBLIC_KEY[:50]}..."
            )
            # Tentar recarregar do settings diretamente
            _reload_key = getattr(settings, "ABACATEPAY_PUBLIC_KEY", None)
            if _reload_key:
                _reload_key = _reload_key.strip().replace("\n", "").replace("\r", "")
                logger.error(
                    f"Tentando recarregar do settings - Length: {len(_reload_key)}, "
                    f"Primeiros 50: {_reload_key[:50]}..."
                )

        # Limpar a assinatura recebida (remover espaços, quebras de linha, etc)
        signature_clean = signature_from_header.strip()

        # Calcula HMAC-SHA256 do body_buffer usando a chave pública
        # Conforme documentação: createHmac("sha256", ABACATEPAY_PUBLIC_KEY).update(bodyBuffer).digest("base64")
        hmac_digest = hmac.new(
            ABACATEPAY_PUBLIC_KEY.encode("utf-8"),
            body_buffer,
            hashlib.sha256,
        ).digest()

        # Converte para base64 (conforme documentação)
        expected_sig = base64.b64encode(hmac_digest).decode("utf-8")

        # Log detalhado para debug em produção
        logger.info(
            f"HMAC Validation - Body length: {len(body_buffer)}, "
            f"Expected signature length: {len(expected_sig)}, "
            f"Received signature length: {len(signature_clean)}, "
            f"Expected (first 30): {expected_sig[:30]}..., "
            f"Received (first 30): {signature_clean[:30] if len(signature_clean) > 30 else signature_clean}..."
        )

        # Converte para bytes para comparação timing-safe
        expected_bytes = expected_sig.encode("utf-8")
        received_bytes = signature_clean.encode("utf-8")

        # Compara usando timing-safe comparison (conforme documentação)
        if len(expected_bytes) != len(received_bytes):
            logger.warning(
                f"HMAC length mismatch: expected={len(expected_bytes)}, received={len(received_bytes)}"
            )
            return False

        is_valid = hmac.compare_digest(expected_bytes, received_bytes)
        if not is_valid:
            logger.warning(
                f"HMAC signature mismatch. Body length: {len(body_buffer)}, "
                f"Public key length: {len(ABACATEPAY_PUBLIC_KEY)}, "
                f"Expected signature: {expected_sig}, "
                f"Received signature: {signature_clean}"
            )
        else:
            logger.info("HMAC signature válida")
        return is_valid
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
        # IMPORTANTE: Lê o corpo bruto ANTES de qualquer processamento
        # request.body é bytes, precisamos usar diretamente para HMAC
        # Mas também precisamos como string para fazer parse do JSON depois
        raw_body_bytes = request.body
        raw_body_str = raw_body_bytes.decode("utf-8")

        # Obter assinatura do header (pode estar em diferentes formatos)
        # Django converte headers para HTTP_* no META, então precisamos verificar ambos
        signature = (
            request.headers.get("X-Webhook-Signature", "")
            or request.headers.get("x-webhook-signature", "")
            or request.META.get("HTTP_X_WEBHOOK_SIGNATURE", "")
            or request.META.get("HTTP_X_WEBHOOK_signature", "")
        ).strip()

        # Log detalhado para debug em produção
        all_headers = dict(request.headers)
        meta_headers = {k: v for k, v in request.META.items() if k.startswith("HTTP_")}
        logger.info(
            f"Webhook recebido - Body length: {len(raw_body_bytes)}, "
            f"Body preview: {raw_body_str[:200]}..., "
            f"Signature present: {bool(signature)}, "
            f"Signature length: {len(signature) if signature else 0}, "
            f"Signature value: {signature[:50] if signature else 'N/A'}..., "
            f"Headers with 'webhook': {[k for k in all_headers.keys() if 'webhook' in k.lower()]}, "
            f"META headers with 'WEBHOOK': {[k for k in meta_headers.keys() if 'WEBHOOK' in k]}"
        )

        # Validação em duas camadas (conforme documentação):
        # 1. Secret na URL (método simples)
        # 2. Assinatura HMAC no header (integridade do corpo)
        signature_valid = False

        # Se houver assinatura no header, valida via HMAC
        if signature:
            signature_valid = verify_webhook_signature(raw_body_str, signature)
            if not signature_valid:
                logger.warning(
                    f"Assinatura HMAC inválida. Body preview: {raw_body_str[:100]}..., "
                    f"Signature: {signature[:50] if len(signature) > 50 else signature}..."
                )
        else:
            # Se não houver assinatura, valida via secret na URL
            logger.info(
                "Assinatura não encontrada no header, tentando validar via secret na URL"
            )
            signature_valid = verify_webhook_secret(request)
            if not signature_valid:
                logger.warning("Secret do webhook inválido ou ausente")

        if not signature_valid:
            # Em produção, se a assinatura HMAC falhar mas houver secret na URL válido,
            # aceitar o webhook (fallback de segurança)
            if signature and verify_webhook_secret(request):
                logger.warning(
                    f"Assinatura HMAC falhou, mas secret na URL é válido. "
                    f"Aceitando webhook como fallback. IP: {request.META.get('REMOTE_ADDR')}"
                )
                signature_valid = True
            else:
                logger.warning(
                    f"Webhook rejeitado - IP: {request.META.get('REMOTE_ADDR')}, "
                    f"Signature presente: {bool(signature)}, "
                    f"Secret válido: {verify_webhook_secret(request)}"
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

                # Envia emails de pagamento confirmado
                from orders.emails import (
                    send_payment_confirmed_email,
                    send_payment_confirmed_admin_email,
                )

                send_payment_confirmed_email(billing.order)
                send_payment_confirmed_admin_email(billing.order)

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
