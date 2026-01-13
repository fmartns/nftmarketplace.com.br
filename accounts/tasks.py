import logging
from celery import shared_task
from django.contrib.auth import get_user_model
from django.utils import timezone
from .models import HabboValidationTask
from .utils import get_habbo_user_motto

User = get_user_model()
logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def validate_habbo_nick(self, validation_task_id):
    """
    Task para validar o nick do Habbo verificando se a palavra de validação
    está presente no motto do usuário
    """
    try:
        validation_task = HabboValidationTask.objects.get(id=validation_task_id)
        validation_task.status = "processing"
        validation_task.save()

        nick = validation_task.nick_habbo
        palavra_esperada = validation_task.palavra_validacao.upper()

        logger.info(
            f"Iniciando validação do nick {nick} com palavra {palavra_esperada}"
        )

        try:
            logger.info(f"🚀 Buscando dados do usuário {nick} via API do Habbo")

            motto = get_habbo_user_motto(nick)

        if motto:
            motto_upper = motto.upper()
            logger.info(f"Comparando: '{palavra_esperada}' in '{motto_upper}'")

            if palavra_esperada in motto_upper:
                user = validation_task.user
                
                existing_user = User.objects.filter(nick_habbo=nick).exclude(id=user.id).first()
                if existing_user:
                    logger.info(
                        f"Desvinculando nick '{nick}' do usuário {existing_user.username} (ID: {existing_user.id}) para vincular ao usuário {user.username} (ID: {user.id})"
                    )
                    existing_user.nick_habbo = None
                    existing_user.habbo_validado = False
                    existing_user.palavra_validacao_habbo = None
                    existing_user.save()
                
                validation_task.status = "success"
                validation_task.resultado = f"Validação bem-sucedida! Palavra '{palavra_esperada}' encontrada no motto: '{motto}'"
                validation_task.save()

                user.nick_habbo = nick
                user.habbo_validado = True
                user.palavra_validacao_habbo = None
                user.save()

                logger.info(
                    f"Usuário {user.username} validado com sucesso para o nick {nick}"
                )

            else:
                validation_task.status = "failed"
                validation_task.resultado = f"Validação falhou! Palavra '{palavra_esperada}' não encontrada no motto: '{motto}'"
                logger.warning(
                    f"Validação falhou para {nick}. Palavra esperada: {palavra_esperada}, Motto: {motto}"
                )

        else:
            validation_task.status = "failed"
            validation_task.resultado = f"Motto não localizado para o nick {nick}. Verifique se o nick existe e tem um motto definido."
            logger.warning(f"Motto não encontrado para o nick {nick}")

        validation_task.save()

        return {
            "status": validation_task.status,
            "nick": nick,
            "resultado": validation_task.resultado,
        }

    except HabboValidationTask.DoesNotExist:
        logger.error(f"Task de validação {validation_task_id} não encontrada")
        return {"status": "failed", "error": "Task de validação não encontrada"}

    except Exception as e:
        logger.error(f"Erro na validação do nick: {str(e)}")

        try:
            validation_task.status = "failed"
            validation_task.resultado = f"Erro: {str(e)}"
            validation_task.save()
        except Exception:
            pass

        if self.request.retries < self.max_retries:
            logger.info(
                f"Tentando novamente validação (tentativa {self.request.retries + 1})"
            )
            raise self.retry(countdown=60 * (self.request.retries + 1))

        return {"status": "failed", "error": f"Erro: {str(e)}"}


@shared_task
def cleanup_old_validation_tasks():
    """
    Task para limpar tasks de validação antigas (mais de 7 dias)
    """
    from datetime import timedelta

    cutoff_date = timezone.now() - timedelta(days=7)
    old_tasks = HabboValidationTask.objects.filter(created_at__lt=cutoff_date)

    count = old_tasks.count()
    old_tasks.delete()

    logger.info(f"Removidas {count} tasks de validação antigas")
    return f"Removidas {count} tasks antigas"


@shared_task
def retry_failed_validations():
    """
    Task para tentar novamente validações que falharam
    """
    failed_tasks = HabboValidationTask.objects.filter(
        status="failed", created_at__gte=timezone.now() - timezone.timedelta(hours=24)
    )

    count = 0
    for task in failed_tasks:
        validate_habbo_nick.apply_async(args=[task.id], countdown=300)
        count += 1

    logger.info(f"Reagendadas {count} validações que falharam")
    return f"Reagendadas {count} validações"
