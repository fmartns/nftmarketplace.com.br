"""
Documentação das rotas de validação do Habbo.
"""

from drf_spectacular.utils import (
    extend_schema,
    OpenApiParameter,
    OpenApiResponse,
    OpenApiExample,
)
from drf_spectacular.types import OpenApiTypes
from ..serializers.habbo import (
    HabboValidationSerializer,
    HabboValidationStatusSerializer,
)


habbo_verify_schema = extend_schema(
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
    5. Ou confirme manualmente via POST /accounts/habbo/confirm/ após colocar a palavra

    **Importante:**
    - Se o nick já estiver vinculado a outra conta, ele será desvinculado da conta antiga apenas após a validação ser bem-sucedida
    - A palavra de validação deve ser colocada exatamente como fornecida (case-insensitive)
    - O processo de validação automática leva 5 minutos

    **Requer autenticação:** Sim (JWT Token)
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
            description="Dados inválidos",
            examples=[
                OpenApiExample(
                    name="Nick ausente",
                    value={
                        "nick_habbo": ["Este campo é obrigatório."],
                    },
                ),
                OpenApiExample(
                    name="Nick muito longo",
                    value={
                        "nick_habbo": [
                            "Certifique-se de que este campo não tenha mais de 50 caracteres."
                        ],
                    },
                ),
            ],
        ),
        401: OpenApiResponse(
            description="Não autenticado",
            examples=[
                OpenApiExample(
                    name="Token ausente",
                    value={
                        "detail": "As credenciais de autenticação não foram fornecidas."
                    },
                ),
            ],
        ),
    },
)


habbo_confirm_schema = extend_schema(
    operation_id="habbo_confirm",
    tags=["accounts"],
    summary="Confirmar validação do Habbo manualmente",
    description="""
    Verifica imediatamente se a palavra de validação está presente no motto do Habbo.

    **Quando usar:**
    - Quando você já colocou a palavra no motto e não quer esperar 5 minutos
    - Para verificar imediatamente se a validação foi bem-sucedida

    **Requisitos:**
    - Uma validação deve ter sido iniciada anteriormente via POST /accounts/habbo/verify/
    - A palavra de validação deve estar presente no motto do Habbo

    **Requer autenticação:** Sim (JWT Token)
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
                        "instrucoes": "Coloque a palavra 'BANANA' no seu motto do Habbo e tente novamente.",
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
        401: OpenApiResponse(
            description="Não autenticado",
            examples=[
                OpenApiExample(
                    name="Token ausente",
                    value={
                        "detail": "As credenciais de autenticação não foram fornecidas."
                    },
                ),
            ],
        ),
        500: OpenApiResponse(
            description="Erro ao acessar API do Habbo",
            examples=[
                OpenApiExample(
                    name="Erro na API",
                    value={
                        "error": "Erro ao verificar perfil do Habbo. Verifique se o nick está correto e tente novamente.",
                        "detalhes": "Connection timeout",
                    },
                ),
            ],
        ),
    },
)


habbo_unlink_schema = extend_schema(
    operation_id="habbo_unlink",
    tags=["accounts"],
    summary="Desvincular nick do Habbo",
    description="""
    Remove a associação do nick do Habbo do perfil do usuário autenticado.

    **O que acontece:**
    - O nick do Habbo é removido do perfil
    - O status de validação é resetado (habbo_validado = False)
    - A palavra de validação é removida

    **Importante:**
    - Esta ação não pode ser desfeita
    - Você precisará validar novamente se quiser vincular o mesmo ou outro nick

    **Requer autenticação:** Sim (JWT Token)
    """,
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
        401: OpenApiResponse(
            description="Não autenticado",
            examples=[
                OpenApiExample(
                    name="Token ausente",
                    value={
                        "detail": "As credenciais de autenticação não foram fornecidas."
                    },
                ),
            ],
        ),
    },
)


habbo_validation_status_schema = extend_schema(
    operation_id="habbo_validation_status",
    tags=["accounts"],
    summary="Verificar status da validação do Habbo",
    description="""
    Verifica o status de uma validação do Habbo.

    **Comportamento:**
    - Se o parâmetro `validation_id` for fornecido, retorna o status dessa validação específica
    - Se o parâmetro não for fornecido, retorna o status da validação mais recente do usuário

    **Status possíveis:**
    - `pending`: Validação em andamento, aguardando verificação
    - `success`: Validação bem-sucedida, nick vinculado
    - `failed`: Validação falhou (palavra não encontrada ou erro na API)

    **Requer autenticação:** Sim (JWT Token)
    """,
    parameters=[
        OpenApiParameter(
            name="validation_id",
            type=OpenApiTypes.INT,
            location=OpenApiParameter.QUERY,
            description="ID da validação para verificar status (opcional, se não fornecido retorna a mais recente)",
            required=False,
            examples=[
                OpenApiExample(
                    name="Com ID",
                    value=1,
                    description="Retorna status da validação com ID 1",
                ),
            ],
        )
    ],
    responses={
        200: OpenApiResponse(
            response=HabboValidationStatusSerializer,
            description="Status da validação retornado com sucesso",
            examples=[
                OpenApiExample(
                    name="Validação pendente",
                    value={
                        "id": 1,
                        "nick_habbo": "Maikkk.",
                        "palavra_validacao": "BANANA",
                        "status": "pending",
                        "resultado": None,
                        "created_at": "2024-01-20T14:30:00Z",
                        "updated_at": "2024-01-20T14:30:00Z",
                    },
                    response_only=True,
                ),
                OpenApiExample(
                    name="Validação bem-sucedida",
                    value={
                        "id": 1,
                        "nick_habbo": "Maikkk.",
                        "palavra_validacao": "BANANA",
                        "status": "success",
                        "resultado": "Validação confirmada manualmente! Palavra 'BANANA' encontrada no motto: 'Eu sou BANANA'",
                        "created_at": "2024-01-20T14:30:00Z",
                        "updated_at": "2024-01-20T14:35:00Z",
                    },
                    response_only=True,
                ),
                OpenApiExample(
                    name="Validação falhou",
                    value={
                        "id": 1,
                        "nick_habbo": "Maikkk.",
                        "palavra_validacao": "BANANA",
                        "status": "failed",
                        "resultado": "Validação falhou! Palavra 'BANANA' não encontrada no motto: 'sou quem sou'",
                        "created_at": "2024-01-20T14:30:00Z",
                        "updated_at": "2024-01-20T14:35:00Z",
                    },
                    response_only=True,
                ),
            ],
        ),
        401: OpenApiResponse(
            description="Não autenticado",
            examples=[
                OpenApiExample(
                    name="Token ausente",
                    value={
                        "detail": "As credenciais de autenticação não foram fornecidas."
                    },
                ),
            ],
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


habbo_validation_history_schema = extend_schema(
    operation_id="habbo_validation_history",
    tags=["accounts"],
    summary="Histórico de validações do Habbo",
    description="""
    Retorna o histórico completo de todas as validações do Habbo do usuário autenticado.

    **Ordenação:**
    - As validações são retornadas ordenadas pela mais recente primeiro (created_at DESC)

    **Informações retornadas:**
    - ID da validação
    - Nick do Habbo usado
    - Palavra de validação gerada
    - Status da validação (pending, success, failed)
    - Resultado/mensagem da validação
    - Timestamps (created_at, updated_at)

    **Requer autenticação:** Sim (JWT Token)
    """,
    responses={
        200: OpenApiResponse(
            response=HabboValidationStatusSerializer(many=True),
            description="Histórico de validações retornado com sucesso",
            examples=[
                OpenApiExample(
                    name="Histórico completo",
                    value=[
                        {
                            "id": 3,
                            "nick_habbo": "Maikkk.",
                            "palavra_validacao": "ORANGE",
                            "status": "success",
                            "resultado": "Validação confirmada manualmente! Palavra 'ORANGE' encontrada no motto: 'Eu sou ORANGE'",
                            "created_at": "2024-01-20T15:00:00Z",
                            "updated_at": "2024-01-20T15:05:00Z",
                        },
                        {
                            "id": 2,
                            "nick_habbo": "Maikkk.",
                            "palavra_validacao": "BANANA",
                            "status": "failed",
                            "resultado": "Validação falhou! Palavra 'BANANA' não encontrada no motto: 'sou quem sou'",
                            "created_at": "2024-01-20T14:30:00Z",
                            "updated_at": "2024-01-20T14:35:00Z",
                        },
                        {
                            "id": 1,
                            "nick_habbo": "Maikkk.",
                            "palavra_validacao": "APPLE",
                            "status": "success",
                            "resultado": "Validação confirmada manualmente! Palavra 'APPLE' encontrada no motto: 'Eu sou APPLE'",
                            "created_at": "2024-01-20T10:00:00Z",
                            "updated_at": "2024-01-20T10:05:00Z",
                        },
                    ],
                    response_only=True,
                ),
                OpenApiExample(
                    name="Histórico vazio",
                    value=[],
                    response_only=True,
                ),
            ],
        ),
        401: OpenApiResponse(
            description="Não autenticado",
            examples=[
                OpenApiExample(
                    name="Token ausente",
                    value={
                        "detail": "As credenciais de autenticação não foram fornecidas."
                    },
                ),
            ],
        ),
    },
)
