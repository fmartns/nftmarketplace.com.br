# Módulo de Pagamentos AbacatePay

Este módulo fornece integração completa com a API da [AbacatePay](https://docs.abacatepay.com), um gateway de pagamento brasileiro simplificado.

## Configuração

### Variáveis de Ambiente

Adicione as seguintes variáveis ao seu arquivo `.env`:

```env
# AbacatePay API
ABACATEPAY_API_BASE_URL=https://api.abacatepay.com
ABACATEPAY_API_KEY=sua_chave_api_aqui
ABACATEPAY_WEBHOOK_SECRET=seu_secret_webhook_aqui
```

### Migrations

Execute as migrations para criar as tabelas:

```bash
python manage.py makemigrations payments
python manage.py migrate payments
```

## Funcionalidades

### Clientes

- **Criar cliente**: Cria um cliente na AbacatePay para o usuário autenticado
- **Listar clientes**: Lista clientes (admin vê todos, usuário comum vê apenas o seu)

### Cobranças (Billing)

- **Criar cobrança**: Cria uma nova cobrança para um pedido existente
- **Listar cobranças**: Lista todas as cobranças do usuário
- **Verificar status**: Verifica o status atualizado de uma cobrança
- **QRCode PIX**: Gera QRCode PIX para pagamento
- **Verificar PIX**: Verifica status de pagamento PIX
- **Simular pagamento**: Simula pagamento (apenas em dev mode)

### Webhooks

O módulo inclui um endpoint de webhook para receber notificações da AbacatePay:

- `POST /payments/webhook/`

Eventos suportados:
- `billing.paid`: Cobrança foi paga
- `billing.expired`: Cobrança expirou
- `billing.cancelled`: Cobrança foi cancelada

## Integração com Pedidos

O módulo está integrado com o sistema de pedidos (`orders`). Quando uma cobrança é criada:

1. O pedido é vinculado à cobrança
2. O status do pedido é atualizado automaticamente quando o pagamento é confirmado
3. A data de pagamento é registrada automaticamente

## Uso

### Criar uma cobrança para um pedido

```python
POST /payments/billing/create/
{
    "order_id": "#KFNSFG",
    "description": "Pedido de NFTs",
    "metadata": {
        "custom_field": "value"
    }
}
```

### Verificar status de uma cobrança

```python
GET /payments/billing/{billing_id}/status/
```

### Gerar QRCode PIX

```python
POST /payments/billing/{billing_id}/pix/qrcode/
```

## Documentação da API

A documentação completa está disponível no Swagger UI em `/docs/` após iniciar o servidor.

## Estrutura

```
payments/
├── models.py          # Modelos: AbacatePayCustomer, AbacatePayBilling, AbacatePayPayment
├── services.py        # Serviço de integração com API da AbacatePay
├── serializers/       # Serializers organizados por funcionalidade
├── views/            # Views organizadas por funcionalidade
├── docs/             # Documentação modularizada (schemas OpenAPI)
├── urls.py           # URLs do módulo
└── admin.py          # Configuração do admin Django
```

## Referências

- [Documentação AbacatePay](https://docs.abacatepay.com)
- [API Reference](https://docs.abacatepay.com/pages/introduction)
