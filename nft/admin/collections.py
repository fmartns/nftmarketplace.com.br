from django.contrib import admin, messages
from django.db import transaction
from django.urls import path
from django.shortcuts import render, redirect
from decimal import Decimal
import json
from ..models import NftCollection


@admin.register(NftCollection)
class NftCollectionAdmin(admin.ModelAdmin):
    list_display = [
        "name",
        "author",
        "items_count",
        "owners_count",
        "floor_price_eth",
        "total_volume_eth",
        "created_at",
    ]
    list_filter = ["created_at", "updated_at"]
    search_fields = ["name", "description", "address", "creator_name"]
    readonly_fields = ["slug", "created_at", "updated_at", "author"]
    change_list_template = "admin/nft/nftcollection/change_list.html"

    fieldsets = (
        ("Informações Básicas", {"fields": ("name", "slug", "description", "address")}),
        ("Imagens", {"fields": ("profile_image", "cover_image")}),
        ("Criador", {"fields": ("creator", "creator_name", "author")}),
        (
            "Estatísticas",
            {
                "fields": (
                    "items_count",
                    "owners_count",
                    "floor_price",
                    "total_volume",
                )
            },
        ),
        (
            "Site Oficial",
            {
                "fields": ("website_url",),
            },
        ),
        (
            "Redes Sociais",
            {
                "fields": (
                    "twitter_url",
                    "instagram_url",
                    "discord_url",
                    "telegram_url",
                ),
                "classes": ("collapse",),
            },
        ),
        (
            "Metadados",
            {
                "fields": (
                    "metadata_api_url",
                    "project_id",
                    "project_owner_address",
                ),
                "classes": ("collapse",),
            },
        ),
        ("Timestamps", {"fields": ("created_at", "updated_at")}),
    )

    # --- Import JSON custom admin view ---
    def get_urls(self):
        urls = super().get_urls()
        custom = [
            path(
                "import-json/",
                self.admin_site.admin_view(self.import_json_view),
                name="nft_nftcollection_import_json",
            )
        ]
        return custom + urls

    def import_json_view(self, request):
        context = {**self.admin_site.each_context(request)}
        context.update(
            {
                "opts": self.model._meta,
                "title": "Importar coleções via JSON",
            }
        )

        if request.method == "POST":
            raw = request.POST.get("payload", "").strip()
            update_existing = request.POST.get("update_existing") == "on"
            try:
                data = json.loads(raw)
            except json.JSONDecodeError as e:
                messages.error(request, f"JSON inválido: {e}")
                return render(
                    request, "admin/nft/nftcollection/import_json.html", context
                )

            # Aceita {"collections": [...]} ou um único objeto
            items = []
            if (
                isinstance(data, dict)
                and "collections" in data
                and isinstance(data["collections"], list)
            ):
                items = data["collections"]
            elif isinstance(data, dict):
                items = [data]
            elif isinstance(data, list):
                items = data
            else:
                messages.error(
                    request,
                    'Estrutura JSON não reconhecida. Informe um objeto, lista ou {"collections": [...]}.',
                )
                return render(
                    request, "admin/nft/nftcollection/import_json.html", context
                )

            created = 0
            updated = 0
            errors = 0

            @transaction.atomic
            def _import():
                nonlocal created, updated, errors
                for idx, obj in enumerate(items, start=1):
                    try:
                        address = (obj.get("address") or "").strip()
                        if not address:
                            raise ValueError(
                                "Campo 'address' é obrigatório em cada coleção"
                            )

                        defaults = {}
                        # Map simple fields
                        for src, dst in [
                            ("name", "name"),
                            ("description", "description"),
                            ("metadata_api_url", "metadata_api_url"),
                            ("project_id", "project_id"),
                            ("project_owner_address", "project_owner_address"),
                            ("website_url", "website_url"),
                            ("twitter_url", "twitter_url"),
                            ("instagram_url", "instagram_url"),
                            ("discord_url", "discord_url"),
                            ("telegram_url", "telegram_url"),
                            ("creator_name", "creator_name"),
                        ]:
                            val = obj.get(src)
                            if val is not None:
                                defaults[dst] = val

                        # Images mapping with fallbacks
                        profile_image = obj.get("profile_image") or obj.get("icon_url")
                        cover_image = obj.get("cover_image") or obj.get(
                            "collection_image_url"
                        )
                        if profile_image:
                            defaults["profile_image"] = profile_image
                        if cover_image:
                            defaults["cover_image"] = cover_image

                        # Numeric fields
                        for src, dst, cast in [
                            ("items_count", "items_count", int),
                            ("owners_count", "owners_count", int),
                        ]:
                            if obj.get(src) is not None:
                                try:
                                    defaults[dst] = cast(obj.get(src))
                                except Exception:
                                    pass

                        for src, dst in [
                            ("floor_price", "floor_price"),
                            ("total_volume", "total_volume"),
                        ]:
                            if obj.get(src) is not None:
                                try:
                                    defaults[dst] = Decimal(str(obj.get(src)))
                                except Exception:
                                    pass

                        if update_existing:
                            # update_or_create by address
                            _, created_flag = NftCollection.objects.update_or_create(
                                address=address, defaults=defaults
                            )
                            if created_flag:
                                created += 1
                            else:
                                updated += 1
                        else:
                            # create if not exists; skip if exists
                            obj_qs = NftCollection.objects.filter(address=address)
                            if obj_qs.exists():
                                updated += 1  # contado como 'existente (pulado)'
                            else:
                                NftCollection.objects.create(
                                    address=address, **defaults
                                )
                                created += 1
                    except Exception:
                        errors += 1
                        # continua importação

            _import()

            if created:
                messages.success(request, f"{created} coleção(ões) criada(s)")
            if updated:
                messages.info(
                    request, f"{updated} coleção(ões) atualizada(s)/existentes"
                )
            if errors:
                messages.warning(
                    request, f"{errors} item(ns) com erro; verifique o JSON"
                )

            return redirect("admin:nft_nftcollection_changelist")

        return render(request, "admin/nft/nftcollection/import_json.html", context)
