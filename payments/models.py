"""
Modelos para integração com AbacatePay
"""
from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator
from decimal import Decimal


class AbacatePayCustomer(models.Model):
    """
    Cliente na AbacatePay
    """
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="abacatepay_customer",
        help_text="Usuário associado",
    )
    
    external_id = models.CharField(
        max_length=255,
        unique=True,
        db_index=True,
        help_text="ID do cliente na AbacatePay (ex: cust_12345)",
    )
    
    metadata = models.JSONField(
        default=dict,
        blank=True,
        help_text="Metadados adicionais do cliente",
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Cliente AbacatePay"
        verbose_name_plural = "Clientes AbacatePay"
        ordering = ["-created_at"]
    
    def __str__(self):
        return f"{self.user.username} - {self.external_id}"


class AbacatePayBilling(models.Model):
    """
    Cobrança (Billing) na AbacatePay
    """
    order = models.OneToOneField(
        "orders.Order",
        on_delete=models.CASCADE,
        related_name="abacatepay_billing",
        help_text="Pedido associado",
    )
    
    customer = models.ForeignKey(
        AbacatePayCustomer,
        on_delete=models.PROTECT,
        related_name="billings",
        help_text="Cliente que fez a cobrança",
    )
    
    billing_id = models.CharField(
        max_length=255,
        unique=True,
        db_index=True,
        help_text="ID da cobrança na AbacatePay (ex: bill_12345667)",
    )
    
    payment_url = models.URLField(
        max_length=500,
        blank=True,
        help_text="URL para pagamento",
    )
    
    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.01"))],
        help_text="Valor da cobrança em reais",
    )
    
    STATUS_CHOICES = [
        ("PENDING", "Pendente"),
        ("PAID", "Pago"),
        ("EXPIRED", "Expirado"),
        ("CANCELLED", "Cancelado"),
    ]
    
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="PENDING",
        db_index=True,
        help_text="Status da cobrança",
    )
    
    methods = models.JSONField(
        default=list,
        help_text="Métodos de pagamento disponíveis (ex: ['PIX', 'CARD'])",
    )
    
    frequency = models.CharField(
        max_length=50,
        default="ONE_TIME",
        help_text="Frequência da cobrança (ONE_TIME, RECURRING, etc.)",
    )
    
    dev_mode = models.BooleanField(
        default=False,
        help_text="Se a cobrança está em modo de desenvolvimento",
    )
    
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Cobrança AbacatePay"
        verbose_name_plural = "Cobranças AbacatePay"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["billing_id"]),
            models.Index(fields=["status"]),
            models.Index(fields=["customer"]),
        ]
    
    def __str__(self):
        return f"{self.billing_id} - {self.order.order_id} - {self.status}"


class AbacatePayPayment(models.Model):
    """
    Pagamento processado pela AbacatePay
    """
    billing = models.ForeignKey(
        AbacatePayBilling,
        on_delete=models.CASCADE,
        related_name="payments",
        help_text="Cobrança associada",
    )
    
    order = models.ForeignKey(
        "orders.Order",
        on_delete=models.CASCADE,
        related_name="abacatepay_payments",
        help_text="Pedido associado",
    )
    
    payment_url = models.URLField(
        max_length=500,
        blank=True,
        help_text="URL para pagamento",
    )
    
    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.01"))],
        help_text="Valor pago",
    )
    
    STATUS_CHOICES = [
        ("PENDING", "Pendente"),
        ("PAID", "Pago"),
        ("EXPIRED", "Expirado"),
        ("CANCELLED", "Cancelado"),
        ("FAILED", "Falhou"),
    ]
    
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="PENDING",
        db_index=True,
        help_text="Status do pagamento",
    )
    
    PAYMENT_METHOD_CHOICES = [
        ("PIX", "PIX"),
        ("CARD", "Cartão de Crédito"),
        ("BOLETO", "Boleto"),
    ]
    
    payment_method = models.CharField(
        max_length=20,
        choices=PAYMENT_METHOD_CHOICES,
        blank=True,
        help_text="Método de pagamento usado",
    )
    
    raw_response = models.JSONField(
        default=dict,
        help_text="Resposta completa da API da AbacatePay",
    )
    
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)
    paid_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Data/hora em que o pagamento foi confirmado",
    )
    
    class Meta:
        verbose_name = "Pagamento AbacatePay"
        verbose_name_plural = "Pagamentos AbacatePay"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["billing"]),
            models.Index(fields=["status"]),
            models.Index(fields=["order"]),
        ]
    
    def __str__(self):
        return f"{self.billing.billing_id} - {self.order.order_id} - {self.status}"
