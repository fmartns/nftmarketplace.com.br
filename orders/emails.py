"""
Módulo para envio de emails relacionados a pedidos
"""

import logging
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
from django.utils.html import strip_tags

logger = logging.getLogger(__name__)


def get_admin_email():
    """Retorna o email do administrador para notificações"""
    return getattr(settings, "ADMIN_EMAIL", settings.DEFAULT_FROM_EMAIL)


def send_order_created_email(order):
    """
    Envia email quando um pedido é criado

    Args:
        order: Instância do modelo Order
    """
    try:
        user = order.user
        if not user.email:
            logger.warning(f"Usuário {user.username} não tem email cadastrado")
            return False

        context = {
            "order": order,
            "user": user,
            "order_id": order.order_id,
            "total": order.total,
            "items": order.items.all(),
            "site_url": (
                getattr(settings, "FRONTEND_ORIGINS", ["http://localhost:3000"])[0]
                if getattr(settings, "FRONTEND_ORIGINS", [])
                else "http://localhost:3000"
            ),
        }

        # Renderiza o template HTML
        html_message = render_to_string("emails/order_created.html", context)
        plain_message = strip_tags(html_message)

        # Envia o email
        send_mail(
            subject=f"Pedido {order.order_id} criado com sucesso!",
            message=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            html_message=html_message,
            fail_silently=False,
        )

        logger.info(
            f"Email de pedido criado enviado para {user.email} - Pedido {order.order_id}"
        )
        return True

    except Exception as e:
        logger.error(f"Erro ao enviar email de pedido criado: {e}", exc_info=True)
        return False


def send_payment_confirmed_email(order):
    """
    Envia email quando o pagamento é confirmado (para o usuário)

    Args:
        order: Instância do modelo Order
    """
    try:
        user = order.user
        if not user.email:
            logger.warning(f"Usuário {user.username} não tem email cadastrado")
            return False

        context = {
            "order": order,
            "user": user,
            "order_id": order.order_id,
            "total": order.total,
            "paid_at": order.paid_at,
            "items": order.items.all(),
            "site_url": (
                getattr(settings, "FRONTEND_ORIGINS", ["http://localhost:3000"])[0]
                if getattr(settings, "FRONTEND_ORIGINS", [])
                else "http://localhost:3000"
            ),
        }

        # Renderiza o template HTML
        html_message = render_to_string("emails/payment_confirmed.html", context)
        plain_message = strip_tags(html_message)

        # Envia o email
        send_mail(
            subject=f"Pagamento confirmado - Pedido {order.order_id}",
            message=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            html_message=html_message,
            fail_silently=False,
        )

        logger.info(
            f"Email de pagamento confirmado enviado para {user.email} - Pedido {order.order_id}"
        )
        return True

    except Exception as e:
        logger.error(
            f"Erro ao enviar email de pagamento confirmado: {e}", exc_info=True
        )
        return False


def send_payment_confirmed_admin_email(order):
    """
    Envia email para o administrador quando o pagamento é confirmado

    Args:
        order: Instância do modelo Order
    """
    try:
        admin_email = get_admin_email()

        context = {
            "order": order,
            "user": order.user,
            "order_id": order.order_id,
            "total": order.total,
            "paid_at": order.paid_at,
            "items": order.items.all(),
        }

        # Renderiza o template HTML
        html_message = render_to_string("emails/payment_confirmed_admin.html", context)
        plain_message = strip_tags(html_message)

        # Envia o email
        send_mail(
            subject=f"⚠️ Novo pagamento confirmado - Pedido {order.order_id}",
            message=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[admin_email],
            html_message=html_message,
            fail_silently=False,
        )

        logger.info(
            f"Email de pagamento confirmado (admin) enviado para {admin_email} - Pedido {order.order_id}"
        )
        return True

    except Exception as e:
        logger.error(
            f"Erro ao enviar email de pagamento confirmado (admin): {e}", exc_info=True
        )
        return False


def send_order_delivered_email(order):
    """
    Envia email quando o pedido é entregue

    Args:
        order: Instância do modelo Order
    """
    try:
        user = order.user
        if not user.email:
            logger.warning(f"Usuário {user.username} não tem email cadastrado")
            return False

        context = {
            "order": order,
            "user": user,
            "order_id": order.order_id,
            "delivered_at": order.delivered_at,
            "items": order.items.all(),
            "site_url": (
                getattr(settings, "FRONTEND_ORIGINS", ["http://localhost:3000"])[0]
                if getattr(settings, "FRONTEND_ORIGINS", [])
                else "http://localhost:3000"
            ),
        }

        # Renderiza o template HTML
        html_message = render_to_string("emails/order_delivered.html", context)
        plain_message = strip_tags(html_message)

        # Envia o email
        send_mail(
            subject=f"Pedido {order.order_id} entregue!",
            message=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            html_message=html_message,
            fail_silently=False,
        )

        logger.info(
            f"Email de pedido entregue enviado para {user.email} - Pedido {order.order_id}"
        )
        return True

    except Exception as e:
        logger.error(f"Erro ao enviar email de pedido entregue: {e}", exc_info=True)
        return False


def send_order_cancelled_email(order, reason="Tempo esgotado para pagamento"):
    """
    Envia email quando o pedido é cancelado (tempo esgotado)

    Args:
        order: Instância do modelo Order
        reason: Motivo do cancelamento
    """
    try:
        user = order.user
        if not user.email:
            logger.warning(f"Usuário {user.username} não tem email cadastrado")
            return False

        context = {
            "order": order,
            "user": user,
            "order_id": order.order_id,
            "total": order.total,
            "reason": reason,
            "items": order.items.all(),
            "site_url": (
                getattr(settings, "FRONTEND_ORIGINS", ["http://localhost:3000"])[0]
                if getattr(settings, "FRONTEND_ORIGINS", [])
                else "http://localhost:3000"
            ),
        }

        # Renderiza o template HTML
        html_message = render_to_string("emails/order_cancelled.html", context)
        plain_message = strip_tags(html_message)

        # Envia o email
        send_mail(
            subject=f"Pedido {order.order_id} cancelado",
            message=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            html_message=html_message,
            fail_silently=False,
        )

        logger.info(
            f"Email de pedido cancelado enviado para {user.email} - Pedido {order.order_id}"
        )
        return True

    except Exception as e:
        logger.error(f"Erro ao enviar email de pedido cancelado: {e}", exc_info=True)
        return False
