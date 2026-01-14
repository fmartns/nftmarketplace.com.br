from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="NFTItem",
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
                ("type", models.CharField(max_length=120)),
                ("blueprint", models.TextField(blank=True)),
                ("image_url", models.URLField(blank=True)),
                ("name", models.CharField(db_index=True, max_length=200)),
                ("source", models.CharField(blank=True, db_index=True, max_length=80)),
                ("is_crafted_item", models.BooleanField(db_index=True, default=False)),
                (
                    "is_craft_material",
                    models.BooleanField(db_index=True, default=False),
                ),
                ("rarity", models.CharField(blank=True, db_index=True, max_length=80)),
                (
                    "item_type",
                    models.CharField(blank=True, db_index=True, max_length=80),
                ),
                (
                    "item_sub_type",
                    models.CharField(blank=True, db_index=True, max_length=80),
                ),
                ("number", models.IntegerField(blank=True, null=True)),
                (
                    "product_code",
                    models.CharField(
                        blank=True, max_length=120, null=True, unique=True
                    ),
                ),
                ("product_type", models.CharField(blank=True, max_length=120)),
                ("material", models.CharField(blank=True, max_length=120)),
                (
                    "last_price_eth",
                    models.DecimalField(
                        blank=True, decimal_places=18, max_digits=38, null=True
                    ),
                ),
                (
                    "last_price_usd",
                    models.DecimalField(
                        blank=True, decimal_places=2, max_digits=18, null=True
                    ),
                ),
                (
                    "last_price_brl",
                    models.DecimalField(
                        blank=True, decimal_places=2, max_digits=18, null=True
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={
                "ordering": ["name", "rarity", "item_type", "item_sub_type"],
            },
        ),
        migrations.AddIndex(
            model_name="nftitem",
            index=models.Index(fields=["source"], name="nft_item_source_idx"),
        ),
        migrations.AddIndex(
            model_name="nftitem",
            index=models.Index(fields=["rarity"], name="nft_item_rarity_idx"),
        ),
        migrations.AddIndex(
            model_name="nftitem",
            index=models.Index(fields=["item_type"], name="nft_item_item_type_idx"),
        ),
        migrations.AddIndex(
            model_name="nftitem",
            index=models.Index(
                fields=["item_sub_type"], name="nft_item_item_sub_type_idx"
            ),
        ),
        migrations.AddIndex(
            model_name="nftitem",
            index=models.Index(
                fields=["is_crafted_item"], name="nft_item_is_crafted_idx"
            ),
        ),
        migrations.AddIndex(
            model_name="nftitem",
            index=models.Index(
                fields=["is_craft_material"], name="nft_item_is_material_idx"
            ),
        ),
        migrations.AddIndex(
            model_name="nftitem",
            index=models.Index(fields=["name"], name="nft_item_name_idx"),
        ),
        migrations.AddIndex(
            model_name="nftitem",
            index=models.Index(
                fields=["product_code"], name="nft_item_product_code_idx"
            ),
        ),
    ]
