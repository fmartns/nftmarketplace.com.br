# Generated manually to add collection field after NftCollection model is created
# Since the column already exists in the database (from previous migration),
# this migration only updates Django's state without modifying the database
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("nft", "0007_nftcollection"),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=[
                # Create column if it doesn't exist (for fresh databases)
                migrations.RunSQL(
                    sql="""
                        DO $$
                        BEGIN
                            IF NOT EXISTS (
                                SELECT 1 FROM information_schema.columns 
                                WHERE table_name='nft_nftitem' AND column_name='collection_id'
                            ) THEN
                                ALTER TABLE nft_nftitem 
                                ADD COLUMN collection_id INTEGER NULL;
                            END IF;
                        END $$;
                    """,
                    reverse_sql="ALTER TABLE nft_nftitem DROP COLUMN IF EXISTS collection_id;",
                ),
            ],
            state_operations=[
                # State operations: update Django's state to reflect the existing column
                migrations.AddField(
                    model_name="nftitem",
                    name="collection",
                    field=models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="items",
                        to="nft.nftcollection",
                        verbose_name="Coleção",
                    ),
                ),
            ],
        ),
    ]
