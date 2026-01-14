from django.contrib import admin, messages
from django.db import transaction
from django.shortcuts import render, redirect
from django.urls import path
from django.utils.dateparse import parse_datetime
from django.http import JsonResponse, HttpResponse
from decimal import Decimal
import json
import requests
import hashlib
from PIL import Image, ImageDraw, ImageFont
import io
import os
from django.conf import settings

from .models import NFTItem, PricingConfig, NFTItemAccess
from nft.models import NftCollection

# Import admin for collections to register it
from .admin.collections import NftCollectionAdmin  # noqa: F401


@admin.register(NFTItem)
class NFTItemAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "name_pt_br",
        "collection",
        "product_code",
        "source",
        "rarity",
        "item_type",
        "item_sub_type",
        "is_crafted_item",
        "is_craft_material",
        "last_price_eth",
        "last_price_usd",
        "last_price_brl",
        "markup_percent",
    )
    # Enable inline editing of the per-item markup in the changelist
    list_editable = ("markup_percent",)
    search_fields = (
        "name",
        "name_pt_br",
        "product_code",
        "material",
        "blueprint",
        "type",
    )
    list_filter = (
        "source",
        "rarity",
        "item_type",
        "item_sub_type",
        "is_crafted_item",
        "is_craft_material",
        "collection",
    )
    readonly_fields = ("created_at", "updated_at")
    change_list_template = "admin/nft/nftitem/change_list.html"

    def get_urls(self):
        urls = super().get_urls()
        custom = [
            path(
                "import-json/",
                self.admin_site.admin_view(self.import_json_view),
                name="nft_nftitem_import_json",
            ),
            path(
                "generate-promo-image/",
                self.admin_site.admin_view(self.generate_promo_image_view),
                name="nft_nftitem_generate_promo_image",
            ),
            path(
                "get-nfts/",
                self.admin_site.admin_view(self.get_nfts_api),
                name="nft_nftitem_get_nfts_api",
            ),
        ]
        return custom + urls

    def import_json_view(self, request):
        context = {**self.admin_site.each_context(request)}
        context.update(
            {
                "opts": self.model._meta,
                "title": "Importar NFTs via JSON",
            }
        )

        if request.method == "POST":
            raw = request.POST.get("payload", "").strip()
            update_existing = request.POST.get("update_existing") == "on"
            try:
                data = json.loads(raw)
            except json.JSONDecodeError as e:
                messages.error(request, f"JSON inválido: {e}")
                return render(request, "admin/nft/nftitem/import_json.html", context)

            # Aceita diferentes formatos:
            # 1. {"success": true, "data": [...]} - formato Habbo API
            # 2. {"nfts": [...]} - formato custom
            # 3. Lista de objetos
            # 4. Objeto único
            entries = []
            if (
                isinstance(data, dict)
                and "data" in data
                and isinstance(data["data"], list)
            ):
                # Formato Habbo API: {"success": true, "data": [...]}
                entries = data["data"]
            elif (
                isinstance(data, dict)
                and "nfts" in data
                and isinstance(data["nfts"], list)
            ):
                entries = data["nfts"]
            elif isinstance(data, list):
                entries = data
            elif isinstance(data, dict):
                entries = [data]
            else:
                messages.error(
                    request,
                    'Estrutura JSON não reconhecida. Informe um objeto, lista, {"data": [...]} ou {"nfts": [...]}.',
                )
                return render(request, "admin/nft/nftitem/import_json.html", context)

            created = 0
            updated = 0
            errors = 0

            @transaction.atomic
            def _import():
                nonlocal created, updated, errors
                for idx, entry in enumerate(entries, start=1):
                    try:
                        if not isinstance(entry, dict):
                            raise ValueError("Entrada inválida; esperado objeto")

                        # Suporta dois formatos:
                        # 1. Formato Django export: {"pk": 123, "fields": {...}}
                        # 2. Formato direto/Habbo API: {"id": "...", "name": "...", ...}
                        fields = (
                            entry.get("fields")
                            if isinstance(entry.get("fields"), dict)
                            else entry
                        )
                        pk = entry.get("pk")
                        if not isinstance(fields, dict):
                            raise ValueError("Entrada inválida; esperado objeto")

                        defaults = {}
                        is_habbo_format = (
                            "id" in fields
                            and "name" in fields
                            and "collection_name" in fields
                        )

                        # Mapeamento para formato Habbo API
                        if is_habbo_format:
                            # Formato Habbo API: mapear campos
                            defaults["product_code"] = fields.get("id", "").strip()
                            defaults["name"] = fields.get("name", "").strip()
                            defaults["image_url"] = fields.get("image_url", "").strip()

                            # Mapear preço (assumindo ETH)
                            if fields.get("current_price") is not None:
                                try:
                                    defaults["last_price_eth"] = Decimal(
                                        str(fields.get("current_price"))
                                    )
                                except (ValueError, TypeError):
                                    pass

                            # Mapear raridade baseado em isRelic e isLtd
                            if fields.get("isRelic"):
                                defaults["rarity"] = "Relic"
                            elif fields.get("isLtd"):
                                defaults["rarity"] = "LTD"
                            else:
                                defaults["rarity"] = "Common"

                            # Definir source como Habbo
                            defaults["source"] = "habbo"

                            # Associar coleção
                            collection_name = fields.get("collection_name", "").strip()
                            if collection_name:
                                # Gerar endereço único baseado no nome da coleção (hash)
                                hash_obj = hashlib.sha256(
                                    collection_name.encode()
                                ).hexdigest()[:40]
                                placeholder_address = f"0x{hash_obj}"

                                collection, _ = NftCollection.objects.get_or_create(
                                    name=collection_name,
                                    defaults={
                                        "address": placeholder_address,
                                        "description": f"Coleção {collection_name}",
                                    },
                                )
                                defaults["collection"] = collection
                        else:
                            # Formato Django export ou formato direto com campos do modelo
                            # Texto/booleanos
                            direct_keys = [
                                "type",
                                "blueprint",
                                "image_url",
                                "name",
                                "name_pt_br",
                                "source",
                                "is_crafted_item",
                                "is_craft_material",
                                "rarity",
                                "item_type",
                                "item_sub_type",
                                "product_code",
                                "product_type",
                                "material",
                            ]
                            for key in direct_keys:
                                if key in fields and fields[key] is not None:
                                    defaults[key] = fields[key]

                            # Inteiros (apenas para formato Django)
                            if fields.get("number") is not None:
                                try:
                                    defaults["number"] = int(fields.get("number"))
                                except Exception:
                                    pass
                            if fields.get("seven_day_sales_count") is not None:
                                try:
                                    defaults["seven_day_sales_count"] = int(
                                        fields.get("seven_day_sales_count")
                                    )
                                except Exception:
                                    pass

                            # Decimais (apenas para formato Django)
                            for src in [
                                "last_price_eth",
                                "last_price_usd",
                                "last_price_brl",
                                "markup_percent",
                                "seven_day_volume_brl",
                                "seven_day_avg_price_brl",
                                "seven_day_last_sale_brl",
                                "seven_day_price_change_pct",
                            ]:
                                if fields.get(src) not in (None, ""):
                                    try:
                                        defaults[src] = Decimal(str(fields.get(src)))
                                    except Exception:
                                        pass

                            # Datetime (apenas para formato Django)
                            if fields.get("seven_day_updated_at"):
                                try:
                                    defaults["seven_day_updated_at"] = parse_datetime(
                                        fields.get("seven_day_updated_at")
                                    )
                                except Exception:
                                    pass

                            # ForeignKey: collection por id (apenas para formato Django)
                            if fields.get("collection"):
                                try:
                                    defaults["collection"] = NftCollection.objects.get(
                                        pk=fields.get("collection")
                                    )
                                except NftCollection.DoesNotExist:
                                    raise ValueError(
                                        f"Coleção com id={fields.get('collection')} não existe"
                                    )

                        product_code = fields.get("product_code")

                        if update_existing:
                            if product_code:
                                obj, created_flag = NFTItem.objects.update_or_create(
                                    product_code=product_code, defaults=defaults
                                )
                                if created_flag:
                                    created += 1
                                else:
                                    updated += 1
                            elif pk:
                                obj = NFTItem.objects.filter(pk=pk).first()
                                if obj:
                                    for k, v in defaults.items():
                                        setattr(obj, k, v)
                                    obj.save()
                                    updated += 1
                                else:
                                    NFTItem.objects.create(id=pk, **defaults)  # type: ignore[arg-type]
                                    created += 1
                            else:
                                NFTItem.objects.create(**defaults)
                                created += 1
                        else:
                            if (
                                product_code
                                and NFTItem.objects.filter(
                                    product_code=product_code
                                ).exists()
                            ):
                                updated += 1  # existente (pulado)
                            elif pk and NFTItem.objects.filter(pk=pk).exists():
                                updated += 1  # existente (pulado)
                            else:
                                if pk:
                                    NFTItem.objects.create(id=pk, **defaults)  # type: ignore[arg-type]
                                else:
                                    NFTItem.objects.create(**defaults)
                                created += 1
                    except Exception:
                        errors += 1

            _import()

            if created:
                messages.success(request, f"{created} NFT(s) criado(s)")
            if updated:
                messages.info(request, f"{updated} NFT(s) atualizado(s)/existentes")
            if errors:
                messages.warning(
                    request,
                    f"{errors} item(ns) com erro; verifique o JSON e coleções referenciadas",
                )

            return redirect("admin:nft_nftitem_changelist")

        return render(request, "admin/nft/nftitem/import_json.html", context)

    def get_nfts_api(self, request):
        """API para buscar NFTs para seleção"""
        from django.db import models

        search = request.GET.get("search", "")
        nfts = NFTItem.objects.all()

        if search:
            nfts = nfts.filter(
                models.Q(name__icontains=search)
                | models.Q(name_pt_br__icontains=search)
                | models.Q(product_code__icontains=search)
            )

        nfts = nfts[:50]  # Limitar resultados

        data = []
        for nft in nfts:
            data.append(
                {
                    "id": nft.id,
                    "name": nft.name,
                    "name_pt_br": nft.name_pt_br,
                    "image_url": nft.image_url,
                    "last_price_brl": (
                        float(nft.last_price_brl) if nft.last_price_brl else 0
                    ),
                    "collection": (
                        nft.collection.name if nft.collection else "Sem coleção"
                    ),
                }
            )

        return JsonResponse({"nfts": data})

    def generate_promo_image_view(self, request):
        """View para gerar imagem promocional"""
        context = {**self.admin_site.each_context(request)}
        context.update(
            {
                "opts": self.model._meta,
                "title": "Gerar Imagem Promocional",
            }
        )

        if request.method == "POST":
            try:
                nft_ids = request.POST.getlist("nft_ids")

                if len(nft_ids) != 3:
                    messages.error(request, "Selecione exatamente 3 NFTs.")
                    return render(
                        request, "admin/nft/nftitem/generate_promo_image.html", context
                    )

                # Buscar os NFTs
                nfts = []
                for nft_id in nft_ids:
                    try:
                        nft = NFTItem.objects.get(id=nft_id)
                        nfts.append(nft)
                    except NFTItem.DoesNotExist:
                        messages.error(request, f"NFT com ID {nft_id} não encontrado.")
                        return render(
                            request,
                            "admin/nft/nftitem/generate_promo_image.html",
                            context,
                        )

                # Gerar a imagem
                image_buffer = self._generate_promo_image(nfts)

                if image_buffer:
                    response = HttpResponse(
                        image_buffer.getvalue(), content_type="image/png"
                    )
                    response["Content-Disposition"] = (
                        'attachment; filename="promo_image.png"'
                    )
                    return response
                else:
                    messages.error(
                        request,
                        "Erro ao gerar a imagem. Verifique se o arquivo 'template.jpeg' está em static/admin/images/",
                    )

            except Exception as e:
                messages.error(request, f"Erro: {str(e)}")

        return render(request, "admin/nft/nftitem/generate_promo_image.html", context)

    def _generate_promo_image(self, nfts):
        """Gera a imagem promocional usando o template original"""
        try:
            # Caminho para a imagem template original
            template_path = os.path.join(
                settings.BASE_DIR, "static", "admin", "images", "template.jpeg"
            )

            if not os.path.exists(template_path):
                print(f"Template original não encontrado: {template_path}")
                print("Coloque o arquivo 'template.jpeg' em static/admin/images/")
                return None

            # Carregar a imagem template original
            template = Image.open(template_path)

            # Converter para RGBA para permitir transparência
            if template.mode != "RGBA":
                template = template.convert("RGBA")

            # Posições dos quadrados coloridos ajustadas para compensar a rotação
            # Baseado na análise da imagem: conteúdo central está rotacionado ~5-10 graus
            # Ajuste fino para compensar o desalinhamento
            nft_positions = [
                (225, 327, 515, 607),  # Quadrado verde (primeiro NFT) - desceu 2px
                (225, 635, 515, 915),  # Quadrado roxo (segundo NFT) - mantido
                (225, 943, 515, 1223),  # Quadrado vermelho (terceiro NFT) - subiu 2px
            ]

            # Processar cada NFT
            for i, nft in enumerate(nfts):
                # Baixar e redimensionar a imagem do NFT
                nft_image = self._download_and_resize_nft_image(
                    nft.image_url, nft_positions[i]
                )

                if nft_image:
                    # Colar a imagem do NFT no template, substituindo o quadrado colorido
                    # Usar a máscara da própria imagem para transparência perfeita
                    template.paste(
                        nft_image, (nft_positions[i][0], nft_positions[i][1]), nft_image
                    )

                    # Adicionar retângulo de preço no canto inferior esquerdo
                    self._add_price_rectangle(
                        template, nft.last_price_brl, nft_positions[i]
                    )

            # Salvar a imagem final
            output = io.BytesIO()
            template.save(output, format="PNG")
            output.seek(0)
            return output

        except Exception as e:
            print(f"Erro ao gerar imagem: {e}")
            return None

    def _round_price_up(self, price):
        """Arredonda o preço para cima terminando em 5 ou 0"""
        try:
            # Converter para float se for string
            if isinstance(price, str):
                price = float(price.replace(",", ".").replace("R$", "").strip())

            # Arredondar para cima para o próximo múltiplo de 5
            rounded = ((int(price) + 4) // 5) * 5

            # Se o preço original já termina em 0 ou 5, manter
            if int(price) % 5 == 0:
                rounded = int(price)

            return f"R$ {rounded}.00"
        except (ValueError, TypeError):
            return "R$ 0.00"

    def _add_price_rectangle(self, template, price, nft_position):
        """Adiciona retângulo de preço com layout específico"""
        try:
            draw = ImageDraw.Draw(template)

            # Arredondar o preço
            rounded_price = self._round_price_up(price)

            # Posição do retângulo (35px à esquerda da página)
            nft_x, nft_y, nft_x2, nft_y2 = nft_position

            # Dimensões do retângulo de preço
            rect_width = 120
            rect_height = 35  # Reduzido para layout horizontal

            # Posição do retângulo (55px da borda esquerda da página - 35px + 20px)
            rect_x = 55  # 35px + 20px para direita
            rect_y = nft_y2 - rect_height - 10  # 10px da borda inferior do NFT

            # Desenhar retângulo com bordas arredondadas
            self._draw_rounded_rectangle(
                draw,
                (rect_x, rect_y, rect_x + rect_width, rect_y + rect_height),
                fill="#20e5f6",
                radius=8,
            )

            # Adicionar texto do preço com layout específico
            try:
                # Tentar carregar fonte Poppins, fallback para fonte padrão
                font_large_size = 20  # Fonte grande para o preço principal
                font_small_size = 12  # Fonte pequena para "R$" e ",00"

                try:
                    # Tentar carregar Poppins do diretório de fontes
                    poppins_path = os.path.join(
                        settings.BASE_DIR,
                        "static",
                        "admin",
                        "fonts",
                        "Poppins-Regular.ttf",
                    )
                    if os.path.exists(poppins_path):
                        font_large = ImageFont.truetype(poppins_path, font_large_size)
                        font_small = ImageFont.truetype(poppins_path, font_small_size)
                    else:
                        raise OSError("Poppins font not found")
                except (OSError, IOError):
                    try:
                        # Fallback para Arial
                        font_large = ImageFont.truetype("arial.ttf", font_large_size)
                        font_small = ImageFont.truetype("arial.ttf", font_small_size)
                    except (OSError, IOError):
                        # Fallback para fonte padrão
                        font_large = ImageFont.load_default()
                        font_small = ImageFont.load_default()

                # Extrair partes do preço (ex: "R$ 125.00" -> "R$", "125", ".00")
                price_parts = rounded_price.split()
                if len(price_parts) >= 2:
                    currency = price_parts[0]  # "R$"
                    price_value = price_parts[1]  # "125.00"

                    # Separar valor e centavos
                    if "." in price_value:
                        main_price, cents = price_value.split(".")
                    else:
                        main_price = price_value
                        cents = "00"

                    # Layout horizontal: R$ (esquerda) | PREÇO (centro) | ,00 (direita voando)
                    # Calcular larguras dos textos
                    currency_bbox = draw.textbbox((0, 0), currency, font=font_small)
                    currency_width = currency_bbox[2] - currency_bbox[0]

                    price_bbox = draw.textbbox((0, 0), main_price, font=font_large)
                    price_width = price_bbox[2] - price_bbox[0]

                    cents_text = f",{cents}"
                    cents_bbox = draw.textbbox((0, 0), cents_text, font=font_small)
                    cents_width = cents_bbox[2] - cents_bbox[0]

                    # Calcular largura total e posição inicial
                    total_width = (
                        currency_width + price_width + cents_width + 15
                    )  # 15px de espaçamento total
                    start_x = rect_x + (rect_width - total_width) // 2

                    # Posições horizontais
                    currency_x = start_x  # "R$" à esquerda
                    price_x = currency_x + currency_width + 5  # Preço no centro
                    cents_x = price_x + price_width + 5  # ",00" à direita

                    # Posição vertical centralizada para todos
                    center_y = rect_y + (rect_height - font_large_size) // 2

                    # Desenhar textos horizontalmente
                    draw.text(
                        (currency_x, center_y),
                        currency,
                        fill="#0d2539",
                        font=font_small,
                    )
                    draw.text(
                        (price_x, center_y), main_price, fill="#0d2539", font=font_large
                    )
                    draw.text(
                        (cents_x, center_y), cents_text, fill="#0d2539", font=font_small
                    )

            except Exception as e:
                print(f"Erro ao adicionar texto do preço: {e}")

        except Exception as e:
            print(f"Erro ao adicionar retângulo de preço: {e}")

    def _draw_rounded_rectangle(self, draw, xy, fill=None, radius=0):
        """Desenha um retângulo com bordas arredondadas"""
        x1, y1, x2, y2 = xy

        # Desenhar retângulo principal
        draw.rectangle([x1 + radius, y1, x2 - radius, y2], fill=fill)
        draw.rectangle([x1, y1 + radius, x2, y2 - radius], fill=fill)

        # Desenhar cantos arredondados
        draw.pieslice([x1, y1, x1 + 2 * radius, y1 + 2 * radius], 180, 270, fill=fill)
        draw.pieslice([x2 - 2 * radius, y1, x2, y1 + 2 * radius], 270, 360, fill=fill)
        draw.pieslice([x1, y2 - 2 * radius, x1 + 2 * radius, y2], 90, 180, fill=fill)
        draw.pieslice([x2 - 2 * radius, y2 - 2 * radius, x2, y2], 0, 90, fill=fill)

    def _create_basic_template(self):
        """Cria um template básico baseado na imagem de referência"""
        # Dimensões baseadas na imagem de referência (800x1200)
        width, height = 800, 1200
        template = Image.new("RGB", (width, height), color="#0a0a0a")
        draw = ImageDraw.Draw(template)

        # Cores baseadas na imagem de referência
        green_color = "#19ff00"  # Verde do primeiro quadrado
        purple_color = "#430064"  # Roxo do segundo quadrado
        red_color = "#EA0804"  # Vermelho do terceiro quadrado
        white_color = "#ffffff"  # Branco para textos
        cyan_color = "#00ffff"  # Ciano para elementos decorativos

        # Desenhar elementos decorativos (circuitos)
        self._draw_circuit_pattern(draw, width, height, cyan_color)

        # Adicionar título
        try:
            title_font = ImageFont.truetype("arial.ttf", 36)
            subtitle_font = ImageFont.truetype("arial.ttf", 18)
        except (OSError, IOError):
            title_font = ImageFont.load_default()
            subtitle_font = ImageFont.load_default()

        # Logo BEA SOUSA VENDAS no canto superior esquerdo
        title_text = "BEA SOUSA"
        draw.textbbox((0, 0), title_text, font=title_font)
        draw.text((50, 50), title_text, fill=white_color, font=title_font)

        # Subtítulo VENDAS
        vendas_text = "VENDAS"
        draw.textbbox((0, 0), vendas_text, font=subtitle_font)
        draw.text((50, 100), vendas_text, fill=white_color, font=subtitle_font)

        # Texto centralizado no topo
        subtitle_text = "+6 ANOS NAS VENDAS ADM DOS GRUPOS +1500 REFS"
        subtitle_bbox = draw.textbbox((0, 0), subtitle_text, font=subtitle_font)
        subtitle_width = subtitle_bbox[2] - subtitle_bbox[0]
        subtitle_x = (width - subtitle_width) // 2
        draw.text((subtitle_x, 50), subtitle_text, fill=cyan_color, font=subtitle_font)

        # Logo NFT central (hexágono brilhante)
        nft_logo_size = 100
        nft_logo_x = (width - nft_logo_size) // 2
        nft_logo_y = 150

        # Desenhar hexágono brilhante para o logo NFT
        hexagon_points = [
            (nft_logo_x + nft_logo_size // 2, nft_logo_y),
            (nft_logo_x + nft_logo_size, nft_logo_y + nft_logo_size // 3),
            (nft_logo_x + nft_logo_size, nft_logo_y + 2 * nft_logo_size // 3),
            (nft_logo_x + nft_logo_size // 2, nft_logo_y + nft_logo_size),
            (nft_logo_x, nft_logo_y + 2 * nft_logo_size // 3),
            (nft_logo_x, nft_logo_y + nft_logo_size // 3),
        ]
        draw.polygon(hexagon_points, fill=cyan_color, outline=white_color, width=3)

        # Texto NFT dentro do hexágono
        nft_text = "NFT"
        nft_text_bbox = draw.textbbox((0, 0), nft_text, font=title_font)
        nft_text_width = nft_text_bbox[2] - nft_text_bbox[0]
        nft_text_height = nft_text_bbox[3] - nft_text_bbox[1]
        nft_text_x = nft_logo_x + (nft_logo_size - nft_text_width) // 2
        nft_text_y = nft_logo_y + (nft_logo_size - nft_text_height) // 2
        draw.text((nft_text_x, nft_text_y), nft_text, fill=white_color, font=title_font)

        # Texto promocional brilhante
        promo_text = "VALORES PARCELADO EM 3X SEM JUROS OU À VISTA COM 10% DE DESCONTO"
        promo_bbox = draw.textbbox((0, 0), promo_text, font=subtitle_font)
        promo_width = promo_bbox[2] - promo_bbox[0]
        promo_x = (width - promo_width) // 2
        draw.text((promo_x, 280), promo_text, fill=white_color, font=subtitle_font)

        # Posições dos quadrados coloridos baseadas na imagem de referência
        square_width = 290
        square_height = 290
        square_x = 255  # Posição X dos quadrados
        square_spacing = 20  # Espaçamento entre quadrados

        squares = [
            # Quadrado verde (primeiro NFT)
            (square_x, 295, square_x + square_width, 295 + square_height),
            # Quadrado roxo (segundo NFT)
            (
                square_x,
                295 + square_height + square_spacing,
                square_x + square_width,
                295 + square_height + square_spacing + square_height,
            ),
            # Quadrado vermelho (terceiro NFT)
            (
                square_x,
                295 + 2 * (square_height + square_spacing),
                square_x + square_width,
                295 + 2 * (square_height + square_spacing) + square_height,
            ),
        ]

        colors = [green_color, purple_color, red_color]

        # Desenhar os quadrados coloridos
        for i, square in enumerate(squares):
            draw.rectangle(square, fill=colors[i], outline=white_color, width=2)

        # Adicionar hexágonos NFT desbotados no fundo
        self._draw_background_nft_hexagons(draw, width, height, cyan_color)

        return template

    def _draw_background_nft_hexagons(self, draw, width, height, color):
        """Desenha hexágonos NFT desbotados no fundo"""
        # Hexágono no canto superior esquerdo (desbotado)
        hex1_size = 60
        hex1_x = 50
        hex1_y = 200

        hex1_points = [
            (hex1_x + hex1_size // 2, hex1_y),
            (hex1_x + hex1_size, hex1_y + hex1_size // 3),
            (hex1_x + hex1_size, hex1_y + 2 * hex1_size // 3),
            (hex1_x + hex1_size // 2, hex1_y + hex1_size),
            (hex1_x, hex1_y + 2 * hex1_size // 3),
            (hex1_x, hex1_y + hex1_size // 3),
        ]
        draw.polygon(hex1_points, outline=color, width=1)

        # Hexágono no canto inferior esquerdo (desbotado)
        hex2_size = 80
        hex2_x = 50
        hex2_y = height - 200

        hex2_points = [
            (hex2_x + hex2_size // 2, hex2_y),
            (hex2_x + hex2_size, hex2_y + hex2_size // 3),
            (hex2_x + hex2_size, hex2_y + 2 * hex2_size // 3),
            (hex2_x + hex2_size // 2, hex2_y + hex2_size),
            (hex2_x, hex2_y + 2 * hex2_size // 3),
            (hex2_x, hex2_y + hex2_size // 3),
        ]
        draw.polygon(hex2_points, outline=color, width=1)

        # Linha de circuito do hexágono inferior
        draw.line(
            [
                hex2_x + hex2_size // 2,
                hex2_y + hex2_size,
                hex2_x + hex2_size // 2,
                hex2_y + hex2_size + 100,
            ],
            fill=color,
            width=2,
        )

    def _draw_circuit_pattern(self, draw, width, height, color):
        """Desenha um padrão de circuito decorativo"""
        import random

        random.seed(42)  # Para resultados consistentes

        # Pontos brilhantes simulando dados em movimento
        for _ in range(50):
            x = random.randint(0, width)
            y = random.randint(0, height)
            size = random.randint(1, 3)
            draw.ellipse([x - size, y - size, x + size, y + size], fill=color)

        # Linhas de circuito
        for _ in range(20):
            x1 = random.randint(0, width)
            y1 = random.randint(0, height)
            x2 = x1 + random.randint(-50, 50)
            y2 = y1 + random.randint(-50, 50)
            draw.line([x1, y1, x2, y2], fill=color, width=1)

    def _download_and_resize_nft_image(self, image_url, target_size):
        """Baixa e redimensiona a imagem do NFT para encaixar perfeitamente"""
        try:
            if not image_url:
                return None

            response = requests.get(image_url, timeout=10)
            response.raise_for_status()

            image = Image.open(io.BytesIO(response.content))

            # Converter para RGBA se necessário
            if image.mode != "RGBA":
                image = image.convert("RGBA")

            # Calcular dimensões do quadrado de destino
            target_width = target_size[2] - target_size[0]
            target_height = target_size[3] - target_size[1]

            # Redimensionar para preencher completamente o quadrado
            # Usar resize em vez de thumbnail para garantir o tamanho exato
            resized = image.resize(
                (target_width, target_height), Image.Resampling.LANCZOS
            )

            return resized

        except Exception as e:
            print(f"Erro ao processar imagem do NFT: {e}")
            return None


@admin.register(PricingConfig)
class PricingConfigAdmin(admin.ModelAdmin):
    list_display = ("global_markup_percent", "updated_at")
    readonly_fields = ("created_at", "updated_at")


@admin.register(NFTItemAccess)
class NFTItemAccessAdmin(admin.ModelAdmin):
    list_display = ("item", "accessed_at")
    list_filter = ("accessed_at",)
    search_fields = ("item__name", "item__product_code")
