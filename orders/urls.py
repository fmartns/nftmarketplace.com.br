"""
URLs para o módulo de pedidos
"""
from django.urls import path

from .views import (
    OrderListCreateView,
    OrderDetailView,
    CouponValidateView,
)

app_name = "orders"

urlpatterns = [
    # Rotas públicas (autenticadas)
    path("orders/", OrderListCreateView.as_view(), name="order-list-create"),
    path("orders/<str:order_id>/", OrderDetailView.as_view(), name="order-detail"),
    path("coupons/validate/", CouponValidateView.as_view(), name="coupon-validate"),
]


