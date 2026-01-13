from django.contrib.auth.models import AbstractUser
from django.db import models
from django.core.validators import RegexValidator


class OptionalRegexValidator(RegexValidator):
    """Validador que só valida se o valor não estiver vazio"""
    
    def __call__(self, value):
        if value:
            super().__call__(value)


class User(AbstractUser):
    """
    Modelo customizado de usuário com dados brasileiros e integração MetaMask
    """
    
    username = models.CharField(
        max_length=150,
        unique=True,
        null=True,
        blank=True,
        help_text="Nome de usuário (opcional)",
    )

    cpf = models.CharField(
        max_length=14,
        unique=True,
        null=True,
        blank=True,
        validators=[
            OptionalRegexValidator(
                regex=r"^\d{3}\.\d{3}\.\d{3}-\d{2}$",
                message="CPF deve estar no formato XXX.XXX.XXX-XX",
            )
        ],
        help_text="CPF no formato XXX.XXX.XXX-XX",
    )

    telefone = models.CharField(
        max_length=15,
        null=True,
        blank=True,
        validators=[
            OptionalRegexValidator(
                regex=r"^\(\d{2}\)\s\d{4,5}-\d{4}$",
                message="Telefone deve estar no formato (XX) XXXXX-XXXX",
            )
        ],
        help_text="Telefone no formato (XX) XXXXX-XXXX",
    )

    data_nascimento = models.DateField(
        null=True, blank=True, help_text="Data de nascimento"
    )

    # Dados do Habbo
    nick_habbo = models.CharField(
        max_length=50,
        unique=True,
        null=True,
        blank=True,
        help_text="Nick do usuário no Habbo",
    )

    habbo_validado = models.BooleanField(
        default=False, help_text="Indica se o nick do Habbo foi validado"
    )

    palavra_validacao_habbo = models.CharField(
        max_length=50,
        null=True,
        blank=True,
        help_text="Palavra que deve aparecer no motto do Habbo para validação",
    )

    # Dados da carteira MetaMask
    wallet_address = models.CharField(
        max_length=42,
        unique=True,
        null=True,
        blank=True,
        validators=[
            OptionalRegexValidator(
                regex=r"^0x[a-fA-F0-9]{40}$",
                message="Endereço da carteira deve ser um endereço Ethereum válido",
            )
        ],
        help_text="Endereço da carteira MetaMask",
    )

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = "auth_user"
        verbose_name = "Usuário"
        verbose_name_plural = "Usuários"

    def __str__(self):
        username_display = self.username or "Sem username"
        return f"{username_display} ({self.wallet_address or 'Sem carteira'})"

    @property
    def perfil_completo(self):
        """Verifica se o perfil está completo"""
        return all(
            [
                self.cpf,
                self.telefone,
                self.data_nascimento,
                self.nick_habbo,
                self.habbo_validado,
                self.wallet_address,
            ]
        )


class HabboValidationTask(models.Model):
    """
    Modelo para rastrear tasks de validação do Habbo
    """

    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="habbo_validations"
    )
    nick_habbo = models.CharField(max_length=50)
    palavra_validacao = models.CharField(max_length=50)
    task_id = models.CharField(max_length=255, unique=True)

    STATUS_CHOICES = [
        ("pending", "Pendente"),
        ("processing", "Processando"),
        ("success", "Sucesso"),
        ("failed", "Falhou"),
    ]

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    resultado = models.TextField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Validação do Habbo"
        verbose_name_plural = "Validações do Habbo"
        ordering = ["-created_at"]

    def __str__(self):
        return f"Validação {self.nick_habbo} - {self.status}"
