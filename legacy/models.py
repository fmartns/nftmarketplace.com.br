from django.db import models
from django.core.validators import RegexValidator


# Validador customizado que aceita qualquer caractere (incluindo asteriscos)
class FlexibleSlugValidator(RegexValidator):
    regex = r"^.+$"  # Aceita qualquer caractere não vazio
    message = "O slug pode conter qualquer caractere."


class Item(models.Model):
    name = models.CharField(max_length=255)
    image_url = models.URLField(max_length=500, blank=True)
    description = models.TextField(blank=True)
    # Usar CharField em vez de SlugField para aceitar asteriscos e outros caracteres
    slug = models.CharField(
        max_length=255,
        unique=True,
        validators=[FlexibleSlugValidator()],
        db_index=True,  # Manter índice para performance
    )
    last_price = models.DecimalField(max_digits=10, decimal_places=2)
    average_price = models.DecimalField(max_digits=10, decimal_places=2)
    available_offers = models.IntegerField()
    can_buy_multiple = models.BooleanField(
        default=False,
        help_text="Permite compra em maior quantidade (legacy itens).",
    )
    price_history = models.JSONField(default=list, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]
        indexes = [
            models.Index(fields=["slug"]),
        ]

    def __str__(self):
        return self.name


class DefaultPricingConfig(models.Model):
    bar_value = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["bar_value"]
        indexes = [
            models.Index(fields=["bar_value"]),
        ]

    def __str__(self):
        return f"{self.bar_value}"
