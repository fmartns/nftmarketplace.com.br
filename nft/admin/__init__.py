"""
Admin configuration for NFT app
"""

# Importar todos os admins para garantir que sejam registrados
from .items import NFTItemAdmin, PricingConfigAdmin, NFTItemAccessAdmin  # noqa: F401
from .collections import NftCollectionAdmin  # noqa: F401

__all__ = [
    "NFTItemAdmin",
    "PricingConfigAdmin",
    "NFTItemAccessAdmin",
    "NftCollectionAdmin",
]
