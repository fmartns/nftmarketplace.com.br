# Generated manually to fix stripe_payment_intent_id constraint
# Esta migração torna o campo stripe_payment_intent_id opcional (nullable)
# para permitir criação de pedidos sem esse campo, já que usamos AbacatePay

from django.db import migrations, models, connection


def make_stripe_payment_intent_id_nullable_forward(apps, schema_editor):
    """Torna a coluna stripe_payment_intent_id nullable"""
    vendor = connection.vendor

    if vendor == "postgresql":
        # PostgreSQL: usa DO block
        with connection.cursor() as cursor:
            cursor.execute(
                """
                DO $$
                BEGIN
                    IF NOT EXISTS (
                        SELECT 1 FROM information_schema.columns 
                        WHERE table_name='orders_order' 
                        AND column_name='stripe_payment_intent_id'
                    ) THEN
                        ALTER TABLE orders_order 
                        ADD COLUMN stripe_payment_intent_id VARCHAR(255) NULL;
                    ELSIF EXISTS (
                        SELECT 1 FROM information_schema.columns 
                        WHERE table_name='orders_order' 
                        AND column_name='stripe_payment_intent_id'
                        AND is_nullable='NO'
                    ) THEN
                        ALTER TABLE orders_order 
                        ALTER COLUMN stripe_payment_intent_id DROP NOT NULL;
                    END IF;
                END
                $$;
            """
            )
    elif vendor == "sqlite":
        # SQLite: não precisa fazer nada, campos são nullable por padrão
        # Se a coluna já existe com NOT NULL, precisamos recriar a tabela
        # Mas como estamos apenas adicionando o campo ao estado, não precisamos fazer nada
        pass
    # Para outros bancos, não faz nada (o campo será adicionado pelo AddField)


def make_stripe_payment_intent_id_nullable_reverse(apps, schema_editor):
    """Reverte: torna a coluna NOT NULL novamente"""
    vendor = connection.vendor

    if vendor == "postgresql":
        with connection.cursor() as cursor:
            cursor.execute(
                """
                DO $$
                BEGIN
                    IF EXISTS (
                        SELECT 1 FROM information_schema.columns 
                        WHERE table_name='orders_order' 
                        AND column_name='stripe_payment_intent_id'
                        AND is_nullable='YES'
                    ) THEN
                        UPDATE orders_order 
                        SET stripe_payment_intent_id = '' 
                        WHERE stripe_payment_intent_id IS NULL;
                        
                        ALTER TABLE orders_order 
                        ALTER COLUMN stripe_payment_intent_id SET NOT NULL;
                    END IF;
                END
                $$;
            """
            )
    # Para SQLite e outros, não faz nada


class Migration(migrations.Migration):

    dependencies = [
        ("orders", "0001_initial"),
    ]

    operations = [
        # Usa RunPython para detectar o tipo de banco e executar SQL apropriado
        migrations.RunPython(
            make_stripe_payment_intent_id_nullable_forward,
            make_stripe_payment_intent_id_nullable_reverse,
        ),
        # Atualiza o estado do Django para refletir o campo no modelo
        migrations.SeparateDatabaseAndState(
            database_operations=[
                # Não faz nada no banco, já alteramos acima com RunPython
            ],
            state_operations=[
                migrations.AddField(
                    model_name="order",
                    name="stripe_payment_intent_id",
                    field=models.CharField(
                        max_length=255,
                        null=True,
                        blank=True,
                        help_text="ID do PaymentIntent do Stripe (opcional, usado apenas se pagamento via Stripe)",
                    ),
                ),
            ],
        ),
    ]
