from django.contrib import admin
from .models import AbacatePayPayment, AbacatePayCustomer, AbacatePayBilling


@admin.register(AbacatePayPayment)
class AbacatePayPaymentAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "get_billing_id",
        "order",
        "status",
        "amount",
        "payment_method",
        "created_at",
    ]
    list_filter = ["status", "payment_method", "created_at"]
    search_fields = ["billing__billing_id", "order__order_id", "billing__customer__external_id"]
    readonly_fields = [
        "get_billing_id",
        "payment_url",
        "status",
        "payment_method",
        "created_at",
        "updated_at",
    ]
    
    def get_billing_id(self, obj):
        return obj.billing.billing_id
    get_billing_id.short_description = "Billing ID"


@admin.register(AbacatePayCustomer)
class AbacatePayCustomerAdmin(admin.ModelAdmin):
    list_display = ["id", "external_id", "user", "created_at"]
    search_fields = ["external_id", "user__username", "user__email"]
    readonly_fields = ["external_id", "created_at", "updated_at"]


@admin.register(AbacatePayBilling)
class AbacatePayBillingAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "billing_id",
        "order",
        "status",
        "amount",
        "created_at",
    ]
    list_filter = ["status", "created_at"]
    search_fields = ["billing_id", "order__order_id"]
    readonly_fields = [
        "billing_id",
        "payment_url",
        "status",
        "methods",
        "created_at",
        "updated_at",
    ]
