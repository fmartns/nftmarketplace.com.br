from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("nft", "0003_add_nftitemaccess"),
    ]

    operations = [
        migrations.AddField(
            model_name="nftitem",
            name="markup_percent",
            field=models.DecimalField(
                blank=True,
                decimal_places=2,
                help_text="Percentual de markup específico para este item (ex.: 30.00 = +30%). Se vazio, usa o global.",
                max_digits=5,
                null=True,
            ),
        ),
        migrations.CreateModel(
            name="PricingConfig",
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
                    "global_markup_percent",
                    models.DecimalField(
                        decimal_places=2,
                        default=30.0,
                        help_text="Markup padrão aplicado em todos os preços quando o item não tem override (ex.: 30.00 = +30%).",
                        max_digits=5,
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={
                "verbose_name": "Configuração de Preço",
                "verbose_name_plural": "Configurações de Preço",
            },
        ),
    ]
