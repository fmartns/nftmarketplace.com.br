from django.contrib import admin
from django.contrib import messages
from django import forms
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
