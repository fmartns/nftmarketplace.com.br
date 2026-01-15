import { useEffect, useState } from 'react';
import { CheckCircle2 } from 'lucide-react';
import { Button } from './ui/button';

interface PaymentSuccessPageProps {
  onBack?: () => void;
}

export function PaymentSuccessPage({ onBack }: PaymentSuccessPageProps) {
  const [orderId, setOrderId] = useState<string | null>(null);

  useEffect(() => {
    // Extrai order_id da URL
    const fullUrl = window.location.href;
    const urlMatch = fullUrl.match(/[?&]order_id=([^&#]*)/);
    
    let id: string | null = null;
    
    if (urlMatch && urlMatch[1]) {
      id = decodeURIComponent(urlMatch[1]);
    }
    
    if (!id || id === '') {
      const urlParams = new URLSearchParams(window.location.search);
      id = urlParams.get('order_id');
    }
    
    if (!id || id === '') {
      const hash = window.location.hash;
      if (hash && hash.length > 1) {
        id = hash.substring(1);
      }
    }
    
    if (id && id !== '') {
      id = id.trim();
      if (!id.startsWith('#')) {
        id = `#${id}`;
      }
    }
    
    setOrderId(id || null);
  }, []);

  const handleViewOrders = () => {
    if (onBack) {
      onBack();
    } else {
      window.location.href = '/pedidos';
    }
  };

  const handleOk = () => {
    window.location.href = '/';
  };

  return (
    <div className="min-h-screen bg-background flex items-center justify-center p-4">
      <div className="max-w-md w-full text-center space-y-8">
        {/* Ícone de Confirmação */}
        <div className="flex justify-center">
          <div className="rounded-full bg-green-500/20 p-6">
            <CheckCircle2 className="w-20 h-20 text-green-500" />
          </div>
        </div>

        {/* Título */}
        <div className="space-y-2">
          <h1 className="text-3xl font-bold text-foreground">Pagamento Confirmado!</h1>
          {orderId && (
            <p className="text-lg text-muted-foreground">
              Pedido {orderId}
            </p>
          )}
        </div>

        {/* Botões */}
        <div className="flex flex-col gap-3">
          <Button
            onClick={handleOk}
            className="w-full bg-[#FFE000] text-black hover:bg-[#FFD700] text-lg py-6"
            size="lg"
          >
            OK
          </Button>
          <Button
            onClick={handleViewOrders}
            variant="outline"
            className="w-full text-lg py-6"
            size="lg"
          >
            Ver Meus Pedidos
          </Button>
        </div>
      </div>
    </div>
  );
}
