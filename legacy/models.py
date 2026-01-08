from pydoc import describe
from django.db import models

class Item(models.Model):
    name = models.CharField(max_length=255)
    image_url = models.URLField(max_length=500, blank=True)
    description = models.TextField(blank=True)
    slug = models.SlugField(max_length=255, unique=True)
    last_price = models.DecimalField(max_digits=10, decimal_places=2)
    average_price = models.DecimalField(max_digits=10, decimal_places=2)
    available_offers = models.IntegerField()
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
