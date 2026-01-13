"""
Documentação modularizada das rotas do módulo payments.
"""

from .billing import (
    billing_create_schema,
    billing_list_schema,
    billing_status_schema,
    billing_pix_qrcode_schema,
    billing_pix_check_schema,
    billing_simulate_schema,
)
from .customer import (
    customer_create_schema,
    customer_list_schema,
)

__all__ = [
    # Billing schemas
    "billing_create_schema",
    "billing_list_schema",
    "billing_status_schema",
    "billing_pix_qrcode_schema",
    "billing_pix_check_schema",
    "billing_simulate_schema",
    # Customer schemas
    "customer_create_schema",
    "customer_list_schema",
]
