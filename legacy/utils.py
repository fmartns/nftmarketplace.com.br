from .models import DefaultPricingConfig

def convert_item_price(value: float) -> float:
    """
    Converte o preço do item usando a configuração de pricing padrão.
    Se não houver configuração, usa bar_value padrão de 50 (multiplicador 1.0).
    """
    
    default_pricing_config = DefaultPricingConfig.objects.first()


    if default_pricing_config is None:
        bar_value = 10.0
    else:
        bar_value = float(default_pricing_config.bar_value)
    price = value * (bar_value / 50)
    return price
    
    