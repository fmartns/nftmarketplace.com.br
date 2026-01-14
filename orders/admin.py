"""
Admin para o módulo de pedidos
"""

from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils import timezone

from .models import Order, OrderItem, Coupon


@admin.register(Coupon)
class CouponAdmin(admin.ModelAdmin):
    list_display = [
        "code",
        "discount_type",
        "discount_value",
        "is_active",
        "uses_count",
        "max_uses",
        "valid_from",
        "valid_until",
        "created_at",
    ]
    list_filter = [
        "is_active",
        "discount_type",
        "valid_from",
        "valid_until",
    ]
    search_fields = ["code", "description"]
    readonly_fields = ["uses_count", "created_at", "updated_at"]
    date_hierarchy = "created_at"

    fieldsets = (
        (
            "Informações Básicas",
            {
                "fields": ("code", "description", "is_active"),
            },
        ),
        (
            "Desconto",
            {
                "fields": (
                    "discount_type",
                    "discount_value",
                    "min_purchase_amount",
                    "max_discount_amount",
                ),
            },
        ),
        (
            "Uso",
            {
                "fields": (
                    "max_uses",
                    "uses_count",
                    "valid_from",
                    "valid_until",
                ),
            },
        ),
        (
            "Metadados",
            {
                "fields": ("created_by", "created_at", "updated_at"),
                "classes": ("collapse",),
            },
        ),
    )


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ["content_type", "object_id", "unit_price", "total_price"]
    fields = ["item", "quantity", "unit_price", "total_price"]


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = [
        "order_id",
        "user_link",
        "status",
        "subtotal",
        "discount_amount",
        "total",
        "delivered",
        "paid_at",
        "created_at",
    ]
    list_filter = [
        "status",
        "delivered",
        "paid_at",
        "created_at",
    ]
    search_fields = ["order_id", "user__username", "user__email"]
    readonly_fields = [
        "order_id",
        "created_at",
        "updated_at",
    ]
    date_hierarchy = "created_at"
    inlines = [OrderItemInline]

    fieldsets = (
        (
            "Informações Básicas",
            {
                "fields": ("order_id", "user", "status"),
            },
        ),
        (
            "Valores",
            {
                "fields": ("subtotal", "discount_amount", "total", "coupon"),
            },
        ),
        (
            "Pagamento",
            {
                "fields": ("paid_at",),
            },
        ),
        (
            "Entrega",
            {
                "fields": (
                    "delivered",
                    "delivered_at",
                    "delivered_by",
                ),
            },
        ),
        (
            "Observações",
            {
                "fields": ("notes",),
            },
        ),
        (
            "Metadados",
            {
                "fields": ("created_at", "updated_at"),
                "classes": ("collapse",),
            },
        ),
    )

    actions = ["mark_as_delivered", "mark_as_paid"]

    def user_link(self, obj):
        """Link para o usuário"""
        if obj.user:
            url = reverse("admin:accounts_user_change", args=[obj.user.pk])
            return format_html('<a href="{}">{}</a>', url, obj.user.username)
        return "-"

    user_link.short_description = "Usuário"

    def mark_as_delivered(self, request, queryset):
        """Marca pedidos como entregues"""
        count = 0
        for order in queryset:
            if not order.delivered:
                order.mark_as_delivered(request.user)
                count += 1
        self.message_user(
            request,
            f"{count} pedido(s) marcado(s) como entregue(s).",
        )

    mark_as_delivered.short_description = "Marcar como entregue"

    def mark_as_paid(self, request, queryset):
        """Marca pedidos como pagos"""
        count = 0
        for order in queryset.filter(status="pending"):
            order.status = "paid"
            if not order.paid_at:
                order.paid_at = timezone.now()
            order.save()
            count += 1
        self.message_user(
            request,
            f"{count} pedido(s) marcado(s) como pago(s).",
        )

    mark_as_paid.short_description = "Marcar como pago"


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = [
        "order_link",
        "item",
        "quantity",
        "unit_price",
        "total_price",
        "created_at",
    ]
    list_filter = ["created_at"]
    search_fields = ["order__order_id"]
    readonly_fields = [
        "order",
        "content_type",
        "object_id",
        "unit_price",
        "total_price",
        "created_at",
    ]

    def order_link(self, obj):
        """Link para o pedido"""
        if obj.order:
            url = reverse("admin:orders_order_change", args=[obj.order.pk])
            return format_html('<a href="{}">{}</a>', url, obj.order.order_id)
        return "-"

    order_link.short_description = "Pedido"
