from django.apps import AppConfig


class NftConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "nft"
    verbose_name = "NFT"

    def ready(self):
        # Importar admin para garantir que os registros sejam feitos
        import nft.admin  # noqa: F401
