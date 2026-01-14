from django.urls import path
from . import views

app_name = "accounts"

urlpatterns = [
    # Perfil do usuário
    path("me/", views.UserProfileView.as_view(), name="user-profile"),
    # Validação do Habbo
    path("habbo/verify/", views.HabboValidationView.as_view(), name="habbo-verify"),
    path("habbo/confirm/", views.HabboConfirmView.as_view(), name="habbo-confirm"),
    path("habbo/unlink/", views.HabboUnlinkView.as_view(), name="habbo-unlink"),
    path(
        "habbo/status/",
        views.HabboValidationStatusView.as_view(),
        name="habbo-validation-status",
    ),
    path(
        "habbo/history/",
        views.HabboValidationHistoryView.as_view(),
        name="habbo-validation-history",
    ),
    # Autenticação MetaMask
    path(
        "auth/metamask/message/",
        views.GenerateAuthMessageView.as_view(),
        name="generate-auth-message",
    ),
    path(
        "auth/metamask/login/", views.MetaMaskAuthView.as_view(), name="metamask-login"
    ),
    path(
        "auth/metamask/register/",
        views.MetaMaskRegisterView.as_view(),
        name="metamask-register",
    ),
]
