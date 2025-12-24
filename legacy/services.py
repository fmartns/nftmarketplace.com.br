import requests
import logging
from .utils import convert_item_price
from django.utils.translation import gettext_lazy as _


logger = logging.getLogger(__name__)


class LegacyPriceService:
    """Service para buscar preços da API externa do Habbo"""
    
    DATA_BASE_URL = "https://turbo.securehabbo.com/legacyPrices/optimized"

    IMAGE_BASE_URL = "https://habboapi.site/api/image"

    
    @staticmethod
    def get_item_data(slug: str) -> dict:
        """
        Busca informações de um item na API externa.
        
        Args:
            slug: Slug do item
            
        Returns:
            Dicionário com informações do item
            
        Raises:
            ValueError: Se o slug for inválido ou preço não encontrado
            requests.RequestException: Se houver erro na requisição HTTP
        """
        if not slug:
            raise ValueError(_("Slug parameter is required"))
        
        url = f"{LegacyPriceService.DATA_BASE_URL}/{slug}/br?include_history=true&history_days=30"
        
        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36",
            "Accept": "*/*",
            "Origin": "https://securehabbo.com",
            "Referer": "https://securehabbo.com/",
        }

        image_url = f"{LegacyPriceService.IMAGE_BASE_URL}/{slug}.png"

        try:
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            data = response.json()

            # Extrair preço: data.data.last_price.price

            item_data = data.get("data", {})
            
            if not item_data:
                raise ValueError(_("Item data not found in API response"))

            name = item_data.get("name")
            description = item_data.get("description", "")
            classname = item_data.get("classname", "")
            image_url = item_data.get("image_url", "")
            last_price_raw = item_data.get("last_price", {}).get("price")
            average_price_raw = item_data.get("last_price", {}).get("average")
            quantity = item_data.get("last_price", {}).get("quantity", 0)
            
            if not name or last_price_raw is None:
                raise ValueError(_("Required fields not found in API response"))

            # Converter preços usando a função utilitária e arredondar para 2 casas decimais
            last_price = round(convert_item_price(float(last_price_raw)), 2)
            average_price = round(convert_item_price(float(average_price_raw)), 2) if average_price_raw else last_price

            return {
                "name": name,
                "description": description,
                "slug": classname,
                "image_url": image_url,
                "last_price": last_price,
                "average_price": average_price,
                "available_offers": quantity,
            }

        except requests.exceptions.RequestException as e:
            logger.error(f"Request error: {str(e)}")
            raise ValueError(_("Failed to fetch data from external API"))
        except (ValueError, KeyError) as e:
            logger.error(f"Processing error: {str(e)}")
            raise ValueError(_("Error processing API response"))
    
    @staticmethod
    def get_price(slug: str) -> float:
        """
        Busca apenas o preço de um item na API externa e converte.
        
        Args:
            slug: Slug do item
            
        Returns:
            Preço convertido do item
            
        Raises:
            ValueError: Se o slug for inválido ou preço não encontrado
        """
        item_data = LegacyPriceService.get_item_data(slug)
        return item_data["last_price"]