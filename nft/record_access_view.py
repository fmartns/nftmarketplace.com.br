from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
from django.utils import timezone

from .models import NFTItem, NFTItemAccess
from .serializers.items import RecordAccessSerializer


class RecordNFTAccessAPI(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        ser = RecordAccessSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        product_code = ser.validated_data.get("product_code")
        item_id = ser.validated_data.get("item_id")
        obj = None
        if item_id:
            obj = NFTItem.objects.filter(id=item_id).first()
        elif product_code:
            obj = NFTItem.objects.filter(product_code=product_code).first()
        if not obj:
            return Response(
                {"detail": "Item não encontrado"}, status=status.HTTP_404_NOT_FOUND
            )

        # Derive simple hashes to avoid storing raw PII
        def _hash(s: str) -> str:
            try:
                import hashlib

                return hashlib.sha256(s.encode("utf-8")).hexdigest()
            except Exception:
                return ""

        ip = request.META.get("REMOTE_ADDR", "")
        ua = request.META.get("HTTP_USER_AGENT", "")
        NFTItemAccess.objects.create(
            item=obj,
            ip_hash=_hash(ip) if ip else "",
            user_agent_hash=_hash(ua) if ua else "",
            accessed_at=timezone.now(),
        )
        return Response({"status": "ok"})
