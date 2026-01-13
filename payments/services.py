"""
Serviço de integração com AbacatePay API
"""
import re
import requests
import logging
from decimal import Decimal
from typing import Optional, Dict, Any, List
from django.conf import settings

logger = logging.getLogger(__name__)


class AbacatePayService:
    """
    Serviço para gerenciar pagamentos com AbacatePay
    """
    
    @staticmethod
    def _get_headers() -> Dict[str, str]:
        """Retorna headers padrão para requisições"""
        api_key = getattr(settings, "ABACATEPAY_API_KEY", "")
        return {
            "Authorization": f"Bearer {api_key or ''}",
            "Content-Type": "application/json",
        }
    
    @staticmethod
    def _make_request(
        method: str,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Faz uma requisição para a API da AbacatePay
        
        Args:
            method: Método HTTP (GET, POST, etc.)
            endpoint: Endpoint da API (ex: /billing/create)
            data: Dados para enviar no body (para POST/PUT)
        
        Returns:
            Dict com a resposta da API no formato {data: {...}, error: null}
        """
        # Verifica se a API base URL está configurada
        if not ABACATEPAY_API_BASE_URL:
            error_msg = "ABACATEPAY_API_BASE_URL não está configurada. Configure a variável de ambiente ABACATEPAY_API_BASE_URL"
            logger.error(error_msg)
            return {"data": None, "error": {"message": error_msg, "statusCode": 500}}
        
        # Obtém configurações do settings
        api_base_url = getattr(settings, "ABACATEPAY_API_BASE_URL", None)
        api_key = getattr(settings, "ABACATEPAY_API_KEY", "")
        
        # Verifica se a API base URL está configurada
        if not api_base_url:
            error_msg = "ABACATEPAY_API_BASE_URL não está configurada. Configure a variável de ambiente ABACATEPAY_API_BASE_URL"
            logger.error(error_msg)
            return {"data": None, "error": {"message": error_msg, "statusCode": 500}}
        
        url = f"{api_base_url}{endpoint}"
        
        # Verifica se a API key está configurada antes de fazer a requisição
        if not api_key:
            error_msg = "ABACATEPAY_API_KEY não está configurada. Configure a variável de ambiente ABACATEPAY_API_KEY"
            logger.error(error_msg)
            return {"data": None, "error": {"message": error_msg, "statusCode": 401}}
        
        headers = AbacatePayService._get_headers()
        
        # Log do payload para debug (sem expor API key)
        if data:
            import json
            log_data = json.dumps(data, indent=2, ensure_ascii=False)
            logger.info(f"Payload enviado para {endpoint}: {log_data}")
        
        try:
            if method.upper() == "GET":
                response = requests.get(url, headers=headers, params=data)
            elif method.upper() == "POST":
                response = requests.post(url, headers=headers, json=data)
            else:
                raise ValueError(f"Método HTTP não suportado: {method}")
            
            response.raise_for_status()
            return response.json()
        
        except requests.exceptions.RequestException as e:
            logger.error(f"Erro ao fazer requisição para AbacatePay: {e}")
            logger.error(f"URL tentada: {url}")
            logger.error(f"Headers: {headers}")
            if hasattr(e, "response") and e.response is not None:
                try:
                    error_data = e.response.json()
                    logger.error(f"Resposta de erro da API: {error_data}")
                    return {"data": None, "error": error_data}
                except:
                    logger.error(f"Status code: {e.response.status_code}")
                    logger.error(f"Response text: {e.response.text[:500]}")
                    return {"data": None, "error": {"message": str(e), "status_code": e.response.status_code}}
            return {"data": None, "error": {"message": str(e)}}
    
    @staticmethod
    def create_customer(
        user_id: str,
        email: Optional[str] = None,
        name: Optional[str] = None,
        cellphone: Optional[str] = None,
        tax_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Cria um novo cliente na AbacatePay
        
        Args:
            user_id: ID do usuário no sistema
            email: Email do cliente
            name: Nome do cliente (obrigatório)
            cellphone: Telefone celular (obrigatório, apenas números)
            tax_id: CPF/CNPJ (obrigatório, apenas números)
            metadata: Metadados adicionais
        
        Returns:
            Dict com dados do cliente criado ou erro
        """
        # Campo name é obrigatório
        if not name and not email:
            return {
                "data": None,
                "error": {
                    "message": "Nome ou email é obrigatório para criar cliente",
                    "statusCode": 400
                }
            }
        customer_name = name or email
        
        # Campo cellphone é obrigatório - remove caracteres não numéricos
        if not cellphone:
            return {
                "data": None,
                "error": {
                    "message": "Telefone celular é obrigatório para criar cliente",
                    "statusCode": 400
                }
            }
        # Remove tudo que não é número
        cellphone_clean = re.sub(r'\D', '', cellphone)
        if len(cellphone_clean) < 10:
            return {
                "data": None,
                "error": {
                    "message": "Telefone celular inválido",
                    "statusCode": 400
                }
            }
        
        # Campo taxId é obrigatório - remove caracteres não numéricos do CPF
        if not tax_id:
            return {
                "data": None,
                "error": {
                    "message": "CPF/CNPJ é obrigatório para criar cliente",
                    "statusCode": 400
                }
            }
        # Remove tudo que não é número
        tax_id_clean = re.sub(r'\D', '', tax_id)
        if len(tax_id_clean) < 11:
            return {
                "data": None,
                "error": {
                    "message": "CPF/CNPJ inválido",
                    "statusCode": 400
                }
            }
        
        data = {
            "name": customer_name,
            "cellphone": cellphone_clean,
            "taxId": tax_id_clean,
            "metadata": {
                "user_id": str(user_id),
                **(metadata or {}),
            },
        }
        
        if email:
            data["email"] = email
            data["metadata"]["email"] = email
        
        # Usa o endpoint correto que encontramos
        endpoint = "/v1/customer/create"
        
        response = AbacatePayService._make_request(
            "POST",
            endpoint,
            data,
        )
        
        if response.get("error"):
            logger.error(f"Erro ao criar cliente: {response['error']}")
            return response
        
        return response
    
    @staticmethod
    def list_customers() -> Dict[str, Any]:
        """
        Lista todos os clientes
        
        Returns:
            Dict com lista de clientes ou erro
        """
        return AbacatePayService._make_request("GET", "/client/list")
    
    @staticmethod
    def create_billing(
        customer_id: Optional[str],
        amount: Decimal,
        description: str,
        products: Optional[List[Dict[str, Any]]] = None,
        return_url: Optional[str] = None,
        completion_url: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Cria uma nova cobrança (billing)
        
        Args:
            customer_id: ID do cliente na AbacatePay (opcional, pode ser None)
            amount: Valor da cobrança em reais
            description: Descrição da cobrança
            products: Lista de produtos (obrigatório) - formato: [{"name": "...", "quantity": 1, "price": 1000}]
            return_url: URL para voltar (obrigatório)
            completion_url: URL de conclusão do pagamento (obrigatório)
            metadata: Metadados adicionais
        
        Returns:
            Dict com dados da cobrança criada ou erro
        """
        # Converte Decimal para centavos (int)
        amount_cents = int(amount * 100)
        
        # Campo products é obrigatório
        if not products:
            # Se não fornecido, cria um produto genérico
            products = [{
                "externalId": f"product_{int(amount_cents)}",
                "name": description or "Produto",
                "description": description or "Produto",
                "quantity": 1,
                "price": amount_cents,
            }]
        
        # Campos returnUrl e completionUrl são obrigatórios
        # Se não fornecidos, usa a primeira origem do frontend
        if not return_url or not completion_url:
            frontend_origins = getattr(settings, "CORS_ALLOWED_ORIGINS", [])
            if not frontend_origins:
                return {
                    "data": None,
                    "error": {
                        "message": "CORS_ALLOWED_ORIGINS não configurado e return_url/completion_url não fornecidos",
                        "statusCode": 400
                    }
                }
            base_url = frontend_origins[0]
            
            if not return_url:
                return_url = f"{base_url}/payment"
            if not completion_url:
                completion_url = f"{base_url}/payment/success"
        
        data = {
            "amount": amount_cents,
            "description": description,
            "frequency": "ONE_TIME",  # Campo obrigatório: ONE_TIME, RECURRING, etc.
            "methods": ["PIX"],  # Apenas PIX (CARD requer habilitação adicional)
            "products": products,  # Campo obrigatório: array de produtos
            "returnUrl": return_url,  # Campo obrigatório: URL para voltar
            "completionUrl": completion_url,  # Campo obrigatório: URL de conclusão do pagamento
            "metadata": metadata or {},
        }
        
        # Adiciona customerId apenas se fornecido
        if customer_id:
            data["customerId"] = customer_id
        
        # Usa o endpoint correto que encontramos
        endpoint = "/v1/billing/create"
        
        response = AbacatePayService._make_request(
            "POST",
            endpoint,
            data,
        )
        
        if response.get("error"):
            logger.error(f"Erro ao criar cobrança: {response['error']}")
            return response
        
        return response
    
    @staticmethod
    def list_billings() -> Dict[str, Any]:
        """
        Lista todas as cobranças
        
        Returns:
            Dict com lista de cobranças ou erro
        """
        return AbacatePayService._make_request("GET", "/v1/billing/list")
    
    @staticmethod
    def get_billing_status(billing_id: str) -> Dict[str, Any]:
        """
        Verifica o status de uma cobrança
        
        Args:
            billing_id: ID da cobrança na AbacatePay
        
        Returns:
            Dict com status da cobrança ou erro
        """
        # Lista todas as cobranças e filtra pelo billing_id
        list_response = AbacatePayService._make_request("GET", "/v1/billing/list")
        
        if list_response.get("error"):
            return list_response
        
        # Procura a cobrança específica na lista
        billings = list_response.get("data", [])
        for billing in billings:
            if billing.get("id") == billing_id:
                return {"data": billing, "error": None}
        
        # Se não encontrou, retorna erro
        return {
            "data": None,
            "error": {"message": f"Cobrança {billing_id} não encontrada", "statusCode": 404}
        }
    
    @staticmethod
    def create_pix_qrcode(billing_id: str) -> Dict[str, Any]:
        """
        Cria um QRCode PIX para uma cobrança
        
        Args:
            billing_id: ID da cobrança
        
        Returns:
            Dict com dados do QRCode PIX ou erro
        """
        data = {"billingId": billing_id}
        
        response = AbacatePayService._make_request(
            "POST",
            "/pix/qrcode/create",
            data,
        )
        
        if response.get("error"):
            logger.error(f"Erro ao criar QRCode PIX: {response['error']}")
            return response
        
        return response
    
    @staticmethod
    def check_pix_status(billing_id: str) -> Dict[str, Any]:
        """
        Verifica o status de pagamento PIX
        
        Args:
            billing_id: ID da cobrança
        
        Returns:
            Dict com status do pagamento PIX ou erro
        """
        return AbacatePayService._make_request(
            "GET",
            "/pix/check",
            {"billingId": billing_id},
        )
    
    @staticmethod
    def simulate_payment(billing_id: str) -> Dict[str, Any]:
        """
        Simula um pagamento (apenas em dev mode)
        
        Args:
            billing_id: ID da cobrança
        
        Returns:
            Dict com resultado da simulação ou erro
        """
        data = {"billingId": billing_id}
        
        response = AbacatePayService._make_request(
            "POST",
            "/pix/simulate",
            data,
        )
        
        if response.get("error"):
            logger.error(f"Erro ao simular pagamento: {response['error']}")
            return response
        
        return response
