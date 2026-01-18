from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
import random
from banners.models import Banner
from banners.serializers import BannerSerializer


class BannerListAPIView(APIView):
    """
    API para listar banners ativos
    """

    permission_classes = [AllowAny]

    def get(self, request):
        banners = Banner.objects.filter(is_active=True).order_by("order", "-created_at")

        serializer = BannerSerializer(banners, many=True, context={"request": request})
        return Response(serializer.data)


class BannerDetailAPIView(APIView):
    """
    API para obter detalhes de um banner específico
    """

    permission_classes = [AllowAny]

    def get(self, request, pk):
        try:
            banner = Banner.objects.get(pk=pk, is_active=True)
            serializer = BannerSerializer(banner, context={"request": request})
            return Response(serializer.data)
        except Banner.DoesNotExist:
            return Response(
                {"message": "Banner não encontrado"}, status=status.HTTP_404_NOT_FOUND
            )


class CollectionBannerAPIView(APIView):
    """
    Endpoint específico para o banner das páginas de coleção.
    Retorna um banner aleatório entre os banners ativos.
    """

    permission_classes = [AllowAny]

    def get(self, request):
        banners = Banner.objects.filter(is_active=True)

        if not banners.exists():
            return Response(
                {"message": "Nenhum banner encontrado"},
                status=status.HTTP_404_NOT_FOUND,
            )

        # Seleciona um banner aleatório
        count = banners.count()
        random_index = random.randint(0, count - 1)
        banner = banners[random_index]

        serializer = BannerSerializer(banner, context={"request": request})
        return Response(serializer.data)
