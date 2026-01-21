from django.core.management.base import BaseCommand

from orders.backup import send_db_backup_email


class Command(BaseCommand):
    help = "Envia backup do banco de dados por email ao administrador."

    def add_arguments(self, parser):
        parser.add_argument(
            "--to",
            dest="to_email",
            default=None,
            help="Email de destino (opcional).",
        )

    def handle(self, *args, **options):
        to_email = options.get("to_email")
        self.stdout.write("Gerando backup e enviando por email...")
        send_db_backup_email(to_email=to_email)
        self.stdout.write(self.style.SUCCESS("Backup enviado com sucesso."))
