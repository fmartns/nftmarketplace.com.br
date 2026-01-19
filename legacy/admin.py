from django.contrib import admin
from django.contrib import messages
from django import forms
from django.shortcuts import render, redirect
from django.urls import path
from django.db import transaction
from django.http import HttpResponse
from decimal import Decimal
import json
from .models import Item
from .services import LegacyPriceService


class SlugInputNoValidation(forms.TextInput):
    """Widget customizado que remove validação HTML5 do slug"""

    def __init__(self, attrs=None):
        if attrs is None:
            attrs = {}
        # Remover qualquer validação HTML5 - não definir pattern
        attrs.pop("pattern", None)
        attrs.pop("data-pattern", None)
        super().__init__(attrs)

    def render(self, name, value, attrs=None, renderer=None):
        """Renderizar sem atributos de validação"""
        if attrs is None:
            attrs = {}
        # Garantir que não há pattern
        attrs.pop("pattern", None)
        attrs.pop("data-pattern", None)
        return super().render(name, value, attrs, renderer)


class ItemCreateForm(forms.ModelForm):
    """Formulário simplificado para criação - apenas slug"""

    class Meta:
        model = Item
        # Não incluir slug aqui - será adicionado manualmente como CharField
        fields = [
            "name",
            "description",
            "image_url",
            "last_price",
            "average_price",
            "available_offers",
        ]
        exclude = []

    def __init__(self, *args, **kwargs):
        # Chamar super().__init__() primeiro
        super().__init__(*args, **kwargs)

        # Adicionar campo slug manualmente como CharField (não SlugField)
        # Isso garante que nunca seja criado como SlugField
        from django import forms as django_forms

        slug_field = django_forms.CharField(
            max_length=255,
            label="ID/Slug do Item",
            help_text="Digite apenas o ID (slug) do item. Os demais dados serão buscados automaticamente da API externa.",
            required=True,
            validators=[],  # Sem validadores
        )
        # Usar widget customizado que remove validação HTML5
        slug_field.widget = SlugInputNoValidation()
        # Adicionar o campo slug ao formulário (não substituir, pois não existe ainda)
        self.fields["slug"] = slug_field

        # Tornar todos os campos opcionais na criação (exceto slug)
        for field_name, field in self.fields.items():
            if field_name != "slug":
                field.required = False
                field.widget = (
                    forms.HiddenInput()
                )  # Esconder campos que serão preenchidos automaticamente
                # Definir valores temporários para campos obrigatórios (serão substituídos no save_model)
                if field_name == "name":
                    self.fields[field_name].initial = "Temporary - will be replaced"
                elif field_name == "last_price":
                    self.fields[field_name].initial = 0
                elif field_name == "average_price":
                    self.fields[field_name].initial = 0
                elif field_name == "available_offers":
                    self.fields[field_name].initial = 0

    def clean_slug(self):
        """Validação customizada do slug - aceita asteriscos e outros caracteres"""
        slug = self.cleaned_data.get("slug")
        if not slug:
            raise forms.ValidationError("Este campo é obrigatório.")
        # Aceitar qualquer caractere (incluindo asteriscos)
        # A validação do modelo será feita no save_model
        return slug

    def clean(self):
        """Preencher valores temporários para campos obrigatórios se não fornecidos"""
        cleaned_data = super().clean()
        # Preencher valores temporários para campos obrigatórios que não foram fornecidos
        from decimal import Decimal

        if not cleaned_data.get("name"):
            cleaned_data["name"] = "Temporary - will be replaced"
        if cleaned_data.get("last_price") is None:
            cleaned_data["last_price"] = Decimal("0.00")
        if cleaned_data.get("average_price") is None:
            cleaned_data["average_price"] = Decimal("0.00")
        if cleaned_data.get("available_offers") is None:
            cleaned_data["available_offers"] = 0
        return cleaned_data

    def save(self, commit=True):
        """Salvar sem commit - os dados serão preenchidos no save_model do admin"""
        # Criar instância com valores temporários para passar validação
        instance = super().save(commit=False)
        return instance


class ItemChangeForm(forms.ModelForm):
    """Formulário completo para edição"""

    class Meta:
        model = Item
        fields = "__all__"


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
    change_list_template = "admin/legacy/item/change_list.html"

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

    def formfield_for_dbfield(self, db_field, request, **kwargs):
        """Sobrescrever o campo slug para aceitar asteriscos na criação"""
        # Verificar se estamos na página de adicionar (não editar)
        if db_field.name == "slug":
            try:
                url_name = (
                    request.resolver_match.url_name
                    if hasattr(request, "resolver_match")
                    else None
                )
                if url_name and "add" in url_name:
                    # Na criação, criar CharField diretamente em vez de SlugField
                    # Remover todos os argumentos específicos do SlugField
                    kwargs.pop("allow_unicode", None)
                    kwargs.pop("form_class", None)
                    # Criar CharField diretamente
                    return forms.CharField(
                        max_length=255,
                        required=not db_field.blank,
                        validators=[],
                        **{
                            k: v
                            for k, v in kwargs.items()
                            if k not in ["form_class", "allow_unicode"]
                        },
                    )
            except Exception:
                pass
        return super().formfield_for_dbfield(db_field, request, **kwargs)

    def get_form(self, request, obj=None, **kwargs):
        """Usa formulário simplificado na criação, completo na edição"""
        if obj is None:
            # Criação - apenas slug
            kwargs["form"] = ItemCreateForm
        else:
            # Edição - todos os campos
            kwargs["form"] = ItemChangeForm
        return super().get_form(request, obj, **kwargs)

    def get_fieldsets(self, request, obj=None):
        """Mostra apenas o slug na criação, todos os campos na edição"""
        if obj is None:
            # Criação - apenas slug visível
            return (
                (
                    "Criar Item",
                    {
                        "fields": ("slug",),
                        "description": "Digite apenas o ID (slug) do item. Os demais dados serão buscados automaticamente da API externa.",
                    },
                ),
            )
        else:
            # Edição - todos os campos
            return self.fieldsets

    def save_model(self, request, obj, form, change):
        """Busca dados da API ao criar novo item"""
        if not change:  # Se é criação (não edição)
            slug = form.cleaned_data.get("slug")
            if slug:
                # Remover validadores do slug temporariamente para aceitar asteriscos
                slug_field = obj._meta.get_field("slug")
                original_validators = slug_field.validators[:]  # Copiar lista
                slug_field.validators = []

                try:
                    # Buscar dados da API externa
                    item_data = LegacyPriceService.get_item_data(slug)

                    # Preencher todos os campos com os dados da API
                    obj.name = item_data["name"]
                    obj.image_url = item_data["image_url"]
                    obj.description = item_data.get("description", "")
                    obj.last_price = item_data["last_price"]
                    obj.average_price = item_data["average_price"]
                    obj.available_offers = item_data["available_offers"]
                    obj.price_history = item_data.get("price_history", [])

                    # Definir o slug (pode conter asteriscos)
                    obj.slug = slug

                    # Salvar o objeto (validadores do slug já foram removidos acima)
                    obj.save()

                    self.message_user(
                        request,
                        f"Item '{obj.name}' criado com sucesso a partir da API externa.",
                        level=messages.SUCCESS,
                    )
                except ValueError as e:
                    self.message_user(
                        request,
                        f"Erro ao buscar dados da API: {str(e)}. Item não foi criado.",
                        level=messages.ERROR,
                    )
                except Exception as e:
                    self.message_user(
                        request,
                        f"Erro ao salvar item: {str(e)}. Item não foi criado.",
                        level=messages.ERROR,
                    )
                finally:
                    # Sempre restaurar validadores
                    slug_field.validators = original_validators
        else:
            # Edição normal - salvar normalmente
            super().save_model(request, obj, form, change)

    actions = ["create_from_slug", "refresh_from_api"]

    def get_urls(self):
        urls = super().get_urls()
        custom = [
            path(
                "import-json/",
                self.admin_site.admin_view(self.import_json_view),
                name="legacy_item_import_json",
            ),
            path(
                "download-links/",
                self.admin_site.admin_view(self.download_links_view),
                name="legacy_item_download_links",
            ),
        ]
        return custom + urls

    def import_json_view(self, request):
        """View para importar itens legacy a partir de um arquivo JSON"""
        context = {**self.admin_site.each_context(request)}
        context.update(
            {
                "opts": self.model._meta,
                "title": "Importar Itens Legacy via JSON",
                "has_view_permission": self.has_view_permission(request),
            }
        )

        if request.method == "POST":
            # Aceita tanto upload de arquivo quanto cola de texto
            json_data = None
            if "json_file" in request.FILES:
                file = request.FILES["json_file"]
                try:
                    json_data = json.loads(file.read().decode("utf-8"))
                except json.JSONDecodeError as e:
                    messages.error(request, f"Erro ao ler arquivo JSON: {e}")
                    return render(
                        request, "admin/legacy/item/import_json.html", context
                    )
            elif "json_text" in request.POST:
                json_text = request.POST.get("json_text", "").strip()
                if json_text:
                    try:
                        json_data = json.loads(json_text)
                    except json.JSONDecodeError as e:
                        messages.error(request, f"JSON inválido: {e}")
                        return render(
                            request, "admin/legacy/item/import_json.html", context
                        )
                else:
                    messages.error(
                        request,
                        "Por favor, forneça um arquivo JSON ou cole o conteúdo JSON.",
                    )
                    return render(
                        request, "admin/legacy/item/import_json.html", context
                    )
            else:
                messages.error(
                    request,
                    "Por favor, forneça um arquivo JSON ou cole o conteúdo JSON.",
                )
                return render(request, "admin/legacy/item/import_json.html", context)

            if not json_data:
                messages.error(request, "Nenhum dado JSON foi fornecido.")
                return render(request, "admin/legacy/item/import_json.html", context)

            # Processar o JSON - aceita formato legacy.json
            items_to_import = []

            # Verificar se tem estrutura data.topSold ou data.topVolume
            if isinstance(json_data, dict) and "data" in json_data:
                data = json_data["data"]
                # Combinar topSold e topVolume (removendo duplicatas por classname)
                seen_classnames = set()
                for item_list in [data.get("topSold", []), data.get("topVolume", [])]:
                    if isinstance(item_list, list):
                        for item in item_list:
                            if isinstance(item, dict) and "classname" in item:
                                classname = item.get("classname")
                                if classname and classname not in seen_classnames:
                                    items_to_import.append(item)
                                    seen_classnames.add(classname)
            elif isinstance(json_data, list):
                # Se for uma lista direta de itens
                items_to_import = json_data
            elif isinstance(json_data, dict) and "classname" in json_data:
                # Se for um único item
                items_to_import = [json_data]
            else:
                messages.error(
                    request,
                    "Estrutura JSON não reconhecida. Esperado formato com 'data.topSold' e 'data.topVolume', ou lista de itens.",
                )
                return render(request, "admin/legacy/item/import_json.html", context)

            if not items_to_import:
                messages.warning(
                    request, "Nenhum item encontrado no JSON para importar."
                )
                return render(request, "admin/legacy/item/import_json.html", context)

            created = 0
            updated = 0
            errors = 0
            error_messages = []

            @transaction.atomic
            def _import():
                nonlocal created, updated, errors

                for item_data in items_to_import:
                    try:
                        if not isinstance(item_data, dict):
                            raise ValueError("Item deve ser um objeto JSON")

                        # Extrair campos do JSON (ignorar campos adicionais)
                        classname = item_data.get("classname", "").strip()
                        if not classname:
                            raise ValueError("Campo 'classname' é obrigatório")

                        name = item_data.get("name", "").strip()
                        if not name:
                            name = (
                                classname  # Fallback para classname se name não existir
                            )

                        # Preços - usar current_price e current_average
                        current_price = item_data.get("current_price")
                        current_average = item_data.get("current_average")

                        # Quantidade disponível
                        current_quantity = item_data.get("current_quantity", 0)

                        # Converter preços para Decimal
                        try:
                            last_price = (
                                Decimal(str(current_price))
                                if current_price is not None
                                else Decimal("0.00")
                            )
                        except (ValueError, TypeError):
                            last_price = Decimal("0.00")

                        try:
                            average_price = (
                                Decimal(str(current_average))
                                if current_average is not None
                                else Decimal("0.00")
                            )
                        except (ValueError, TypeError):
                            average_price = Decimal("0.00")

                        # Garantir que available_offers seja um inteiro
                        try:
                            available_offers = (
                                int(current_quantity)
                                if current_quantity is not None
                                else 0
                            )
                        except (ValueError, TypeError):
                            available_offers = 0

                        # Gerar URL da imagem usando o mesmo padrão do LegacyPriceService
                        # Ignorar qualquer image_url que venha no JSON
                        image_url = (
                            f"{LegacyPriceService.IMAGE_BASE_URL}/{classname}.png"
                        )

                        # Criar ou atualizar o item
                        item, was_created = Item.objects.update_or_create(
                            slug=classname,
                            defaults={
                                "name": name,
                                "last_price": last_price,
                                "average_price": average_price,
                                "available_offers": available_offers,
                                # image_url sempre gerado a partir do classname
                                "image_url": image_url,
                                "description": item_data.get("description", "").strip()
                                or "",
                                # price_history pode ser uma lista vazia se não existir
                                "price_history": item_data.get("price_history", []),
                            },
                        )

                        if was_created:
                            created += 1
                        else:
                            updated += 1

                    except Exception as e:
                        errors += 1
                        classname_str = (
                            item_data.get("classname", "desconhecido")
                            if isinstance(item_data, dict)
                            else "inválido"
                        )
                        error_msg = f"Erro ao importar '{classname_str}': {str(e)}"
                        error_messages.append(error_msg)

            try:
                _import()

                # Mensagens de sucesso
                if created > 0:
                    messages.success(
                        request, f"{created} item(ns) criado(s) com sucesso."
                    )
                if updated > 0:
                    messages.success(
                        request, f"{updated} item(ns) atualizado(s) com sucesso."
                    )
                if errors > 0:
                    messages.warning(
                        request, f"{errors} item(ns) com erro durante a importação."
                    )
                    for error_msg in error_messages[
                        :10
                    ]:  # Mostrar apenas os 10 primeiros erros
                        messages.error(request, error_msg)
                    if len(error_messages) > 10:
                        messages.info(
                            request, f"... e mais {len(error_messages) - 10} erro(s)."
                        )

                if created == 0 and updated == 0 and errors == 0:
                    messages.info(request, "Nenhum item foi processado.")

                # Redirecionar para a lista de itens
                return redirect("admin:legacy_item_changelist")

            except Exception as e:
                messages.error(request, f"Erro durante a importação: {str(e)}")
                return render(request, "admin/legacy/item/import_json.html", context)

        # GET request - mostrar formulário
        return render(request, "admin/legacy/item/import_json.html", context)

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

    def download_links_view(self, request):
        """
        View para fazer download de um arquivo TXT com links de todos os itens Legacy
        """
        if not request.user.is_staff:
            messages.error(request, "Acesso negado.")
            return redirect("admin:legacy_item_changelist")

        # Buscar todos os itens Legacy que têm slug
        items = (
            Item.objects.filter(slug__isnull=False).exclude(slug="").order_by("slug")
        )

        # Gerar conteúdo do arquivo TXT
        lines = []
        base_url = "https://www.nftmarketplace.com.br/legacy"

        for item in items:
            if item.slug:
                link = f"{base_url}/{item.slug}"
                lines.append(link)

        # Criar resposta HTTP com o arquivo TXT
        content = "\n".join(lines)
        response = HttpResponse(content, content_type="text/plain; charset=utf-8")
        response["Content-Disposition"] = 'attachment; filename="legacy_links.txt"'
        return response
