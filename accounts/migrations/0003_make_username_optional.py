# Generated manually to make username optional

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0002_alter_user_cpf_alter_user_telefone_and_more"),
    ]

    operations = [
        migrations.AlterField(
            model_name="user",
            name="username",
            field=models.CharField(
                blank=True,
                help_text="Nome de usuário (opcional)",
                max_length=150,
                null=True,
                unique=True,
            ),
        ),
    ]
