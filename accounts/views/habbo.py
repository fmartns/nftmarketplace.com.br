"""
Views para validação do Habbo
"""

from datetime import datetime, timedelta
import pytz
from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated

from ..serializers import HabboValidationSerializer, HabboValidationStatusSerializer
from ..models import HabboValidationTask
from ..utils import generate_validation_word
from ..docs.habbo import (
    habbo_verify_schema,
    habbo_confirm_schema,
    habbo_unlink_schema,
    habbo_validation_status_schema,
    habbo_validation_history_schema,
)

User = get_user_model()


class HabboValidationView(APIView):
    """
    View para iniciar processo de validação do nick do Habbo.
    Gera uma palavra aleatória que deve ser colocada no motto do Habbo.
    """

    permission_classes = [IsAuthenticated]

    @habbo_verify_schema
    def post(self, request):
        serializer = HabboValidationSerializer(
            data=request.data, context={"request": request}
        )
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        validated_data = serializer.validated_data
        assert validated_data is not None
        nick_habbo = validated_data["nick_habbo"]
        user = request.user

        # Se o usuário atual já tinha um nick diferente, limpar primeiro
        if user.nick_habbo and user.nick_habbo != nick_habbo:
            user.nick_habbo = None
            user.habbo_validado = False

        palavra_validacao = generate_validation_word()
        user.palavra_validacao_habbo = palavra_validacao
        user.save()

        validation_task = HabboValidationTask.objects.create(
            user=user,
            nick_habbo=nick_habbo,
            palavra_validacao=palavra_validacao,
            task_id=f"habbo_validation_{user.id}_{timezone.now().timestamp()}",
        )

        from ..tasks import validate_habbo_nick

        task_result = validate_habbo_nick.apply_async(
            args=[validation_task.id], countdown=300
        )

        validation_task.task_id = task_result.id
        validation_task.save()

        br_tz = pytz.timezone("America/Sao_Paulo")
        current_time = datetime.now(br_tz)
        eta_time = current_time + timedelta(minutes=5)

        message = f'Validação iniciada! Coloque a palavra "{palavra_validacao}" no seu motto do Habbo e aguarde 5 minutos.'

        return Response(
            {
                "message": message,
                "palavra_validacao": palavra_validacao,
                "nick_habbo": nick_habbo,
                "validation_id": validation_task.id,
                "eta_time": eta_time.strftime("%H:%M:%S"),
                "current_time": current_time.strftime("%H:%M:%S"),
            }
        )


class HabboUnlinkView(APIView):
    """
    View para desvincular o nick do Habbo do usuário.
    Remove a associação do nick validado do perfil do usuário.
    """

    permission_classes = [IsAuthenticated]
    serializer_class = None

    @habbo_unlink_schema
    def post(self, request):
        """Desvincula o nick do Habbo do usuário autenticado"""
        user = request.user

        if not user.nick_habbo:
            return Response(
                {
                    "error": "Usuário não possui nick do Habbo configurado",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        nick_anterior = user.nick_habbo
        user.nick_habbo = None
        user.habbo_validado = False
        user.palavra_validacao_habbo = None
        user.save()

        return Response(
            {
                "message": f'Nick "{nick_anterior}" desvinculado com sucesso',
                "nick_anterior": nick_anterior,
            }
        )


class HabboValidationStatusView(APIView):
    """
    View para verificar o status de uma validação do Habbo.
    Se não for fornecido validation_id, retorna o status da validação mais recente.
    """

    permission_classes = [IsAuthenticated]

    @habbo_validation_status_schema
    def get(self, request):
        validation_id = request.query_params.get("validation_id")

        if validation_id:
            validation_task = HabboValidationTask.objects.filter(
                id=validation_id, user=request.user
            ).first()
        else:
            validation_task = (
                HabboValidationTask.objects.filter(user=request.user)
                .order_by("-created_at")
                .first()
            )

        if not validation_task:
            return Response(
                {"error": "Validação não encontrada"}, status=status.HTTP_404_NOT_FOUND
            )

        return Response(HabboValidationStatusSerializer(validation_task).data)


class HabboValidationHistoryView(APIView):
    """
    View para obter o histórico de validações do Habbo do usuário.
    Retorna todas as validações ordenadas pela mais recente primeiro.
    """

    permission_classes = [IsAuthenticated]

    @habbo_validation_history_schema
    def get(self, request):
        validations = HabboValidationTask.objects.filter(user=request.user).order_by(
            "-created_at"
        )

        return Response(HabboValidationStatusSerializer(validations, many=True).data)


class HabboConfirmView(APIView):
    """
    View para confirmação manual da validação do Habbo.
    Verifica imediatamente se a palavra de validação está no motto.
    """

    permission_classes = [IsAuthenticated]

    @habbo_confirm_schema
    def post(self, request):
        """
        Confirma manualmente a validação do Habbo.
        Verifica se a palavra de validação está presente no motto.
        """
        user = request.user

        # Busca a validação pendente mais recente
        validation_task = (
            HabboValidationTask.objects.filter(user=user, status="pending")
            .order_by("-created_at")
            .first()
        )

        if not validation_task:
            return Response(
                {
                    "error": "Nenhuma validação pendente encontrada. Inicie uma validação primeiro."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        nick_habbo = validation_task.nick_habbo
        palavra_esperada = validation_task.palavra_validacao.upper()

        try:
            # Busca o motto do usuário via API do Habbo
            from ..utils import get_habbo_user_motto

            motto = get_habbo_user_motto(nick_habbo)

            if not motto:
                return Response(
                    {
                        "error": "Motto não encontrado no perfil do Habbo. Verifique se o nick está correto e se você tem um motto definido.",
                        "nick_habbo": nick_habbo,
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            motto_upper = motto.upper()

            # Verifica se a palavra de validação está no motto
            if palavra_esperada in motto_upper:
                # Se o nick já está associado a outro usuário, desvincular da conta antiga
                existing_user = (
                    User.objects.filter(nick_habbo=nick_habbo)
                    .exclude(id=user.id)
                    .first()
                )
                if existing_user:
                    existing_user.nick_habbo = None
                    existing_user.habbo_validado = False
                    existing_user.palavra_validacao_habbo = None
                    existing_user.save()

                # Validação bem-sucedida - vincular à nova conta
                validation_task.status = "success"
                validation_task.resultado = f"Validação confirmada manualmente! Palavra '{palavra_esperada}' encontrada no motto: '{motto}'"
                validation_task.save()

                # Atualiza o usuário
                user.nick_habbo = nick_habbo
                user.habbo_validado = True
                user.palavra_validacao_habbo = None  # Remove a palavra após validação
                user.save()

                return Response(
                    {
                        "message": "Nick validado com sucesso!",
                        "nick_habbo": nick_habbo,
                        "habbo_validado": True,
                    },
                    status=status.HTTP_200_OK,
                )
            else:
                # Palavra não encontrada
                validation_task.status = "failed"
                validation_task.resultado = f"Validação falhou! Palavra '{palavra_esperada}' não encontrada no motto: '{motto}'"
                validation_task.save()

                return Response(
                    {
                        "error": "Palavra de validação não encontrada no motto do Habbo.",
                        "palavra_esperada": palavra_esperada,
                        "motto_atual": motto,
                        "instrucoes": f"Coloque a palavra '{palavra_esperada}' no seu motto do Habbo e tente novamente.",
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

        except Exception as e:
            # Erro ao acessar API do Habbo
            validation_task.status = "failed"
            validation_task.resultado = f"Erro ao acessar API do Habbo: {str(e)}"
            validation_task.save()

            return Response(
                {
                    "error": "Erro ao verificar perfil do Habbo. Verifique se o nick está correto e tente novamente.",
                    "detalhes": str(e),
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
