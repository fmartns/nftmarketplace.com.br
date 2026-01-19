"""
Comando de management para sincronizar novos NFTs da API securehabbo.com
"""

from django.core.management.base import BaseCommand
from nft.services_securehabbo import sync_new_nfts_from_securehabbo


class Command(BaseCommand):
    help = (
        "Sincroniza novos NFTs da API securehabbo.com que ainda não estão cadastrados"
    )

    def handle(self, *args, **options):
        self.stdout.write("Iniciando sincronização de NFTs da securehabbo...")

        result = sync_new_nfts_from_securehabbo()

        if result["status"] == "success":
            self.stdout.write(
                self.style.SUCCESS(
                    f"\n✅ Sincronização concluída com sucesso!\n"
                    f"   Total de itens na API: {result['total_api']}\n"
                    f"   Novos itens cadastrados: {result['new_items']}\n"
                    f"   Itens atualizados: {result['updated_items']}"
                )
            )

            if result.get("errors"):
                self.stdout.write(
                    self.style.WARNING(
                        f"\n⚠️  {len(result['errors'])} erro(s) durante o processamento:"
                    )
                )
                for error in result["errors"][:10]:  # Mostra apenas os primeiros 10
                    self.stdout.write(f"   - {error}")
                if len(result["errors"]) > 10:
                    self.stdout.write(
                        f"   ... e mais {len(result['errors']) - 10} erro(s)"
                    )
        else:
            self.stdout.write(
                self.style.ERROR(
                    f"\n❌ Erro na sincronização: {result.get('message', 'Erro desconhecido')}"
                )
            )

            if result.get("errors"):
                for error in result["errors"]:
                    self.stdout.write(f"   - {error}")
