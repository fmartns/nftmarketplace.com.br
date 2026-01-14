#!/bin/bash
# Script para criar o usuário nftuser no PostgreSQL se não existir

echo "Criando usuário nftuser no PostgreSQL..."

# Ler variáveis do .env se existir
if [ -f "../.env" ]; then
    export $(cat ../.env | grep -v '^#' | xargs)
fi

# Usar valores padrão se não estiverem no .env
POSTGRES_USER=${POSTGRES_USER:-postgres}
POSTGRES_PASSWORD=${POSTGRES_PASSWORD:-postgres}
POSTGRES_DB=${POSTGRES_DB:-nft_portal}
NEW_USER=${POSTGRES_USER:-nftuser}
NEW_PASSWORD=${POSTGRES_PASSWORD}

# Se o usuário já for postgres, não precisa fazer nada
if [ "$NEW_USER" = "postgres" ]; then
    echo "Usuário já é postgres, nada a fazer."
    exit 0
fi

# Criar usuário se não existir
docker compose exec -T db psql -U postgres << EOF
DO \$\$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_user WHERE usename = '$NEW_USER') THEN
        CREATE USER $NEW_USER WITH PASSWORD '$NEW_PASSWORD';
        ALTER USER $NEW_USER CREATEDB;
        GRANT ALL PRIVILEGES ON DATABASE $POSTGRES_DB TO $NEW_USER;
        ALTER DATABASE $POSTGRES_DB OWNER TO $NEW_USER;
        RAISE NOTICE 'Usuário $NEW_USER criado com sucesso';
    ELSE
        RAISE NOTICE 'Usuário $NEW_USER já existe';
    END IF;
END
\$\$;
EOF

echo "Concluído!"
