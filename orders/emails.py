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
    print(f"[EMAIL] send_order_created_email chamado para pedido {order.order_id}")
    try:
        user = order.user
        if not user.email:
            print(f"[EMAIL] ⚠ Usuário {user.username} não tem email cadastrado")
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

        # Verifica qual backend está sendo usado
        email_backend = getattr(settings, "EMAIL_BACKEND", "")
        print(
            f"[EMAIL] Tentando enviar email de pedido criado. Backend: {email_backend}, "
            f"Para: {user.email}, Pedido: {order.order_id}"
        )
        logger.info(
            f"Tentando enviar email de pedido criado. Backend: {email_backend}, "
            f"Para: {user.email}, Pedido: {order.order_id}"
        )

        # Envia o email
        try:
            result = send_mail(
                subject=f"Pedido {order.order_id} criado com sucesso!",
                message=plain_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
                html_message=html_message,
                fail_silently=True,  # Não quebrar o fluxo se o email falhar
            )

            if result:
                print(
                    f"[EMAIL] ✓ Email de pedido criado enviado com sucesso para {user.email} - Pedido {order.order_id}"
                )
                logger.info(
                    f"Email de pedido criado enviado com sucesso para {user.email} - Pedido {order.order_id}"
                )
            else:
                print(
                    f"[EMAIL] ⚠ Falha ao enviar email de pedido criado para {user.email} - Pedido {order.order_id}. "
                    f"Retornou False. Verifique as configurações de email."
                )
                logger.warning(
                    f"Falha ao enviar email de pedido criado para {user.email} - Pedido {order.order_id}. "
                    f"Verifique as configurações de email."
                )
            return result
        except Exception as email_error:
            error_str = str(email_error)
            print(f"[EMAIL] ✗ Erro ao enviar email de pedido criado: {error_str}")

            # Mensagens de ajuda específicas para erros comuns
            if (
                "535" in error_str
                or "BadCredentials" in error_str
                or "Username and Password not accepted" in error_str
            ):
                print(
                    "[EMAIL] ⚠ ERRO DE AUTENTICAÇÃO GMAIL (535):\n"
                    "  - Verifique se EMAIL_HOST_USER é um email Gmail válido (ex: seu-email@gmail.com)\n"
                    "  - Verifique se EMAIL_HOST_PASSWORD é uma SENHA DE APP do Gmail (não a senha normal)\n"
                    "  - Para criar senha de app: https://myaccount.google.com/apppasswords\n"
                    "  - Certifique-se de que não há espaços extras no .env\n"
                    "  - A senha de app deve ter 16 caracteres (sem espaços ou hífens)"
                )
            elif "Connection" in error_str or "timeout" in error_str.lower():
                print(
                    "[EMAIL] ⚠ ERRO DE CONEXÃO:\n"
                    "  - Verifique se o container tem acesso à internet\n"
                    "  - Verifique se a porta 587 não está bloqueada\n"
                    "  - Tente aumentar EMAIL_TIMEOUT no .env"
                )

            logger.error(
                f"Erro ao enviar email de pedido criado: {email_error}", exc_info=True
            )
            return False

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

        # Verifica se as configurações de email estão disponíveis
        if not getattr(settings, "EMAIL_HOST_USER", None) or not getattr(
            settings, "EMAIL_HOST_PASSWORD", None
        ):
            logger.warning(
                "Configurações de email não encontradas. Email não será enviado."
            )
            return False

        # Envia o email
        send_mail(
            subject=f"Pagamento confirmado - Pedido {order.order_id}",
            message=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            html_message=html_message,
            fail_silently=True,  # Não quebrar o fluxo se o email falhar
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

        # Verifica se as configurações de email estão disponíveis
        if not getattr(settings, "EMAIL_HOST_USER", None) or not getattr(
            settings, "EMAIL_HOST_PASSWORD", None
        ):
            logger.warning(
                "Configurações de email não encontradas. Email não será enviado."
            )
            return False

        # Envia o email
        send_mail(
            subject=f"⚠️ Novo pagamento confirmado - Pedido {order.order_id}",
            message=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[admin_email],
            html_message=html_message,
            fail_silently=True,  # Não quebrar o fluxo se o email falhar
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

        # Verifica se as configurações de email estão disponíveis
        if not getattr(settings, "EMAIL_HOST_USER", None) or not getattr(
            settings, "EMAIL_HOST_PASSWORD", None
        ):
            logger.warning(
                "Configurações de email não encontradas. Email não será enviado."
            )
            return False

        # Envia o email
        send_mail(
            subject=f"Pedido {order.order_id} entregue!",
            message=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            html_message=html_message,
            fail_silently=True,  # Não quebrar o fluxo se o email falhar
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

        # Verifica se as configurações de email estão disponíveis
        if not getattr(settings, "EMAIL_HOST_USER", None) or not getattr(
            settings, "EMAIL_HOST_PASSWORD", None
        ):
            logger.warning(
                "Configurações de email não encontradas. Email não será enviado."
            )
            return False

        # Envia o email
        send_mail(
            subject=f"Pedido {order.order_id} cancelado",
            message=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            html_message=html_message,
            fail_silently=True,  # Não quebrar o fluxo se o email falhar
        )

        logger.info(
            f"Email de pedido cancelado enviado para {user.email} - Pedido {order.order_id}"
        )
        return True

    except Exception as e:
        logger.error(f"Erro ao enviar email de pedido cancelado: {e}", exc_info=True)
        return False
