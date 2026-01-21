from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("legacy", "0002_alter_item_slug"),
    ]

    operations = [
        migrations.AddField(
            model_name="item",
            name="can_buy_multiple",
            field=models.BooleanField(
                default=False,
                help_text="Permite compra em maior quantidade (legacy itens).",
            ),
        ),
    ]
