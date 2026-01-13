"""
Views principais - Importa todas as views dos módulos organizados
"""

# Importa todas as views dos módulos organizados
from .views import (
    MetaMaskAuthView,
    MetaMaskRegisterView,
    GenerateAuthMessageView,
    UserProfileView,
    HabboValidationView,
    HabboConfirmView,
    HabboUnlinkView,
    HabboValidationStatusView,
    HabboValidationHistoryView,
)

__all__ = [
    "MetaMaskAuthView",
    "MetaMaskRegisterView",
    "GenerateAuthMessageView",
    "UserProfileView",
    "HabboValidationView",
    "HabboConfirmView",
    "HabboUnlinkView",
    "HabboValidationStatusView",
    "HabboValidationHistoryView",
]
