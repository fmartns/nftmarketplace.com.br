# Generated manually to fix foreign key constraint pointing to gallery_nftcollection
# This migration fixes the foreign key constraint that was created when gallery app was active
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("nft", "0008_add_collection_to_nftitem"),
    ]

    def _apply_constraint(schema_editor):
        vendor = schema_editor.connection.vendor
        # SQLite não suporta ALTER TABLE DROP/ADD CONSTRAINT; pula em dev/tests locais
        if vendor == "sqlite":
            return

        if vendor == "mysql":
            drop_sql = """
                ALTER TABLE nft_nftitem
                DROP FOREIGN KEY IF EXISTS nft_nftitem_collection_id_bd18b663_fk_gallery_nftcollection_id;
            """
            add_sql = """
                ALTER TABLE nft_nftitem
                ADD CONSTRAINT nft_nftitem_collection_id_bd18b663_fk_nft_nftcollection_id
                FOREIGN KEY (collection_id)
                REFERENCES nft_nftcollection(id)
                ON DELETE SET NULL;
            """
        else:  # assume PostgreSQL or compatible
            drop_sql = """
                ALTER TABLE nft_nftitem
                DROP CONSTRAINT IF EXISTS nft_nftitem_collection_id_bd18b663_fk_gallery_nftcollection_id;
            """
            add_sql = """
                ALTER TABLE nft_nftitem
                ADD CONSTRAINT nft_nftitem_collection_id_bd18b663_fk_nft_nftcollection_id
                FOREIGN KEY (collection_id)
                REFERENCES nft_nftcollection(id)
                ON DELETE SET NULL
                DEFERRABLE INITIALLY DEFERRED;
            """

        schema_editor.execute(drop_sql)
        schema_editor.execute(add_sql)

    def _unapply_constraint(schema_editor):
        vendor = schema_editor.connection.vendor
        if vendor == "sqlite":
            return

        if vendor == "mysql":
            drop_sql = """
                ALTER TABLE nft_nftitem
                DROP FOREIGN KEY IF EXISTS nft_nftitem_collection_id_bd18b663_fk_nft_nftcollection_id;
            """
        else:
            drop_sql = """
                ALTER TABLE nft_nftitem
                DROP CONSTRAINT IF EXISTS nft_nftitem_collection_id_bd18b663_fk_nft_nftcollection_id;
            """
        schema_editor.execute(drop_sql)

    operations = [
        migrations.RunPython(
            code=lambda apps, schema_editor: Migration._apply_constraint(schema_editor),
            reverse_code=lambda apps, schema_editor: Migration._unapply_constraint(
                schema_editor
            ),
        )
    ]
