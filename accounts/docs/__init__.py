"""
Documentação modularizada das rotas do módulo accounts.

Este módulo contém todos os schemas de documentação OpenAPI organizados por funcionalidade.
"""

from .user import (
    user_profile_get_schema,
    user_profile_update_schema,
    user_profile_partial_update_schema,
)
from .habbo import (
    habbo_verify_schema,
    habbo_confirm_schema,
    habbo_unlink_schema,
    habbo_validation_status_schema,
    habbo_validation_history_schema,
)
from .metamask import (
    metamask_auth_schema,
    metamask_register_schema,
    generate_auth_message_schema,
)

__all__ = [
    # User schemas
    "user_profile_get_schema",
    "user_profile_update_schema",
    "user_profile_partial_update_schema",
    # Habbo schemas
    "habbo_verify_schema",
    "habbo_confirm_schema",
    "habbo_unlink_schema",
    "habbo_validation_status_schema",
    "habbo_validation_history_schema",
    # MetaMask schemas
    "metamask_auth_schema",
    "metamask_register_schema",
    "generate_auth_message_schema",
]
