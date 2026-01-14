# Generated manually - Initial migration for orders app
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
from decimal import Decimal
import django.core.validators


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("contenttypes", "0002_remove_content_type_name"),
    ]

    operations = [
        migrations.CreateModel(
            name="Coupon",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "code",
                    models.CharField(
                        db_index=True,
                        help_text="Código do cupom (ex: DESCONTO20)",
                        max_length=50,
                        unique=True,
                    ),
                ),
                (
                    "description",
                    models.TextField(blank=True, help_text="Descrição do cupom"),
                ),
                (
                    "discount_type",
                    models.CharField(
                        choices=[("percentage", "Percentual"), ("fixed", "Valor fixo")],
                        default="percentage",
                        help_text="Tipo de desconto",
                        max_length=20,
                    ),
                ),
                (
                    "discount_value",
                    models.DecimalField(
                        decimal_places=2,
                        help_text="Valor do desconto (percentual ou valor fixo)",
                        max_digits=10,
                        validators=[
                            django.core.validators.MinValueValidator(Decimal("0.01"))
                        ],
                    ),
                ),
                (
                    "min_purchase_amount",
                    models.DecimalField(
                        decimal_places=2,
                        default=Decimal("0.00"),
                        help_text="Valor mínimo de compra para usar o cupom",
                        max_digits=10,
                        validators=[
                            django.core.validators.MinValueValidator(Decimal("0.00"))
                        ],
                    ),
                ),
                (
                    "max_discount_amount",
                    models.DecimalField(
                        blank=True,
                        decimal_places=2,
                        help_text="Valor máximo de desconto (apenas para percentual, opcional)",
                        max_digits=10,
                        null=True,
                        validators=[
                            django.core.validators.MinValueValidator(Decimal("0.01"))
                        ],
                    ),
                ),
                (
                    "max_uses",
                    models.IntegerField(
                        blank=True,
                        help_text="Número máximo de usos (null = ilimitado)",
                        null=True,
                        validators=[django.core.validators.MinValueValidator(1)],
                    ),
                ),
                (
                    "uses_count",
                    models.IntegerField(
                        default=0, help_text="Número de vezes que o cupom foi usado"
                    ),
                ),
                (
                    "is_active",
                    models.BooleanField(default=True, help_text="Se o cupom está ativo"),
                ),
                (
                    "valid_from",
                    models.DateTimeField(help_text="Data/hora de início da validade"),
                ),
                (
                    "valid_until",
                    models.DateTimeField(help_text="Data/hora de fim da validade"),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "created_by",
                    models.ForeignKey(
                        help_text="Usuário que criou o cupom",
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="created_coupons",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "verbose_name": "Cupom",
                "verbose_name_plural": "Cupons",
                "ordering": ["-created_at"],
            },
        ),
        migrations.CreateModel(
            name="Order",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "order_id",
                    models.CharField(
                        db_index=True,
                        help_text="ID único do pedido (ex: #KFNSFG)",
                        max_length=10,
                        unique=True,
                    ),
                ),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("pending", "Pendente"),
                            ("paid", "Pago"),
                            ("processing", "Processando"),
                            ("delivered", "Entregue"),
                            ("cancelled", "Cancelado"),
                            ("refunded", "Reembolsado"),
                        ],
                        db_index=True,
                        default="pending",
                        help_text="Status do pedido",
                        max_length=20,
                    ),
                ),
                (
                    "subtotal",
                    models.DecimalField(
                        decimal_places=2,
                        help_text="Subtotal dos itens (sem desconto)",
                        max_digits=10,
                        validators=[
                            django.core.validators.MinValueValidator(Decimal("0.01"))
                        ],
                    ),
                ),
                (
                    "discount_amount",
                    models.DecimalField(
                        decimal_places=2,
                        default=Decimal("0.00"),
                        help_text="Valor do desconto aplicado",
                        max_digits=10,
                        validators=[
                            django.core.validators.MinValueValidator(Decimal("0.00"))
                        ],
                    ),
                ),
                (
                    "total",
                    models.DecimalField(
                        decimal_places=2,
                        help_text="Valor total do pedido (subtotal - desconto)",
                        max_digits=10,
                        validators=[
                            django.core.validators.MinValueValidator(Decimal("0.01"))
                        ],
                    ),
                ),
                (
                    "paid_at",
                    models.DateTimeField(
                        blank=True,
                        help_text="Data/hora em que o pedido foi pago",
                        null=True,
                    ),
                ),
                (
                    "delivered",
                    models.BooleanField(
                        db_index=True,
                        default=False,
                        help_text="Se o pedido foi entregue pelo administrador",
                    ),
                ),
                (
                    "delivered_at",
                    models.DateTimeField(
                        blank=True,
                        help_text="Data/hora em que o pedido foi entregue",
                        null=True,
                    ),
                ),
                (
                    "notes",
                    models.TextField(blank=True, help_text="Observações do pedido"),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True, db_index=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "coupon",
                    models.ForeignKey(
                        blank=True,
                        help_text="Cupom aplicado (se houver)",
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="orders",
                        to="orders.coupon",
                    ),
                ),
                (
                    "delivered_by",
                    models.ForeignKey(
                        blank=True,
                        help_text="Administrador que entregou o pedido",
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="delivered_orders",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "user",
                    models.ForeignKey(
                        help_text="Usuário que fez o pedido",
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="orders",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "verbose_name": "Pedido",
                "verbose_name_plural": "Pedidos",
                "ordering": ["-created_at"],
            },
        ),
        migrations.CreateModel(
            name="OrderItem",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "object_id",
                    models.PositiveIntegerField(help_text="ID do item"),
                ),
                (
                    "quantity",
                    models.IntegerField(
                        default=1,
                        help_text="Quantidade do item",
                        validators=[django.core.validators.MinValueValidator(1)],
                    ),
                ),
                (
                    "unit_price",
                    models.DecimalField(
                        decimal_places=2,
                        help_text="Preço unitário do item no momento da compra",
                        max_digits=10,
                        validators=[
                            django.core.validators.MinValueValidator(Decimal("0.01"))
                        ],
                    ),
                ),
                (
                    "total_price",
                    models.DecimalField(
                        decimal_places=2,
                        help_text="Preço total (unitário * quantidade)",
                        max_digits=10,
                        validators=[
                            django.core.validators.MinValueValidator(Decimal("0.01"))
                        ],
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "content_type",
                    models.ForeignKey(
                        help_text="Tipo do item (legacy.Item ou nft.NFTItem)",
                        on_delete=django.db.models.deletion.PROTECT,
                        to="contenttypes.contenttype",
                    ),
                ),
                (
                    "order",
                    models.ForeignKey(
                        help_text="Pedido ao qual este item pertence",
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="items",
                        to="orders.order",
                    ),
                ),
            ],
            options={
                "verbose_name": "Item do Pedido",
                "verbose_name_plural": "Itens do Pedido",
                "ordering": ["order", "created_at"],
            },
        ),
        migrations.AddIndex(
            model_name="order",
            index=models.Index(fields=["order_id"], name="orders_orde_order_i_idx"),
        ),
        migrations.AddIndex(
            model_name="order",
            index=models.Index(fields=["status"], name="orders_orde_status_idx"),
        ),
        migrations.AddIndex(
            model_name="order",
            index=models.Index(fields=["user"], name="orders_orde_user_id_idx"),
        ),
        migrations.AddIndex(
            model_name="order",
            index=models.Index(fields=["delivered"], name="orders_orde_deliver_idx"),
        ),
        migrations.AddIndex(
            model_name="orderitem",
            index=models.Index(fields=["order"], name="orders_orde_order_i_idx"),
        ),
        migrations.AddIndex(
            model_name="orderitem",
            index=models.Index(
                fields=["content_type", "object_id"], name="orders_orde_content_idx"
            ),
        ),
        migrations.AddIndex(
            model_name="coupon",
            index=models.Index(fields=["code"], name="orders_coup_code_idx"),
        ),
        migrations.AddIndex(
            model_name="coupon",
            index=models.Index(fields=["is_active"], name="orders_coup_is_acti_idx"),
        ),
    ]
