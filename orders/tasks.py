"""
Tasks Celery para o módulo de pedidos
"""

import logging
from datetime import timedelta
from celery import shared_task
from django.utils import timezone
from .models import Order

logger = logging.getLogger(__name__)


@shared_task
def send_order_created_email_task(order_id: int):
    """
    Task assíncrona para enviar email de pedido criado

    Args:
        order_id: ID do pedido
    """
    try:
        order = Order.objects.get(id=order_id)
        from .emails import send_order_created_email

        send_order_created_email(order)
    except Order.DoesNotExist:
        logger.error(f"Pedido com ID {order_id} não encontrado para envio de email")
    except Exception as e:
        logger.error(
            f"Erro ao enviar email de pedido criado para pedido {order_id}: {e}",
            exc_info=True,
        )


@shared_task
def check_and_cancel_order(order_id: int):
    """
    Verifica se um pedido específico foi pago e cancela se não foi.

    Esta task é lançada quando um pedido é criado, com countdown de 5 minutos.
    Após 5 minutos, verifica se o pedido foi pago e cancela se não foi.

    Args:
        order_id: ID do pedido a ser verificado
    """
    try:
        order = Order.objects.get(id=order_id)

        # Verifica se o pedido ainda está pendente e não foi pago
        if order.status == "pending" and order.paid_at is None:
            # Verifica se já passaram 5 minutos desde a criação
            time_since_creation = timezone.now() - order.created_at
            if time_since_creation >= timedelta(minutes=5):
                if order.cancel(reason="Pagamento não realizado em 5 minutos"):
                    logger.info(
                        f"Pedido {order.order_id} cancelado automaticamente "
                        f"(criado em {order.created_at}, não pago em 5 minutos)"
                    )
                    # Envia email de pedido cancelado
                    from .emails import send_order_cancelled_email

                    send_order_cancelled_email(
                        order, reason="Tempo esgotado para pagamento (5 minutos)"
                    )
                    return {
                        "status": "cancelled",
                        "order_id": order.order_id,
                        "message": "Pedido cancelado por falta de pagamento",
                    }
                else:
                    logger.warning(
                        f"Pedido {order.order_id} não pode ser cancelado "
                        f"(status atual: {order.status})"
                    )
                    return {
                        "status": "skipped",
                        "order_id": order.order_id,
                        "message": "Pedido não pode ser cancelado",
                    }
            else:
                # Ainda não passaram 5 minutos, não cancela
                logger.debug(
                    f"Pedido {order.order_id} ainda dentro do prazo de 5 minutos "
                    f"(tempo restante: {timedelta(minutes=5) - time_since_creation})"
                )
                return {
                    "status": "pending",
                    "order_id": order.order_id,
                    "message": "Pedido ainda dentro do prazo",
                }
        else:
            # Pedido já foi pago ou cancelado
            logger.debug(
                f"Pedido {order.order_id} já foi processado "
                f"(status: {order.status}, paid_at: {order.paid_at})"
            )
            return {
                "status": "already_processed",
                "order_id": order.order_id,
                "message": f"Pedido já foi processado (status: {order.status})",
            }

    except Order.DoesNotExist:
        logger.error(f"Pedido com ID {order_id} não encontrado")
        return {"status": "error", "error": "Pedido não encontrado"}
    except Exception as e:
        logger.error(
            f"Erro ao verificar pedido {order_id}: {e}",
            exc_info=True,
        )
        return {"status": "error", "error": str(e)}


@shared_task
def cancel_unpaid_orders_security_check():
    """
    Rotina de segurança que verifica e cancela pedidos não pagos.

    Esta task é executada a cada 30 minutos como uma segunda camada de segurança,
    verificando todos os pedidos pendentes criados há mais de 5 minutos.

    Esta é uma rotina de backup caso alguma task individual não tenha sido executada.
    """
    try:
        # Calcula o tempo limite (5 minutos atrás)
        time_limit = timezone.now() - timedelta(minutes=5)

        # Busca pedidos pendentes criados há mais de 5 minutos e não pagos
        unpaid_orders = Order.objects.filter(
            status="pending",
            created_at__lt=time_limit,
            paid_at__isnull=True,
        )

        count = unpaid_orders.count()

        if count == 0:
            logger.debug("Rotina de segurança: nenhum pedido pendente para cancelar")
            return {
                "status": "success",
                "cancelled": 0,
                "message": "Nenhum pedido para cancelar",
            }

        # Cancela os pedidos
        cancelled_count = 0
        for order in unpaid_orders:
            try:
                if order.cancel(
                    reason="Pagamento não realizado (verificação de segurança)"
                ):
                    cancelled_count += 1
                    logger.info(
                        f"Pedido {order.order_id} cancelado pela rotina de segurança "
                        f"(criado em {order.created_at}, não pago em 5 minutos)"
                    )
                    # Envia email de pedido cancelado
                    from .emails import send_order_cancelled_email

                    send_order_cancelled_email(
                        order,
                        reason="Tempo esgotado para pagamento (verificação de segurança)",
                    )
                else:
                    logger.warning(
                        f"Pedido {order.order_id} não pode ser cancelado "
                        f"(status atual: {order.status})"
                    )
            except Exception as e:
                logger.error(
                    f"Erro ao cancelar pedido {order.order_id}: {e}",
                    exc_info=True,
                )

        logger.info(
            f"Rotina de segurança concluída: {cancelled_count} pedido(s) cancelado(s) "
            f"(de {count} encontrados)"
        )

        return {
            "status": "success",
            "cancelled": cancelled_count,
            "total_found": count,
            "message": f"{cancelled_count} pedido(s) cancelado(s) pela rotina de segurança",
        }

    except Exception as e:
        logger.error(
            f"Erro na rotina de segurança cancel_unpaid_orders_security_check: {e}",
            exc_info=True,
        )
        return {"status": "error", "error": str(e)}
