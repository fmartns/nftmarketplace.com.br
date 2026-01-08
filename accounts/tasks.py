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
        # Busca a task de validação
        validation_task = HabboValidationTask.objects.get(id=validation_task_id)
        validation_task.status = "processing"
        validation_task.save()

        nick = validation_task.nick_habbo
        palavra_esperada = validation_task.palavra_validacao.upper()

        logger.info(
            f"Iniciando validação do nick {nick} com palavra {palavra_esperada}"
        )

        # Usa as funções utilitárias da API do Habbo
        try:
            logger.info(f"🚀 Buscando dados do usuário {nick} via API do Habbo")

            motto = get_habbo_user_motto(nick)

            if motto:
                logger.info(f"✅ Motto encontrado: '{motto}'")
            else:
                logger.info("ℹ️ Usuário não tem motto definido")

        except Exception as e:
            logger.error(f"❌ Erro ao acessar API do Habbo: {e}")
            raise Exception(f"Erro ao acessar perfil do Habbo: {e}")

        if motto:
            motto_upper = motto.upper()
            logger.info(f"Comparando: '{palavra_esperada}' in '{motto_upper}'")

            # Verifica se a palavra de validação está no motto
            if palavra_esperada in motto_upper:
                # Atualiza o usuário
                user = validation_task.user
                
                # Verifica se o nick já está associado a outro usuário
                existing_user = User.objects.filter(nick_habbo=nick).exclude(id=user.id).first()
                if existing_user:
                    validation_task.status = "failed"
                    validation_task.resultado = f"Nick '{nick}' já está associado a outro usuário."
                    validation_task.save()
                    logger.warning(
                        f"Validação falhou: nick '{nick}' já está associado ao usuário {existing_user.username} (ID: {existing_user.id})"
                    )
                    return {
                        "status": "failed",
                        "nick": nick,
                        "resultado": validation_task.resultado,
                    }
                
                # Validação bem-sucedida
                validation_task.status = "success"
                validation_task.resultado = f"Validação bem-sucedida! Palavra '{palavra_esperada}' encontrada no motto: '{motto}'"
                validation_task.save()

                user.nick_habbo = nick
                user.habbo_validado = True
                user.palavra_validacao_habbo = None  # Remove a palavra após validação
                user.save()

                logger.info(
                    f"Usuário {user.username} validado com sucesso para o nick {nick}"
                )

            else:
                # Palavra não encontrada
                validation_task.status = "failed"
                validation_task.resultado = f"Validação falhou! Palavra '{palavra_esperada}' não encontrada no motto: '{motto}'"
                logger.warning(
                    f"Validação falhou para {nick}. Palavra esperada: {palavra_esperada}, Motto: {motto}"
                )

        else:
            # Motto não encontrado
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

        # Tenta atualizar o status da task
        try:
            validation_task.status = "failed"
            validation_task.resultado = f"Erro: {str(e)}"
            validation_task.save()
        except Exception:
            pass

        # Retry da task se ainda tiver tentativas
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
        # Agenda nova validação
        validate_habbo_nick.apply_async(args=[task.id], countdown=300)  # 5 minutos
        count += 1

    logger.info(f"Reagendadas {count} validações que falharam")
    return f"Reagendadas {count} validações"
