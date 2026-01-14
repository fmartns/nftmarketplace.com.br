import logging
from typing import ContextManager, cast
from celery import shared_task
from django.utils import timezone
from django.db import transaction
from .models import NFTItem
from .services import fetch_item_from_immutable, ImmutableAPIError
from random import random

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def update_nft_price(self, product_code):
    """
    Task para atualizar o preço de um NFT específico usando a API da Immutable.
    Esta task é chamada individualmente para cada produto durante a rotina da madrugada.
    """
    try:
        logger.info("Iniciando atualização de preço para produto: %s", product_code)

        # Busca o item no banco de dados
        try:
            nft_item = NFTItem.objects.get(product_code=product_code)
        except NFTItem.DoesNotExist:
            logger.warning("Produto %s não encontrado no banco de dados", product_code)
            return {"status": "skipped", "reason": "Produto não encontrado"}

        # Atualiza o timestamp de última atualização
        nft_item.updated_at = timezone.now()
        nft_item.save(update_fields=["updated_at"])

        # Busca dados atualizados da Immutable
        try:
            mapped_data, _ = fetch_item_from_immutable(product_code)
        except ImmutableAPIError as e:
            logger.error("Erro da API Immutable para %s: %s", product_code, e)
            raise Exception(f"Erro da API Immutable: {e}") from e
        except Exception as e:
            logger.error("Erro inesperado ao buscar dados para %s: %s", product_code, e)
            raise Exception(f"Erro inesperado: {e}") from e

        # Atualiza os campos do item com os dados mais recentes
        with cast(ContextManager[None], transaction.atomic()):
            # Atualiza apenas os campos de preço e dados básicos
            update_fields = [
                "last_price_eth",
                "last_price_usd",
                "last_price_brl",
                "name",
                "image_url",
                "blueprint",
                "type",
                "rarity",
                "item_type",
                "item_sub_type",
                "product_type",
                "material",
                "is_crafted_item",
                "is_craft_material",
                "number",
                "updated_at",
            ]

            for field in update_fields:
                if field in mapped_data:
                    setattr(nft_item, field, mapped_data[field])

            nft_item.save(update_fields=update_fields)

        logger.info(
            "Preço atualizado com sucesso para %s: ETH=%s, USD=%s, BRL=%s",
            product_code,
            mapped_data.get("last_price_eth"),
            mapped_data.get("last_price_usd"),
            mapped_data.get("last_price_brl"),
        )

        return {
            "status": "success",
            "product_code": product_code,
            "prices": {
                "eth": str(mapped_data.get("last_price_eth", 0)),
                "usd": str(mapped_data.get("last_price_usd", 0)),
                "brl": str(mapped_data.get("last_price_brl", 0)),
            },
        }

    except Exception as e:
        logger.error("Erro ao atualizar preço para %s: %s", product_code, str(e))

        # Retry da task se ainda tiver tentativas
        if self.request.retries < self.max_retries:
            # Delay exponencial com jitter para evitar sobrecarga
            delay = 60 * (2**self.request.retries) + random() * 10
            logger.info(
                "Tentando novamente atualização de %s em %.1fs (tentativa %d/%d)",
                product_code,
                delay,
                self.request.retries + 1,
                self.max_retries,
            )
            raise self.retry(countdown=delay)

        return {"status": "failed", "product_code": product_code, "error": str(e)}


@shared_task
def update_all_nft_prices_nightly():
    """
    Task principal para atualizar todos os preços dos NFTs durante a madrugada.
    Esta task agenda atualizações individuais para cada produto com intervalo de 6 segundos.
    """
    try:
        logger.info("Iniciando rotina de atualização de preços da madrugada")

        # Busca todos os produtos que têm product_code válido
        nft_items = (
            NFTItem.objects.filter(product_code__isnull=False)
            .exclude(product_code__exact="")
            .values_list("product_code", flat=True)
        )

        total_items = len(nft_items)
        logger.info("Total de produtos para atualizar: %d", total_items)

        if total_items == 0:
            logger.warning("Nenhum produto encontrado para atualização")
            return {"status": "skipped", "reason": "Nenhum produto encontrado"}

        # Agenda atualizações individuais com intervalo de 6 segundos
        scheduled_count = 0
        for i, product_code in enumerate(nft_items):
            # Calcula o delay: 6 segundos * índice do item
            delay_seconds = i * 6

            # Agenda a task individual
            update_nft_price.apply_async(args=[product_code], countdown=delay_seconds)
            scheduled_count += 1

            # Log a cada 50 itens para não sobrecarregar
            if (i + 1) % 50 == 0:
                logger.info("Agendadas %d/%d atualizações", i + 1, total_items)

        logger.info(
            "Rotina da madrugada agendada com sucesso! %d produtos serão atualizados ao longo de %.1f minutos",
            scheduled_count,
            scheduled_count * 6 / 60,
        )

        return {
            "status": "success",
            "total_items": total_items,
            "scheduled_count": scheduled_count,
            "estimated_duration_minutes": scheduled_count * 6 / 60,
        }

    except Exception as e:
        logger.error("Erro na rotina de atualização da madrugada: %s", str(e))
        return {"status": "failed", "error": str(e)}


@shared_task
def cleanup_old_price_updates():
    """
    Task para limpar logs antigos e otimizar o banco de dados.
    Esta task pode ser executada periodicamente para manter o sistema limpo.
    """
    try:
        logger.info("Iniciando limpeza de dados antigos")

        # Aqui você pode adicionar lógica para limpar logs antigos,
        # otimizar índices, etc.

        # Por enquanto, apenas loga que a limpeza foi executada
        logger.info("Limpeza concluída")

        return {"status": "success", "message": "Limpeza concluída"}

    except Exception as e:
        logger.error("Erro na limpeza: %s", str(e))
        return {"status": "failed", "error": str(e)}
