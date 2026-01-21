from django.db import models


class Banner(models.Model):
    """
    Modelo para banners editáveis que podem ser exibidos nas páginas de coleção.
    """

    title = models.CharField(
        max_length=200,
        verbose_name="Título",
        help_text="Título do banner (para identificação no admin)",
    )

    image_url = models.URLField(
        max_length=500,
        verbose_name="URL da Imagem",
        help_text="URL da imagem do banner (ex: https://exemplo.com/imagem.jpg)",
        default="https://via.placeholder.com/800x300/FFE000/000000?text=Banner+Placeholder",
    )

    image_mobile = models.URLField(
        max_length=500,
        verbose_name="URL da Imagem (Mobile)",
        help_text="URL da imagem do banner para dispositivos móveis (opcional).",
        blank=True,
    )

    is_active = models.BooleanField(
        default=True,
        verbose_name="Ativo",
        help_text="Se o banner está ativo e deve ser exibido",
    )

    order = models.PositiveIntegerField(
        default=0,
        verbose_name="Ordem",
        help_text="Ordem de exibição (menor número aparece primeiro)",
    )

    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Criado em")

    updated_at = models.DateTimeField(auto_now=True, verbose_name="Atualizado em")

    class Meta:
        verbose_name = "Banner"
        verbose_name_plural = "Banners"
        ordering = ["order", "-created_at"]

    def __str__(self):
        return f"{self.title}"
