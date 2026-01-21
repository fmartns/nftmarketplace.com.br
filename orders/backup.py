import gzip
import os
import tempfile
import subprocess
from datetime import datetime
from typing import Optional, Tuple

from django.conf import settings
from django.core.mail import EmailMessage
from django.utils import timezone


def _now_stamp() -> str:
    return timezone.now().strftime("%Y%m%d-%H%M%S")


def _get_db_vendor() -> str:
    return settings.DATABASES["default"]["ENGINE"].rsplit(".", 1)[-1]


def _build_postgres_dump(path: str) -> None:
    db = settings.DATABASES["default"]
    cmd = [
        "pg_dump",
        "--format=plain",
        "--no-owner",
        "--no-privileges",
        "--host",
        db.get("HOST") or "localhost",
        "--port",
        str(db.get("PORT") or "5432"),
        "--username",
        db.get("USER") or "",
        db.get("NAME") or "",
    ]
    env = os.environ.copy()
    if db.get("PASSWORD"):
        env["PGPASSWORD"] = db["PASSWORD"]
    with open(path, "wb") as f:
        subprocess.run(cmd, stdout=f, stderr=subprocess.PIPE, check=True, env=env)


def create_db_backup() -> Tuple[str, bytes, str]:
    vendor = _get_db_vendor()
    stamp = _now_stamp()
    if vendor == "sqlite3":
        db_path = settings.DATABASES["default"]["NAME"]
        if not db_path or not os.path.exists(db_path):
            raise FileNotFoundError("SQLite database file not found.")
        with open(db_path, "rb") as f:
            raw = f.read()
        compressed = gzip.compress(raw)
        filename = f"db-backup-sqlite-{stamp}.sqlite3.gz"
        return filename, compressed, "application/gzip"

    if vendor == "postgresql":
        with tempfile.NamedTemporaryFile(suffix=".sql", delete=False) as tmp:
            tmp_path = tmp.name
        try:
            _build_postgres_dump(tmp_path)
            with open(tmp_path, "rb") as f:
                raw = f.read()
            compressed = gzip.compress(raw)
            filename = f"db-backup-postgres-{stamp}.sql.gz"
            return filename, compressed, "application/gzip"
        finally:
            try:
                os.remove(tmp_path)
            except OSError:
                pass

    raise ValueError(f"Unsupported database vendor: {vendor}")


def send_db_backup_email(to_email: Optional[str] = None) -> bool:
    admin_email = (to_email or getattr(settings, "ADMIN_EMAIL", "")).strip() or getattr(
        settings, "DEFAULT_FROM_EMAIL", ""
    )
    if not admin_email:
        raise ValueError("ADMIN_EMAIL ou DEFAULT_FROM_EMAIL não configurado.")

    filename, payload, mime_type = create_db_backup()
    vendor = _get_db_vendor()
    size_mb = round(len(payload) / (1024 * 1024), 2)
    subject = f"Backup diário do banco ({vendor}) - {_now_stamp()}"
    body = (
        "Segue o backup diário do banco de dados em anexo.\n\n"
        f"Vendor: {vendor}\n"
        f"Arquivo: {filename}\n"
        f"Tamanho: {size_mb} MB\n"
        f"Gerado em: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
    )

    email = EmailMessage(
        subject=subject,
        body=body,
        from_email=getattr(settings, "DEFAULT_FROM_EMAIL", None) or admin_email,
        to=[admin_email],
    )
    email.attach(filename, payload, mime_type)
    email.send(fail_silently=False)
    return True
