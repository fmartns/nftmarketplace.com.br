from django.db import models
from django.utils.text import slugify
from django.core.exceptions import ValidationError
from django.conf import settings


class NFTItem(models.Model):
    type = models.CharField(max_length=120)
    blueprint = models.TextField(blank=True)
    image_url = models.URLField(blank=True)
    name = models.CharField(max_length=200, db_index=True)
    name_pt_br = models.CharField(
        "Nome (pt-BR)", max_length=200, blank=True, db_index=True
    )

    source = models.CharField(max_length=80, db_index=True, blank=True)
    is_crafted_item = models.BooleanField(default=False, db_index=True)
    is_craft_material = models.BooleanField(default=False, db_index=True)
    rarity = models.CharField(max_length=80, db_index=True, blank=True)
    item_type = models.CharField(max_length=80, db_index=True, blank=True)
    item_sub_type = models.CharField(max_length=80, db_index=True, blank=True)

    number = models.IntegerField(blank=True, null=True)
    product_code = models.CharField(max_length=120, unique=True, blank=True, null=True)
    product_type = models.CharField(max_length=120, blank=True)
    material = models.CharField(max_length=120, blank=True)

    collection = models.ForeignKey(
        "nft.NftCollection",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="items",
        verbose_name="Coleção",
    )

    last_price_eth = models.DecimalField(
        max_digits=38, decimal_places=18, blank=True, null=True
    )
    last_price_usd = models.DecimalField(
        max_digits=18, decimal_places=2, blank=True, null=True
    )
    last_price_brl = models.DecimalField(
        max_digits=18, decimal_places=2, blank=True, null=True
    )

    # Optional per-item markup percentage (e.g., 30.00 means +30%)
    markup_percent = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        blank=True,
        null=True,
        help_text="Percentual de markup específico para este item (ex.: 30.00 = +30%). Se vazio, usa o global.",
    )

    # 7-day sales metrics
    seven_day_volume_brl = models.DecimalField(
        max_digits=18, decimal_places=2, blank=True, null=True, default=0
    )
    seven_day_sales_count = models.IntegerField(default=0)
    seven_day_avg_price_brl = models.DecimalField(
        max_digits=18, decimal_places=2, blank=True, null=True, default=0
    )
    seven_day_last_sale_brl = models.DecimalField(
        max_digits=18, decimal_places=2, blank=True, null=True, default=0
    )
    seven_day_price_change_pct = models.DecimalField(
        max_digits=7, decimal_places=2, blank=True, null=True, default=0
    )
    seven_day_updated_at = models.DateTimeField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "NFT Item"
        verbose_name_plural = "NFT Items"
        indexes = [
            models.Index(fields=["source"]),
            models.Index(fields=["rarity"]),
            models.Index(fields=["item_type"]),
            models.Index(fields=["item_sub_type"]),
            models.Index(fields=["is_crafted_item"]),
            models.Index(fields=["is_craft_material"]),
            models.Index(fields=["name"]),
            models.Index(fields=["product_code"]),
        ]
        ordering = ["name", "rarity", "item_type", "item_sub_type"]

    def __str__(self) -> str:  # type: ignore[override]
        return str(self.name or (self.product_code or "NFT Item"))


def validate_eth_address(value: str):
    if not isinstance(value, str) or not value.startswith("0x") or len(value) != 42:
        raise ValidationError("Endereço Ethereum inválido. Esperado: 0x + 40 hex.")


class NftCollection(models.Model):
    name = models.CharField(max_length=150, verbose_name="Nome da Coleção")
    slug = models.SlugField(max_length=180, unique=True, blank=True)
    description = models.TextField(blank=True, verbose_name="Descrição")
    address = models.CharField(
        max_length=42,
        unique=True,
        validators=[validate_eth_address],
        verbose_name="Endereço do Contrato",
    )

    profile_image = models.URLField(blank=True, verbose_name="Foto de Perfil")
    cover_image = models.URLField(blank=True, verbose_name="Foto de Capa")

    creator = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="nft_created_collections",
        verbose_name="Criador",
    )
    creator_name = models.CharField(
        max_length=150,
        blank=True,
        verbose_name="Nome do Criador",
        help_text="Nome do criador (caso não seja um usuário registrado)",
    )

    items_count = models.PositiveIntegerField(
        default=0,
        verbose_name="Número de Itens",
        help_text="Total de NFTs nesta coleção",
    )
    owners_count = models.PositiveIntegerField(
        default=0,
        verbose_name="Número de Proprietários",
        help_text="Total de proprietários únicos",
    )
    floor_price = models.DecimalField(
        max_digits=20,
        decimal_places=8,
        default=0,
        verbose_name="Floor Price (ETH)",
        help_text="Menor preço listado na coleção",
    )
    total_volume = models.DecimalField(
        max_digits=30,
        decimal_places=8,
        default=0,
        verbose_name="Volume Total (ETH)",
        help_text="Volume total negociado",
    )

    metadata_api_url = models.URLField(
        blank=True, verbose_name="URL da API de Metadados"
    )

    project_id = models.PositiveBigIntegerField(null=True, blank=True)
    project_owner_address = models.CharField(
        max_length=42, blank=True, validators=[validate_eth_address]
    )

    website_url = models.URLField(blank=True, verbose_name="Site Oficial")
    twitter_url = models.URLField(blank=True, verbose_name="X (Twitter)")
    instagram_url = models.URLField(blank=True, verbose_name="Instagram")
    discord_url = models.URLField(blank=True, verbose_name="Discord")
    telegram_url = models.URLField(blank=True, verbose_name="Telegram")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]
        indexes = [
            models.Index(fields=["slug"]),
            models.Index(fields=["address"]),
        ]

    def save(self, *args, **kwargs):
        # gera slug se vazio; garante unicidade alterando com sufixo numérico se necessário
        if not self.slug:
            base = slugify(self.name)[:170] or "colecao"
            slug = base
            i = 2
            while NftCollection.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base}-{i}"
                i += 1
            self.slug = slug
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.name} ({self.address})"

    @property
    def author(self):
        """Retorna o nome do autor/criador da coleção"""
        if self.creator:
            return self.creator.username
        return self.creator_name or "Desconhecido"

    @property
    def floor_price_eth(self):
        """Retorna o floor price formatado"""
        return f"{self.floor_price:.4f} ETH" if self.floor_price > 0 else "N/A"

    @property
    def total_volume_eth(self):
        """Retorna o volume total formatado"""
        return f"{self.total_volume:.2f} ETH" if self.total_volume > 0 else "N/A"


class NFTItemAccess(models.Model):
    """Tracks user access/pageviews for NFT items."""

    item = models.ForeignKey(NFTItem, on_delete=models.CASCADE, related_name="accesses")
    accessed_at = models.DateTimeField(auto_now_add=True, db_index=True)
    ip_hash = models.CharField(max_length=64, blank=True, default="")
    user_agent_hash = models.CharField(max_length=64, blank=True, default="")

    class Meta:
        indexes = [
            models.Index(fields=["accessed_at"]),
            models.Index(fields=["item", "accessed_at"]),
        ]


class PricingConfig(models.Model):
    """Configuração global de preços (markup padrão)."""

    global_markup_percent = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=30.00,
        help_text="Markup padrão aplicado em todos os preços quando o item não tem override (ex.: 30.00 = +30%).",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Configuração de Preço"
        verbose_name_plural = "Configurações de Preço"

    def __str__(self) -> str:  # type: ignore[override]
        return f"Markup Global: {self.global_markup_percent}%"
