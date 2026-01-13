from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema, OpenApiResponse


class HealthCheckView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        summary="Health check",
        description="Check if the server is running",
        responses={
            200: OpenApiResponse(description="Server is running"),
        },
    )
    def get(self, request):
        return Response({"status": "ok"}, status=200)
