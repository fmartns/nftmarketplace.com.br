"""
Documentação das rotas de perfil do usuário.
"""

from drf_spectacular.utils import (
    extend_schema,
    OpenApiResponse,
    OpenApiExample,
)
from drf_spectacular.types import OpenApiTypes
from ..serializers.user import UserSerializer


user_profile_get_schema = extend_schema(
    operation_id="user_profile_get",
    tags=["accounts"],
    summary="Obter dados do perfil do usuário",
    description="""
    Retorna os dados completos do perfil do usuário autenticado.
    
    **Campos retornados:**
    - Informações básicas: id, username, email, first_name, last_name
    - Informações pessoais: cpf, telefone, data_nascimento
    - Integrações: nick_habbo, habbo_validado, wallet_address
    - Status: perfil_completo, is_staff, is_superuser
    - Timestamps: created_at, updated_at
    
    **Requer autenticação:** Sim (JWT Token)
    """,
    responses={
        200: OpenApiResponse(
            response=UserSerializer,
            description="Dados do perfil retornados com sucesso",
            examples=[
                OpenApiExample(
                    name="Perfil Completo",
                    value={
                        "id": 1,
                        "username": "usuario123",
                        "email": "usuario@example.com",
                        "first_name": "João",
                        "last_name": "Silva",
                        "cpf": "123.456.789-00",
                        "telefone": "(11) 98765-4321",
                        "data_nascimento": "1990-01-15",
                        "nick_habbo": "Maikkk.",
                        "habbo_validado": True,
                        "wallet_address": "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb",
                        "perfil_completo": True,
                        "is_staff": False,
                        "is_superuser": False,
                        "created_at": "2024-01-15T10:30:00Z",
                        "updated_at": "2024-01-20T14:45:00Z",
                    },
                    response_only=True,
                ),
                OpenApiExample(
                    name="Perfil Incompleto",
                    value={
                        "id": 2,
                        "username": "user_abc12345",
                        "email": None,
                        "first_name": None,
                        "last_name": None,
                        "cpf": None,
                        "telefone": None,
                        "data_nascimento": None,
                        "nick_habbo": None,
                        "habbo_validado": False,
                        "wallet_address": "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb",
                        "perfil_completo": False,
                        "is_staff": False,
                        "is_superuser": False,
                        "created_at": "2024-01-15T10:30:00Z",
                        "updated_at": "2024-01-15T10:30:00Z",
                    },
                    response_only=True,
                ),
            ],
        ),
        401: OpenApiResponse(
            description="Não autenticado - requer token JWT válido",
            examples=[
                OpenApiExample(
                    name="Token ausente",
                    value={
                        "detail": "As credenciais de autenticação não foram fornecidas."
                    },
                ),
                OpenApiExample(
                    name="Token inválido",
                    value={"detail": "Token inválido ou expirado."},
                ),
            ],
        ),
    },
)


user_profile_update_schema = extend_schema(
    operation_id="user_profile_update",
    tags=["accounts"],
    summary="Atualizar dados do perfil do usuário (substituição completa)",
    description="""
    Atualiza os dados do perfil do usuário autenticado usando substituição completa (PUT).
    
    **Importante:**
    - Todos os campos editáveis devem ser enviados (exceto os read-only)
    - Campos não enviados serão definidos como None/null
    - Use PATCH para atualização parcial
    
    **Campos editáveis:**
    - username, email, first_name, last_name
    - cpf, telefone, data_nascimento
    
    **Campos read-only (não podem ser editados diretamente):**
    - id, nick_habbo, habbo_validado, wallet_address
    - perfil_completo, is_staff, is_superuser
    - created_at, updated_at
    
    **Requer autenticação:** Sim (JWT Token)
    """,
    request=UserSerializer,
    responses={
        200: OpenApiResponse(
            response=UserSerializer,
            description="Perfil atualizado com sucesso",
            examples=[
                OpenApiExample(
                    name="Atualização bem-sucedida",
                    value={
                        "id": 1,
                        "username": "joao_silva",
                        "email": "joao.silva@example.com",
                        "first_name": "João",
                        "last_name": "Silva",
                        "cpf": "123.456.789-00",
                        "telefone": "(11) 98765-4321",
                        "data_nascimento": "1990-01-15",
                        "nick_habbo": "Maikkk.",
                        "habbo_validado": True,
                        "wallet_address": "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb",
                        "perfil_completo": True,
                        "is_staff": False,
                        "is_superuser": False,
                        "created_at": "2024-01-15T10:30:00Z",
                        "updated_at": "2024-01-20T15:00:00Z",
                    },
                    response_only=True,
                ),
            ],
        ),
        400: OpenApiResponse(
            description="Dados inválidos",
            examples=[
                OpenApiExample(
                    name="Email inválido",
                    value={
                        "email": ["Enter a valid email address."],
                    },
                ),
                OpenApiExample(
                    name="CPF inválido",
                    value={
                        "cpf": ["CPF inválido."],
                    },
                ),
                OpenApiExample(
                    name="Telefone inválido",
                    value={
                        "telefone": ["Telefone inválido."],
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


user_profile_partial_update_schema = extend_schema(
    operation_id="user_profile_partial_update",
    tags=["accounts"],
    summary="Atualizar parcialmente dados do perfil do usuário",
    description="""
    Atualiza parcialmente os dados do perfil do usuário autenticado (PATCH).
    
    **Vantagens sobre PUT:**
    - Apenas os campos enviados serão atualizados
    - Campos não enviados permanecem inalterados
    - Ideal para atualizações pontuais
    
    **Campos editáveis:**
    - username, email, first_name, last_name
    - cpf, telefone, data_nascimento
    
    **Exemplo de uso:**
    ```json
    {
        "email": "novo.email@example.com",
        "telefone": "(11) 98765-4321"
    }
    ```
    Apenas email e telefone serão atualizados, os demais campos permanecem inalterados.
    
    **Requer autenticação:** Sim (JWT Token)
    """,
    request=UserSerializer,
    responses={
        200: OpenApiResponse(
            response=UserSerializer,
            description="Perfil atualizado com sucesso",
            examples=[
                OpenApiExample(
                    name="Atualização parcial bem-sucedida",
                    value={
                        "id": 1,
                        "username": "usuario123",
                        "email": "novo.email@example.com",
                        "first_name": "João",
                        "last_name": "Silva",
                        "cpf": "123.456.789-00",
                        "telefone": "(11) 98765-4321",
                        "data_nascimento": "1990-01-15",
                        "nick_habbo": "Maikkk.",
                        "habbo_validado": True,
                        "wallet_address": "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb",
                        "perfil_completo": True,
                        "is_staff": False,
                        "is_superuser": False,
                        "created_at": "2024-01-15T10:30:00Z",
                        "updated_at": "2024-01-20T15:00:00Z",
                    },
                    response_only=True,
                ),
            ],
        ),
        400: OpenApiResponse(
            description="Dados inválidos",
            examples=[
                OpenApiExample(
                    name="Email inválido",
                    value={
                        "email": ["Enter a valid email address."],
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
