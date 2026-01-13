"""
Documentação das rotas de pedidos (Orders).
"""

from .order import (
    orders_list_schema,
    orders_create_schema,
    orders_detail_schema,
)

__all__ = [
    "orders_list_schema",
    "orders_create_schema",
    "orders_detail_schema",
]
