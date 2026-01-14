from django.urls import path
from .views import LegacyItemDetail, LegacyItemList

urlpatterns = [
    path("", LegacyItemList.as_view(), name="legacy-item-list"),
    path("<str:slug>/", LegacyItemDetail.as_view(), name="legacy-item-detail"),
]
