"""
URLs para o módulo de pagamentos AbacatePay
"""

from django.urls import path
from .views import (
    BillingCreateView,
    BillingListView,
    BillingStatusView,
    BillingPixQRCodeView,
    BillingPixCheckView,
    BillingSimulateView,
    CustomerCreateView,
    CustomerListView,
)
from .views.webhook import AbacatePayWebhookView

app_name = "payments"

urlpatterns = [
    # Clientes
    path("customers/", CustomerCreateView.as_view(), name="customer-create"),
    path("customers/list/", CustomerListView.as_view(), name="customer-list"),
    # Cobranças
    path("billing/create/", BillingCreateView.as_view(), name="billing-create"),
    path("billing/list/", BillingListView.as_view(), name="billing-list"),
    path(
        "billing/<str:billing_id>/status/",
        BillingStatusView.as_view(),
        name="billing-status",
    ),
    path(
        "billing/<str:billing_id>/pix/qrcode/",
        BillingPixQRCodeView.as_view(),
        name="billing-pix-qrcode",
    ),
    path(
        "billing/<str:billing_id>/pix/check/",
        BillingPixCheckView.as_view(),
        name="billing-pix-check",
    ),
    path(
        "billing/<str:billing_id>/simulate/",
        BillingSimulateView.as_view(),
        name="billing-simulate",
    ),
    # Webhook
    # URL conforme documentação: https://docs.abacatepay.com/pages/webhooks
    # A URL será chamada como: https://api.nftmarketplace.com.br/payments/webhook/abacatepay?webhookSecret=seu_secret
    path("webhook/abacatepay", AbacatePayWebhookView, name="webhook"),
]
