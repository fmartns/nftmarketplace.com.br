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
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiResponse, OpenApiExample
from drf_spectacular.types import OpenApiTypes

from ..serializers import HabboValidationSerializer, HabboValidationStatusSerializer
from ..models import HabboValidationTask
from ..utils import generate_validation_word

User = get_user_model()


class HabboValidationView(APIView):
    """
    View para iniciar processo de validação do nick do Habbo.
    Gera uma palavra aleatória que deve ser colocada no motto do Habbo.
    """
    permission_classes = [IsAuthenticated]

    @extend_schema(
        operation_id="habbo_verify",
        tags=["accounts"],
        summary="Iniciar validação do nick do Habbo",
        description="""
        Inicia o processo de validação do nick do Habbo usando o método de verificação por motto.
        
        **Como funciona:**
        1. Envie seu nick do Habbo
        2. Uma palavra aleatória será gerada (ex: "BANANA")
        3. Coloque esta palavra no seu motto do Habbo
        4. A validação será verificada automaticamente em 5 minutos
        5. Ou confirme manualmente via POST /habbo/confirm/ após colocar a palavra
        
        **Nota:** O nick só pode estar associado a um usuário por vez. Se já estiver em uso, a validação será rejeitada.
        """,
        request=HabboValidationSerializer,
        responses={
            200: OpenApiResponse(
                description="Validação iniciada com sucesso",
                examples=[
                    OpenApiExample(
                        name="Validação iniciada",
                        value={
                            "message": 'Validação iniciada! Coloque a palavra "BANANA" no seu motto do Habbo e aguarde 5 minutos.',
                            "palavra_validacao": "BANANA",
                            "nick_habbo": "Maikkk.",
                            "validation_id": 1,
                            "eta_time": "14:35:00",
                            "current_time": "14:30:00",
                        },
                    ),
                ],
            ),
            400: OpenApiResponse(
                description="Erro na validação",
                examples=[
                    OpenApiExample(
                        name="Nick já validado",
                        value={
                            "error": "Este nick do Habbo já está validado por outro usuário",
                        },
                    ),
                ],
            ),
        },
    )
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

        # A validação do serializer já verifica se o nick está associado a outro usuário
        # Não precisamos verificar novamente aqui

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

        return Response(
            {
                "message": f'Validação iniciada! Coloque a palavra "{palavra_validacao}" no seu motto do Habbo e aguarde 5 minutos.',
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

    @extend_schema(
        operation_id="habbo_unlink",
        tags=["accounts"],
        summary="Desvincular nick do Habbo",
        description="Remove a associação do nick do Habbo do perfil do usuário autenticado.",
        responses={
            200: OpenApiResponse(
                description="Nick desvinculado com sucesso",
                examples=[
                    OpenApiExample(
                        name="Desvinculação bem-sucedida",
                        value={
                            "message": 'Nick "Maikkk." desvinculado com sucesso',
                            "nick_anterior": "Maikkk.",
                        },
                    ),
                ],
            ),
            400: OpenApiResponse(
                description="Erro na desvinculação",
                examples=[
                    OpenApiExample(
                        name="Nick não configurado",
                        value={
                            "error": "Usuário não possui nick do Habbo configurado",
                        },
                    ),
                ],
            ),
        },
    )
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

    @extend_schema(
        operation_id="habbo_validation_status",
        tags=["accounts"],
        summary="Verificar status da validação do Habbo",
        description="""
        Verifica o status de uma validação do Habbo.
        Se o parâmetro validation_id não for fornecido, retorna o status da validação mais recente do usuário.
        """,
        parameters=[
            OpenApiParameter(
                name="validation_id",
                type=OpenApiTypes.INT,
                location=OpenApiParameter.QUERY,
                description="ID da validação para verificar status (opcional, se não fornecido retorna a mais recente)",
                required=False,
            )
        ],
        responses={
            200: OpenApiResponse(
                response=HabboValidationStatusSerializer,
                description="Status da validação retornado com sucesso",
            ),
            404: OpenApiResponse(
                description="Validação não encontrada",
                examples=[
                    OpenApiExample(
                        name="Não encontrada",
                        value={
                            "error": "Validação não encontrada",
                        },
                    ),
                ],
            ),
        },
    )
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

    @extend_schema(
        operation_id="habbo_validation_history",
        tags=["accounts"],
        summary="Histórico de validações do Habbo",
        description="Retorna o histórico completo de todas as validações do Habbo do usuário autenticado, ordenado pela mais recente primeiro.",
        responses={
            200: OpenApiResponse(
                response=HabboValidationStatusSerializer(many=True),
                description="Histórico de validações retornado com sucesso",
            ),
        },
    )
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

    @extend_schema(
        operation_id="habbo_confirm",
        tags=["accounts"],
        summary="Confirmar validação do Habbo manualmente",
        description="""
        Verifica imediatamente se a palavra de validação está presente no motto do Habbo.
        Útil quando o usuário já colocou a palavra no motto e não quer esperar 5 minutos.
        
        Requer que uma validação tenha sido iniciada anteriormente via POST /habbo/verify/.
        """,
        responses={
            200: OpenApiResponse(
                description="Validação confirmada com sucesso",
                examples=[
                    OpenApiExample(
                        name="Validação bem-sucedida",
                        value={
                            "message": "Nick validado com sucesso!",
                            "nick_habbo": "Maikkk.",
                            "habbo_validado": True,
                        },
                    ),
                ],
            ),
            400: OpenApiResponse(
                description="Erro na validação",
                examples=[
                    OpenApiExample(
                        name="Palavra não encontrada",
                        value={
                            "error": "Palavra de validação não encontrada no motto do Habbo.",
                            "palavra_esperada": "BANANA",
                            "motto_atual": "sou quem sou independente de quem gost",
                        },
                    ),
                    OpenApiExample(
                        name="Nenhuma validação pendente",
                        value={
                            "error": "Nenhuma validação pendente encontrada. Inicie uma validação primeiro.",
                        },
                    ),
                ],
            ),
            404: OpenApiResponse(
                description="Nick não encontrado",
                examples=[
                    OpenApiExample(
                        name="Usuário não existe",
                        value={
                            "error": "Usuário do Habbo não encontrado. Verifique se o nick está correto.",
                        },
                    ),
                ],
            ),
        },
    )
    def post(self, request):
        """
        Confirma manualmente a validação do Habbo.
        Verifica se a palavra de validação está presente no motto.
        """
        user = request.user
        
        # Busca a validação pendente mais recente
        validation_task = (
            HabboValidationTask.objects.filter(
                user=user,
                status="pending"
            )
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
                # Verifica se o nick já está associado a outro usuário
                existing_user = User.objects.filter(nick_habbo=nick_habbo).exclude(id=user.id).first()
                if existing_user:
                    validation_task.status = "failed"
                    validation_task.resultado = f"Nick '{nick_habbo}' já está associado a outro usuário."
                    validation_task.save()
                    return Response(
                        {
                            "error": "Este nick do Habbo já está associado a outro usuário.",
                            "nick_habbo": nick_habbo,
                        },
                        status=status.HTTP_400_BAD_REQUEST,
                    )
                
                # Validação bem-sucedida
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
