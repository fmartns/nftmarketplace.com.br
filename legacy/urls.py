from django.urls import path
from .views import LegacyItemDetail, LegacyItemCreate, LegacyItemList

urlpatterns = [
    path("", LegacyItemList.as_view(), name="legacy-item-list"),
    path("create/", LegacyItemCreate.as_view(), name="legacy-item-create"),
    path("<str:slug>/", LegacyItemDetail.as_view(), name="legacy-item-detail"),
]