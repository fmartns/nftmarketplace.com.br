"""
Views módulo - Contém todas as views organizadas por funcionalidade
"""

from .metamask import MetaMaskAuthView, MetaMaskRegisterView, GenerateAuthMessageView
from .user import UserProfileView
from .habbo import (
    HabboValidationView,
    HabboUnlinkView,
    HabboValidationStatusView,
    HabboValidationHistoryView,
    HabboConfirmView,
)

__all__ = [
    "MetaMaskAuthView",
    "MetaMaskRegisterView",
    "GenerateAuthMessageView",
    "UserProfileView",
    "HabboValidationView",
    "HabboUnlinkView",
    "HabboValidationStatusView",
    "HabboValidationHistoryView",
    "HabboConfirmView",
]
