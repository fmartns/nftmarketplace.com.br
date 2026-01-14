from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("nft", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="nftitem",
            name="seven_day_volume_brl",
            field=models.DecimalField(
                blank=True, decimal_places=2, default=0, max_digits=18, null=True
            ),
        ),
        migrations.AddField(
            model_name="nftitem",
            name="seven_day_sales_count",
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name="nftitem",
            name="seven_day_avg_price_brl",
            field=models.DecimalField(
                blank=True, decimal_places=2, default=0, max_digits=18, null=True
            ),
        ),
        migrations.AddField(
            model_name="nftitem",
            name="seven_day_last_sale_brl",
            field=models.DecimalField(
                blank=True, decimal_places=2, default=0, max_digits=18, null=True
            ),
        ),
        migrations.AddField(
            model_name="nftitem",
            name="seven_day_price_change_pct",
            field=models.DecimalField(
                blank=True, decimal_places=2, default=0, max_digits=7, null=True
            ),
        ),
        migrations.AddField(
            model_name="nftitem",
            name="seven_day_updated_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
