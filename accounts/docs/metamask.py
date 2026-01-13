"""
Documentação das rotas de autenticação MetaMask.
"""

from drf_spectacular.utils import (
    extend_schema,
    OpenApiParameter,
    OpenApiResponse,
    OpenApiExample,
)
from drf_spectacular.types import OpenApiTypes
from ..serializers.auth import (
    MetaMaskAuthSerializer,
    AuthResponseSerializer,
)
from ..serializers.user import (
    UserSerializer,
    UserRegistrationSerializer,
)


metamask_auth_schema = extend_schema(
    operation_id="metamask_auth",
    tags=["accounts"],
    summary="Autenticar usuário via MetaMask",
    description="""
    Autentica um usuário usando assinatura da carteira MetaMask.
    
    **Como funciona:**
    1. Obtenha uma mensagem para assinar via GET /accounts/auth/metamask/message/
    2. Assine a mensagem com sua carteira MetaMask
    3. Envie o endereço da carteira, a mensagem e a assinatura para esta rota
    4. Se o usuário não existir, ele será criado automaticamente
    5. Tokens JWT serão retornados para autenticação
    
    **Fluxo completo:**
    ```
    1. GET /accounts/auth/metamask/message/?wallet_address=0x...
       → Retorna mensagem para assinar
    2. Usuário assina mensagem no MetaMask
    3. POST /accounts/auth/metamask/login/
       → Envia wallet_address, message, signature
       → Retorna access_token, refresh_token, user
    ```
    
    **Requer autenticação:** Não (público)
    """,
    request=MetaMaskAuthSerializer,
    responses={
        200: OpenApiResponse(
            response=AuthResponseSerializer,
            description="Autenticação bem-sucedida",
            examples=[
                OpenApiExample(
                    name="Usuário existente",
                    value={
                        "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
                        "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
                        "user": {
                            "id": 1,
                            "username": "user_abc12345",
                            "email": "usuario@example.com",
                            "first_name": "João",
                            "last_name": "Silva",
                            "wallet_address": "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb",
                            "perfil_completo": True,
                        },
                        "is_new_user": False,
                    },
                    response_only=True,
                ),
                OpenApiExample(
                    name="Novo usuário criado",
                    value={
                        "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
                        "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
                        "user": {
                            "id": 2,
                            "username": "user_abc12345",
                            "email": None,
                            "first_name": None,
                            "last_name": None,
                            "wallet_address": "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb",
                            "perfil_completo": False,
                        },
                        "is_new_user": True,
                    },
                    response_only=True,
                ),
            ],
        ),
        400: OpenApiResponse(
            description="Dados inválidos",
            examples=[
                OpenApiExample(
                    name="Endereço inválido",
                    value={
                        "wallet_address": [
                            "Endereço da carteira deve ser um endereço Ethereum válido"
                        ],
                    },
                ),
                OpenApiExample(
                    name="Campos obrigatórios ausentes",
                    value={
                        "wallet_address": ["Este campo é obrigatório."],
                        "signature": ["Este campo é obrigatório."],
                        "message": ["Este campo é obrigatório."],
                    },
                ),
            ],
        ),
        401: OpenApiResponse(
            description="Assinatura inválida",
            examples=[
                OpenApiExample(
                    name="Assinatura não corresponde",
                    value={
                        "error": "Assinatura inválida",
                    },
                ),
            ],
        ),
    },
)


metamask_register_schema = extend_schema(
    operation_id="metamask_register",
    tags=["accounts"],
    summary="Registrar novo usuário com dados completos via MetaMask",
    description="""
    Registra um novo usuário com dados completos usando autenticação MetaMask.
    
    **Diferença do login:**
    - Esta rota permite criar um usuário com todos os dados de uma vez (nome, email, CPF, etc.)
    - A rota de login apenas cria um usuário básico se não existir
    
    **Campos obrigatórios:**
    - wallet_address: Endereço da carteira Ethereum (0x...)
    - signature: Assinatura da mensagem
    - message: Mensagem que foi assinada
    - email: Email do usuário
    - first_name: Primeiro nome
    - last_name: Sobrenome
    
    **Campos opcionais:**
    - username: Nome de usuário (se não fornecido, será gerado)
    - cpf: CPF do usuário
    - telefone: Telefone do usuário
    - data_nascimento: Data de nascimento
    - nick_habbo: Nick do Habbo (será validado posteriormente)
    
    **Validações:**
    - wallet_address deve ser um endereço Ethereum válido
    - wallet_address não pode estar associado a outro usuário
    - username deve ser único (se fornecido)
    - email deve ser válido e único
    - nick_habbo não pode estar associado a outro usuário (se fornecido)
    
    **Requer autenticação:** Não (público)
    """,
    request=UserRegistrationSerializer,
    responses={
        201: OpenApiResponse(
            response=AuthResponseSerializer,
            description="Usuário registrado com sucesso",
            examples=[
                OpenApiExample(
                    name="Registro bem-sucedido",
                    value={
                        "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
                        "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
                        "user": {
                            "id": 1,
                            "username": "joao_silva",
                            "email": "joao.silva@example.com",
                            "first_name": "João",
                            "last_name": "Silva",
                            "cpf": "123.456.789-00",
                            "telefone": "(11) 98765-4321",
                            "data_nascimento": "1990-01-15",
                            "nick_habbo": None,
                            "habbo_validado": False,
                            "wallet_address": "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb",
                            "perfil_completo": True,
                        },
                        "is_new_user": True,
                    },
                    response_only=True,
                ),
            ],
        ),
        400: OpenApiResponse(
            description="Dados inválidos",
            examples=[
                OpenApiExample(
                    name="Email já em uso",
                    value={
                        "email": ["Este email já está em uso."],
                    },
                ),
                OpenApiExample(
                    name="Carteira já associada",
                    value={
                        "wallet_address": [
                            "Esta carteira já está associada a outro usuário."
                        ],
                    },
                ),
                OpenApiExample(
                    name="Username já em uso",
                    value={
                        "username": ["Este nome de usuário já está em uso."],
                    },
                ),
                OpenApiExample(
                    name="Nick Habbo já associado",
                    value={
                        "nick_habbo": [
                            "Este nick do Habbo já está associado a outro usuário. Um nick só pode estar vinculado a um usuário por vez."
                        ],
                    },
                ),
                OpenApiExample(
                    name="Campos obrigatórios ausentes",
                    value={
                        "email": ["Este campo é obrigatório."],
                        "first_name": ["Este campo é obrigatório."],
                        "last_name": ["Este campo é obrigatório."],
                    },
                ),
            ],
        ),
        401: OpenApiResponse(
            description="Assinatura inválida",
            examples=[
                OpenApiExample(
                    name="Assinatura não corresponde",
                    value={
                        "error": "Assinatura inválida",
                    },
                ),
            ],
        ),
    },
)


generate_auth_message_schema = extend_schema(
    operation_id="generate_auth_message",
    tags=["accounts"],
    summary="Gerar mensagem para assinatura MetaMask",
    description="""
    Gera uma mensagem única para ser assinada com a carteira MetaMask.
    
    **Uso:**
    1. Chame esta rota com o endereço da carteira
    2. Receba a mensagem formatada
    3. Peça ao usuário para assinar a mensagem no MetaMask
    4. Use a mensagem e assinatura para autenticar via POST /accounts/auth/metamask/login/
    
    **Formato da mensagem:**
    ```
    Bem-vindo ao NFT Portal!
    
    Esta solicitação não custará nada.
    
    Endereço da carteira: 0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb
    Nonce: abc123def456...
    Timestamp: 2024-01-20T14:30:00.123456+00:00
    
    Assine esta mensagem para autenticar-se no NFT Portal.
    ```
    
    **Segurança:**
    - Cada mensagem contém um nonce único
    - O timestamp garante que a mensagem não seja reutilizada
    - A mensagem é específica para o endereço da carteira
    
    **Requer autenticação:** Não (público)
    """,
    parameters=[
        OpenApiParameter(
            name="wallet_address",
            type=OpenApiTypes.STR,
            location=OpenApiParameter.QUERY,
            description="Endereço da carteira MetaMask (formato: 0x seguido de 40 caracteres hexadecimais)",
            required=True,
            examples=[
                OpenApiExample(
                    name="Endereço válido",
                    value="0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb",
                    description="Endereço Ethereum válido",
                ),
            ],
        )
    ],
    responses={
        200: OpenApiResponse(
            description="Mensagem gerada com sucesso",
            examples=[
                OpenApiExample(
                    name="Mensagem gerada",
                    value={
                        "message": "Bem-vindo ao NFT Portal!\n\nEsta solicitação não custará nada.\n\nEndereço da carteira: 0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb\nNonce: abc123def456789012345678901234567890\nTimestamp: 2024-01-20T14:30:00.123456+00:00\n\nAssine esta mensagem para autenticar-se no NFT Portal.",
                        "nonce": "abc123def456789012345678901234567890",
                        "timestamp": "2024-01-20T14:30:00.123456+00:00",
                    },
                ),
            ],
        ),
        400: OpenApiResponse(
            description="Endereço da carteira inválido ou ausente",
            examples=[
                OpenApiExample(
                    name="Endereço ausente",
                    value={
                        "error": "Endereço da carteira é obrigatório",
                    },
                ),
                OpenApiExample(
                    name="Endereço inválido",
                    value={
                        "error": "Endereço da carteira deve ser um endereço Ethereum válido",
                    },
                ),
            ],
        ),
    },
)
