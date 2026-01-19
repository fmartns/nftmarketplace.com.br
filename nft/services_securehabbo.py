"""
Serviço para buscar NFTs da API securehabbo.com
"""

import logging
import requests
import hashlib
from decimal import Decimal
from typing import List, Dict, Any, Optional
from django.db import transaction
from .models import NFTItem, NftCollection
from .services import get_current_rates

logger = logging.getLogger(__name__)

SECUREHABBO_API_URL = "https://turbo.securehabbo.com/market/items"

SECUREHABBO_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36",
    "Accept": "*/*",
    "Origin": "https://securehabbo.com",
    "Referer": "https://securehabbo.com/",
}


def fetch_securehabbo_items() -> List[Dict[str, Any]]:
    """
    Busca todos os itens da API securehabbo.com/market/items

    Returns:
        Lista de dicionários com dados dos itens

    Raises:
        requests.RequestException: Se houver erro na requisição
    """
    try:
        response = requests.get(
            SECUREHABBO_API_URL, headers=SECUREHABBO_HEADERS, timeout=30
        )
        response.raise_for_status()
        data = response.json()

        if not data.get("success"):
            logger.warning("API retornou success=false")
            return []

        items = data.get("data", [])
        logger.info(f"Buscados {len(items)} itens da API securehabbo")
        return items

    except requests.exceptions.RequestException as e:
        logger.error(f"Erro ao buscar itens da API securehabbo: {e}")
        raise
    except (KeyError, ValueError) as e:
        logger.error(f"Erro ao processar resposta da API: {e}")
        raise


def get_or_create_collection(collection_name: str) -> Optional[NftCollection]:
    """
    Obtém ou cria uma coleção baseada no nome

    Args:
        collection_name: Nome da coleção

    Returns:
        Instância de NftCollection ou None se collection_name estiver vazio
    """
    if not collection_name:
        return None

    # Gerar endereço único baseado no nome da coleção (hash)
    hash_obj = hashlib.sha256(collection_name.encode()).hexdigest()[:40]
    placeholder_address = f"0x{hash_obj}"

    collection, created = NftCollection.objects.get_or_create(
        name=collection_name,
        defaults={
            "address": placeholder_address,
            "description": f"Coleção {collection_name}",
        },
    )

    if created:
        logger.info(f"Coleção criada: {collection_name}")

    return collection


def convert_eth_to_brl(eth_price: Decimal) -> Decimal:
    """
    Converte preço de ETH para BRL

    Args:
        eth_price: Preço em ETH

    Returns:
        Preço em BRL
    """
    try:
        eth_usd, usd_brl = get_current_rates()
        if eth_usd and usd_brl:
            usd_price = eth_price * eth_usd
            brl_price = usd_price * usd_brl
            return Decimal(str(brl_price)).quantize(Decimal("0.01"))
    except Exception as e:
        logger.warning(f"Erro ao converter preço ETH->BRL: {e}")

    return Decimal("0.00")


def map_securehabbo_item_to_nft(item_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Mapeia dados da API securehabbo para formato NFTItem

    Args:
        item_data: Dados do item da API

    Returns:
        Dicionário com campos para criar/atualizar NFTItem ou None se dados inválidos
    """
    product_code = item_data.get("id", "").strip()
    if not product_code:
        return None

    # Converter preço de ETH para BRL
    current_price_eth = Decimal(str(item_data.get("current_price", 0)))
    current_price_brl = convert_eth_to_brl(current_price_eth)

    # Mapear raridade
    rarity = "Common"
    if item_data.get("isRelic"):
        rarity = "Relic"
    elif item_data.get("isLtd"):
        rarity = "LTD"

    # Determinar item_type baseado na collection_name
    collection_name = item_data.get("collection_name", "").strip()
    item_type = ""
    if "Clothes" in collection_name:
        item_type = "clothes"
    elif "Furni" in collection_name:
        item_type = "furni"
    elif "Pets" in collection_name:
        item_type = "pets"
    elif "Tokens" in collection_name:
        item_type = "tokens"
    elif "Add Ons" in collection_name:
        item_type = "addons"

    # Verificar se é item craftado (baseado na URL da imagem)
    image_url = item_data.get("image_url", "")
    is_crafted = "/crafted/" in image_url if image_url else False

    mapped = {
        "product_code": product_code,
        "name": item_data.get("name", "").strip(),
        "image_url": image_url,
        "last_price_eth": current_price_eth,
        "last_price_brl": current_price_brl,
        "rarity": rarity,
        "item_type": item_type,
        "source": "habbo",
        "is_crafted_item": is_crafted,
        "is_craft_material": False,
    }

    return mapped


@transaction.atomic
def sync_new_nfts_from_securehabbo() -> Dict[str, Any]:
    """
    Sincroniza novos NFTs da API securehabbo que ainda não estão cadastrados

    Returns:
        Dicionário com estatísticas da sincronização
    """
    try:
        # Buscar itens da API
        api_items = fetch_securehabbo_items()

        if not api_items:
            return {
                "status": "error",
                "message": "Nenhum item retornado da API",
                "total_api": 0,
                "new_items": 0,
                "updated_items": 0,
                "errors": [],
            }

        # Buscar product_codes já cadastrados
        existing_codes = set(
            NFTItem.objects.filter(product_code__isnull=False)
            .exclude(product_code__exact="")
            .values_list("product_code", flat=True)
        )

        new_items_count = 0
        updated_items_count = 0
        errors = []

        # Processar cada item da API
        for item_data in api_items:
            try:
                product_code = item_data.get("id", "").strip()
                if not product_code:
                    continue

                # Mapear dados
                mapped_data = map_securehabbo_item_to_nft(item_data)
                if not mapped_data:
                    continue

                # Verificar se já existe
                exists = product_code in existing_codes

                # Obter ou criar coleção
                collection_name = item_data.get("collection_name", "").strip()
                collection = None
                if collection_name:
                    collection = get_or_create_collection(collection_name)

                if exists:
                    # Atualizar item existente
                    nft_item = NFTItem.objects.get(product_code=product_code)
                    for key, value in mapped_data.items():
                        if key != "product_code":  # Não atualizar product_code
                            setattr(nft_item, key, value)
                    if collection:
                        nft_item.collection = collection
                    nft_item.save()
                    updated_items_count += 1
                else:
                    # Criar novo item
                    mapped_data["collection"] = collection
                    NFTItem.objects.create(**mapped_data)
                    new_items_count += 1
                    existing_codes.add(
                        product_code
                    )  # Adicionar ao set para evitar duplicatas

            except Exception as e:
                error_msg = (
                    f"Erro ao processar item {item_data.get('id', 'unknown')}: {str(e)}"
                )
                logger.error(error_msg, exc_info=True)
                errors.append(error_msg)
                continue

        result = {
            "status": "success",
            "total_api": len(api_items),
            "new_items": new_items_count,
            "updated_items": updated_items_count,
            "errors": errors,
            "message": f"Sincronização concluída: {new_items_count} novos, {updated_items_count} atualizados",
        }

        logger.info(
            f"Sincronização securehabbo concluída: {new_items_count} novos, "
            f"{updated_items_count} atualizados de {len(api_items)} itens da API"
        )

        return result

    except Exception as e:
        logger.error(f"Erro na sincronização securehabbo: {e}", exc_info=True)
        return {
            "status": "error",
            "message": str(e),
            "total_api": 0,
            "new_items": 0,
            "updated_items": 0,
            "errors": [str(e)],
        }
