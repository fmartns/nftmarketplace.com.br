from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("banners", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="banner",
            name="image_mobile",
            field=models.URLField(
                max_length=500,
                verbose_name="URL da Imagem (Mobile)",
                help_text="URL da imagem do banner para dispositivos móveis (opcional).",
                blank=True,
            ),
        ),
    ]
