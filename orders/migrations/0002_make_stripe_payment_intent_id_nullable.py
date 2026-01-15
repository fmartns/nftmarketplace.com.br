# Generated manually to fix stripe_payment_intent_id constraint
# Esta migração torna o campo stripe_payment_intent_id opcional (nullable)
# para permitir criação de pedidos sem esse campo, já que usamos AbacatePay

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("orders", "0001_initial"),
    ]

    operations = [
        # Usa RunSQL para garantir que a coluna existe e é nullable
        migrations.RunSQL(
            # SQL para PostgreSQL: cria a coluna se não existir, ou altera para nullable se existir
            sql="""
                DO $$
                BEGIN
                    -- Verifica se a coluna existe
                    IF NOT EXISTS (
                        SELECT 1 FROM information_schema.columns 
                        WHERE table_name='orders_order' 
                        AND column_name='stripe_payment_intent_id'
                    ) THEN
                        -- Se a coluna não existe, cria como nullable
                        ALTER TABLE orders_order 
                        ADD COLUMN stripe_payment_intent_id VARCHAR(255) NULL;
                    ELSIF EXISTS (
                        SELECT 1 FROM information_schema.columns 
                        WHERE table_name='orders_order' 
                        AND column_name='stripe_payment_intent_id'
                        AND is_nullable='NO'
                    ) THEN
                        -- Se a coluna existe e é NOT NULL, altera para permitir NULL
                        ALTER TABLE orders_order 
                        ALTER COLUMN stripe_payment_intent_id DROP NOT NULL;
                    END IF;
                    -- Se a coluna já existe e já é nullable, não faz nada
                END
                $$;
            """,
            reverse_sql="""
                -- Reverte: torna a coluna NOT NULL novamente (se necessário)
                -- Nota: isso pode falhar se houver valores NULL na coluna
                DO $$
                BEGIN
                    IF EXISTS (
                        SELECT 1 FROM information_schema.columns 
                        WHERE table_name='orders_order' 
                        AND column_name='stripe_payment_intent_id'
                        AND is_nullable='YES'
                    ) THEN
                        -- Primeiro, atualiza valores NULL para string vazia
                        UPDATE orders_order 
                        SET stripe_payment_intent_id = '' 
                        WHERE stripe_payment_intent_id IS NULL;
                        
                        -- Depois, torna NOT NULL
                        ALTER TABLE orders_order 
                        ALTER COLUMN stripe_payment_intent_id SET NOT NULL;
                    END IF;
                END
                $$;
            """,
        ),
        # Atualiza o estado do Django para refletir o campo no modelo
        migrations.SeparateDatabaseAndState(
            database_operations=[
                # Não faz nada no banco, já alteramos acima com RunSQL
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
