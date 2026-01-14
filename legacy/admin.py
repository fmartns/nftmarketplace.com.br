from django.contrib import admin
from django.contrib import messages
from .models import Item
from .services import LegacyPriceService


@admin.register(Item)
class ItemAdmin(admin.ModelAdmin):
    list_display = [
        "name",
        "slug",
        "last_price",
        "average_price",
        "available_offers",
        "created_at",
        "updated_at",
    ]
    list_filter = ["created_at", "updated_at"]
    search_fields = ["name", "slug", "description"]
    readonly_fields = ["created_at", "updated_at", "price_history"]

    fieldsets = (
        (
            "Informações Básicas",
            {
                "fields": ("name", "slug", "description", "image_url"),
            },
        ),
        (
            "Preços",
            {
                "fields": ("last_price", "average_price", "available_offers"),
            },
        ),
        (
            "Histórico",
            {
                "fields": ("price_history",),
                "classes": ("collapse",),
            },
        ),
        (
            "Timestamps",
            {
                "fields": ("created_at", "updated_at"),
                "classes": ("collapse",),
            },
        ),
    )

    actions = ["create_from_slug", "refresh_from_api"]

    def create_from_slug(self, request, queryset):
        """Cria ou atualiza item a partir do slug usando a API externa"""
        if queryset.count() != 1:
            self.message_user(
                request,
                "Por favor, selecione exatamente um item para criar/atualizar.",
                level=messages.ERROR,
            )
            return

        item = queryset.first()
        slug = item.slug

        try:
            item_data = LegacyPriceService.get_item_data(slug)

            item.name = item_data["name"]
            item.image_url = item_data["image_url"]
            item.description = item_data.get("description", "")
            item.last_price = item_data["last_price"]
            item.average_price = item_data["average_price"]
            item.available_offers = item_data["available_offers"]
            item.price_history = item_data.get("price_history")
            item.save()

            self.message_user(
                request,
                f"Item '{item.name}' atualizado com sucesso a partir da API.",
                level=messages.SUCCESS,
            )
        except ValueError as e:
            self.message_user(
                request,
                f"Erro ao buscar dados da API: {str(e)}",
                level=messages.ERROR,
            )

    create_from_slug.short_description = "Criar/Atualizar item a partir da API externa"

    def refresh_from_api(self, request, queryset):
        """Atualiza itens selecionados a partir da API externa"""
        updated = 0
        errors = 0

        for item in queryset:
            try:
                item_data = LegacyPriceService.get_item_data(item.slug)

                item.name = item_data["name"]
                item.image_url = item_data["image_url"]
                item.description = item_data.get("description", "")
                item.last_price = item_data["last_price"]
                item.average_price = item_data["average_price"]
                item.available_offers = item_data["available_offers"]
                item.price_history = item_data.get("price_history")
                item.save()
                updated += 1
            except Exception as e:
                errors += 1
                self.message_user(
                    request,
                    f"Erro ao atualizar '{item.slug}': {str(e)}",
                    level=messages.WARNING,
                )

        if updated:
            self.message_user(
                request,
                f"{updated} item(ns) atualizado(s) com sucesso.",
                level=messages.SUCCESS,
            )
        if errors:
            self.message_user(
                request,
                f"{errors} item(ns) com erro.",
                level=messages.WARNING,
            )

    refresh_from_api.short_description = "Atualizar itens selecionados da API externa"
