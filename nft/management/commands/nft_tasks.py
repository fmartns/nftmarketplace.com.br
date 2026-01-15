from django.core.management.base import BaseCommand
from nft.tasks import (
    update_all_nft_prices_nightly,
    update_all_nft_prices_sequential,
    update_nft_price,
)
from nft.models import NFTItem


class Command(BaseCommand):
    help = "Gerencia as tasks de atualização de preços dos NFTs"

    def add_arguments(self, parser):
        parser.add_argument(
            "action",
            choices=["status", "run-now", "run-sequential", "run-single", "test"],
            help="Ação a ser executada",
        )
        parser.add_argument(
            "--product-code",
            type=str,
            help="Código do produto para atualização individual",
        )

    def handle(self, *args, **options):
        action = options["action"]

        if action == "status":
            self.show_status()
        elif action == "run-now":
            self.run_now()
        elif action == "run-sequential":
            self.run_sequential()
        elif action == "run-single":
            product_code = options.get("product_code")
            if not product_code:
                self.stdout.write(
                    self.style.ERROR(
                        "Erro: --product-code é obrigatório para run-single"
                    )
                )
                return
            self.run_single(product_code)
        elif action == "test":
            self.test_system()

    def show_status(self):
        """Mostra o status do sistema."""
        self.stdout.write(
            self.style.SUCCESS("Status do Sistema de Atualização de Preços NFT")
        )
        self.stdout.write("=" * 50)

        total_products = NFTItem.objects.count()
        products_with_code = (
            NFTItem.objects.filter(product_code__isnull=False)
            .exclude(product_code__exact="")
            .count()
        )

        self.stdout.write(f"Total de produtos no banco: {total_products}")
        self.stdout.write(f"Produtos com product_code válido: {products_with_code}")

        # Mostra alguns produtos de exemplo
        self.stdout.write("\nExemplos de produtos:")
        sample_products = (
            NFTItem.objects.filter(product_code__isnull=False)
            .exclude(product_code__exact="")
            .values_list("product_code", "name", "last_price_brl")[:5]
        )

        for product_code, name, price in sample_products:
            price_str = f"R$ {price}" if price else "N/A"
            self.stdout.write(f"  • {product_code}: {name} - {price_str}")

        self.stdout.write("\nPróxima execução agendada: Todo dia às 3h00")
        self.stdout.write("Intervalo entre atualizações: 3.5 segundos por produto")

        if products_with_code > 0:
            estimated_duration = products_with_code * 3.5 / 60
            self.stdout.write(
                f"Duração estimada da rotina: {estimated_duration:.1f} minutos"
            )

    def run_now(self):
        """Executa a rotina de atualização imediatamente (agenda todas as tasks)."""
        self.stdout.write("Executando rotina de atualização de preços (agendada)...")

        try:
            result = update_all_nft_prices_nightly.delay()
            self.stdout.write(
                self.style.SUCCESS(f"Task agendada com sucesso! ID: {result.id}")
            )
            self.stdout.write("A rotina está sendo executada em background.")
            self.stdout.write(
                "Use 'celery -A core worker --loglevel=info' para ver os logs."
            )

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Erro ao executar a rotina: {e}"))

    def run_sequential(self):
        """Executa a rotina de atualização sequencialmente (um item a cada 3.5s)."""
        self.stdout.write(
            "Executando atualização sequencial de preços (um item a cada 3.5s)..."
        )

        try:
            result = update_all_nft_prices_sequential.delay()
            self.stdout.write(
                self.style.SUCCESS(f"Task sequencial iniciada! ID: {result.id}")
            )
            self.stdout.write(
                "A rotina está processando os itens sequencialmente em background."
            )
            self.stdout.write(
                "Use 'celery -A core worker --loglevel=info' para ver os logs."
            )

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Erro ao executar a rotina: {e}"))

    def run_single(self, product_code):
        """Atualiza um produto específico."""
        self.stdout.write(f"Atualizando produto específico: {product_code}")

        try:
            result = update_nft_price.delay(product_code)
            self.stdout.write(
                self.style.SUCCESS(f"Task agendada com sucesso! ID: {result.id}")
            )
            self.stdout.write(
                f"O produto {product_code} está sendo atualizado em background."
            )

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Erro ao atualizar o produto: {e}"))

    def test_system(self):
        """Testa o sistema com um produto de exemplo."""
        self.stdout.write("Testando sistema de atualização...")

        # Busca um produto para teste
        test_product = (
            NFTItem.objects.filter(product_code__isnull=False)
            .exclude(product_code__exact="")
            .first()
        )

        if not test_product:
            self.stdout.write(
                self.style.WARNING("Nenhum produto encontrado para teste")
            )
            return

        self.stdout.write(f"Produto de teste: {test_product.product_code}")
        self.stdout.write(f"Preço atual: R$ {test_product.last_price_brl or 'N/A'}")

        try:
            result = update_nft_price.delay(test_product.product_code)
            self.stdout.write(
                self.style.SUCCESS(f"Teste agendado com sucesso! ID: {result.id}")
            )
            self.stdout.write("Verifique os logs do Celery para acompanhar o teste.")

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Erro no teste: {e}"))
