from django.contrib import admin
from django.utils.html import format_html
from .models import Banner


@admin.register(Banner)
class BannerAdmin(admin.ModelAdmin):
    list_display = ["title", "is_active", "order", "created_at", "image_preview"]

    list_filter = ["is_active", "created_at"]

    search_fields = ["title"]

    list_editable = ["is_active", "order"]

    fieldsets = (
        ("Informações Básicas", {"fields": ("title", "is_active", "order")}),
        (
            "Imagem",
            {
                "fields": ("image_url", "image_mobile"),
                "description": "Cole a URL da imagem do banner (ex: https://exemplo.com/imagem.jpg). Formatos recomendados: JPG, PNG, WebP. A imagem mobile é opcional.",
            },
        ),
    )

    def image_preview(self, obj):
        """Mostra uma prévia da imagem do banner"""
        if obj.image_url:
            return format_html(
                '<img src="{}" style="max-width: 100px; max-height: 50px; object-fit: cover;" />',
                obj.image_url,
            )
        return "-"

    image_preview.short_description = "Prévia da Imagem"

    def get_queryset(self, request):
        return super().get_queryset(request).order_by("order", "-created_at")
