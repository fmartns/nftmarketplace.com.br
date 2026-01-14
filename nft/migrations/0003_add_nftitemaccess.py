from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("nft", "0002_add_7d_metrics"),
    ]

    operations = [
        migrations.CreateModel(
            name="NFTItemAccess",
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
                ("accessed_at", models.DateTimeField(auto_now_add=True, db_index=True)),
                ("ip_hash", models.CharField(blank=True, default="", max_length=64)),
                (
                    "user_agent_hash",
                    models.CharField(blank=True, default="", max_length=64),
                ),
                (
                    "item",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="accesses",
                        to="nft.nftitem",
                    ),
                ),
            ],
        ),
        migrations.AddIndex(
            model_name="nftitemaccess",
            index=models.Index(fields=["accessed_at"], name="nft_accessed_at_idx"),
        ),
        migrations.AddIndex(
            model_name="nftitemaccess",
            index=models.Index(
                fields=["item", "accessed_at"], name="nft_item_access_idx"
            ),
        ),
    ]
