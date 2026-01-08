# Generated manually to fix foreign key constraint pointing to gallery_nftcollection
# This migration fixes the foreign key constraint that was created when gallery app was active
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('nft', '0008_add_collection_to_nftitem'),
    ]

    operations = [
        migrations.RunSQL(
            # Remove a constraint antiga se existir
            sql="""
                ALTER TABLE nft_nftitem 
                DROP CONSTRAINT IF EXISTS nft_nftitem_collection_id_bd18b663_fk_gallery_nftcollection_id;
            """,
            reverse_sql=migrations.RunSQL.noop,
        ),
        migrations.RunSQL(
            # Adiciona a constraint correta apontando para nft_nftcollection
            sql="""
                ALTER TABLE nft_nftitem 
                ADD CONSTRAINT nft_nftitem_collection_id_bd18b663_fk_nft_nftcollection_id
                FOREIGN KEY (collection_id) 
                REFERENCES nft_nftcollection(id) 
                ON DELETE SET NULL 
                DEFERRABLE INITIALLY DEFERRED;
            """,
            reverse_sql="""
                ALTER TABLE nft_nftitem 
                DROP CONSTRAINT IF EXISTS nft_nftitem_collection_id_bd18b663_fk_nft_nftcollection_id;
            """,
        ),
    ]





