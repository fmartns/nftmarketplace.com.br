# Generated manually

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("legacy", "0002_item_description_item_image_url"),
    ]

    operations = [
        migrations.AddField(
            model_name="item",
            name="price_history",
            field=models.JSONField(blank=True, default=list),
        ),
    ]




