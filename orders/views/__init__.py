"""
Views para o módulo de pedidos
"""

from .order import OrderListCreateView, OrderDetailView
from .coupon import CouponListView, CouponValidateView
from .admin import OrderMarkDeliveredView, OrderListAdminView, CouponAdminView

__all__ = [
    "OrderListCreateView",
    "OrderDetailView",
    "CouponListView",
    "CouponValidateView",
    "OrderMarkDeliveredView",
    "OrderListAdminView",
    "CouponAdminView",
]





