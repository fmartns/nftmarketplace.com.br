"""
Utilitários para o módulo de pedidos
"""
import secrets
import string


def generate_order_id() -> str:
    """
    Gera um ID único de pedido no formato #KFNSFG (6 caracteres aleatórios maiúsculos)
    """
    characters = string.ascii_uppercase
    random_string = ''.join(secrets.choice(characters) for _ in range(6))
    return f"#{random_string}"





