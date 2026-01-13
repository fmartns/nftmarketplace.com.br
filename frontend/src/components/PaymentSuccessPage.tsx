import { useEffect, useState } from 'react';
import { CheckCircle2, Package, ArrowLeft, AlertCircle } from 'lucide-react';
import { Button } from './ui/button';
import { fetchOrderById, type Order } from '@/api/orders';
import { refreshAccessToken } from '@/api/accounts';
import { Skeleton } from './ui/skeleton';
import { Badge } from './ui/badge';
import { ImageWithFallback } from './figma/ImageWithFallback';

function formatBRL(value: string | number): string {
  const num = typeof value === 'string' ? parseFloat(value) : value;
  return new Intl.NumberFormat('pt-BR', {
    style: 'currency',
    currency: 'BRL',
  }).format(num);
}

function formatDate(dateString: string): string {
  try {
    const date = new Date(dateString);
    return new Intl.DateTimeFormat('pt-BR', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    }).format(date);
  } catch {
    return dateString;
  }
}

interface PaymentSuccessPageProps {
  onBack?: () => void;
}

export function PaymentSuccessPage({ onBack }: PaymentSuccessPageProps) {
  const [orderId, setOrderId] = useState<string | null>(null);
  const [order, setOrder] = useState<Order | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [hasAttemptedLoad, setHasAttemptedLoad] = useState(false);

  useEffect(() => {
    // Extrai order_id da URL
    // O problema é que quando temos ?order_id=#OAMIGV, o navegador interpreta o # como hash
    // Então precisamos pegar diretamente da URL completa antes do hash
    let id: string | null = null;
    
    // Pega a URL completa
    const fullUrl = window.location.href;
    
    // Tenta extrair o order_id usando regex na URL completa
    // Procura por order_id= seguido de qualquer coisa até encontrar & ou # ou fim da string
    // Isso captura mesmo se o # estiver no valor do parâmetro
    const urlMatch = fullUrl.match(/[?&]order_id=([^&#]*)/);
    if (urlMatch && urlMatch[1]) {
      // Decodifica o valor (caso tenha sido codificado como %23)
      id = decodeURIComponent(urlMatch[1]);
    }
    
    // Se não encontrou na URL completa, tenta pegar da query string
    // (pode funcionar se o navegador não tiver interpretado o # como hash)
    if (!id || id === '') {
      const urlParams = new URLSearchParams(window.location.search);
      id = urlParams.get('order_id');
    }
    
    // Se ainda não encontrou, tenta do hash
    // (caso o order_id tenha sido interpretado como hash pelo navegador)
    if (!id || id === '') {
      const hash = window.location.hash;
      if (hash && hash.length > 1) {
        // Remove o # inicial do hash
        id = hash.substring(1);
      }
    }
    
    // O order_id no banco tem o formato #XXXXXX, então mantém o #
    // Mas se vier sem #, adiciona
    if (id && id !== '') {
      // Remove espaços e caracteres especiais extras
      id = id.trim();
      // Se não começar com #, adiciona
      if (!id.startsWith('#')) {
        id = `#${id}`;
      }
    } else {
      id = null;
    }
    
    console.log('Order ID extraído:', id);
    console.log('URL completa:', window.location.href);
    console.log('Query params:', window.location.search);
    console.log('Hash:', window.location.hash);
    console.log('URL sem hash:', fullUrl.split('#')[0]);
    
    setOrderId(id);
  }, []);

  useEffect(() => {
    // Reset loading e error quando orderId muda
    setLoading(true);
    setError(null);
    setHasAttemptedLoad(false);
    
    if (!orderId) {
      console.log('OrderId é null, não fazendo requisição');
      setError('ID do pedido não encontrado');
      setLoading(false);
      setHasAttemptedLoad(true);
      return;
    }

    console.log('useEffect executado com orderId:', orderId);
    
    const loadOrder = async () => {
      setHasAttemptedLoad(true);
      try {
        // O order_id no banco tem o formato #XXXXXX
        // O endpoint espera o order_id com o #
        console.log('Iniciando busca do pedido com ID:', orderId);
        console.log('Token disponível:', !!localStorage.getItem('access_token'));
        console.log('Token completo:', localStorage.getItem('access_token')?.substring(0, 20) + '...');
        
        const order = await fetchOrderById(orderId);
        console.log('Pedido encontrado:', order);
        console.log('Tipo do pedido:', typeof order);
        console.log('Pedido tem order_id?', order?.order_id);
        
        if (!order) {
          console.error('Resposta vazia do servidor');
          setError('Pedido não encontrado: resposta vazia do servidor');
          setLoading(false);
          return;
        }
        
        console.log('Definindo pedido no estado');
        console.log('Order antes de definir:', order);
        setOrder(order);
        setError(null); // Limpa qualquer erro anterior
        setLoading(false); // Garante que o loading seja desativado
        console.log('Estado atualizado com sucesso');
      } catch (err: any) {
        console.error('Erro ao carregar pedido:', err);
        console.error('Detalhes do erro:', {
          status: err?.status,
          message: err?.message,
          response: err?.response,
          stack: err?.stack,
        });
        
        // Se o erro for 401 (token expirado), tenta renovar o token
        if (err?.status === 401 || err?.response?.status === 401 || err?.message?.includes('401')) {
          try {
            console.log('Token expirado, tentando renovar...');
            const refreshResponse = await refreshAccessToken();
            // Salva o novo token
            localStorage.setItem('access_token', refreshResponse.access);
            console.log('Token renovado com sucesso, tentando buscar pedido novamente...');
            
            // Tenta buscar o pedido novamente com o novo token
            const order = await fetchOrderById(orderId);
            console.log('Pedido encontrado após renovar token:', order);
            setOrder(order);
            return; // Sucesso, não precisa continuar para o tratamento de erro
          } catch (refreshErr: any) {
            console.error('Erro ao renovar token:', refreshErr);
            // Se falhar ao renovar, limpa os tokens e mostra mensagem
            localStorage.removeItem('access_token');
            localStorage.removeItem('refresh_token');
            localStorage.removeItem('token');
            setError('Sua sessão expirou. Por favor, faça login novamente para ver os detalhes do pedido.');
            return;
          }
        }
        
        if (err?.status === 404 || err?.response?.status === 404 || err?.message?.includes('404')) {
          setError(`Pedido não encontrado: ${orderId.replace(/^#/, '')}. Verifique se você está logado com a conta correta e se o pedido existe.`);
        } else {
          const errorMsg = err?.message || 'Erro desconhecido';
          // Se a mensagem contém detalhes do erro, usa ela
          if (err?.response?.detail) {
            setError(`Erro ao carregar informações do pedido: ${err.response.detail}`);
          } else {
            setError(`Erro ao carregar informações do pedido: ${errorMsg}`);
          }
        }
      } finally {
        setLoading(false);
      }
    };

    loadOrder();
  }, [orderId]);

  const handleBack = () => {
    if (onBack) {
      onBack();
    } else {
      window.location.href = '/pedidos';
    }
  };

  const handleContinueShopping = () => {
    window.location.href = '/';
  };

  // Debug: log do estado atual
  console.log('PaymentSuccessPage - Render - Estado atual:', {
    orderId,
    loading,
    error,
    hasOrder: !!order,
    orderOrderId: order?.order_id,
  });

  // Não mostra erro se ainda está carregando ou se não tentou buscar ainda
  if (loading) {
    return (
      <section className="bg-[#1a1a1a] text-white min-h-screen">
        <div className="max-w-[1800px] mx-auto flex flex-col gap-4 p-6">
          <Skeleton className="h-12 w-64" />
          <Skeleton className="h-96 w-full" />
        </div>
      </section>
    );
  }

  const handleLogin = () => {
    // Redireciona para a página inicial onde o usuário pode fazer login
    window.location.href = '/';
  };

  // Só mostra erro se tentou carregar e falhou, ou se não tem orderId
  if ((error || !order) && (hasAttemptedLoad || !orderId)) {
    const isSessionExpired = error?.includes('sessão expirou') || error?.includes('autenticado');
    
    return (
      <section className="bg-[#1a1a1a] text-white min-h-screen">
        <div className="max-w-[1800px] mx-auto flex flex-col gap-4 p-6">
          <div className="rounded-xl bg-[#202020] p-6 text-center">
            {isSessionExpired ? (
              <AlertCircle className="w-12 h-12 text-yellow-500 mx-auto mb-4" />
            ) : (
              <h1 className="text-2xl font-bold mb-4 text-red-500">Erro</h1>
            )}
            <p className="text-gray-300 mb-2">{error || 'Pedido não encontrado'}</p>
            {orderId && !isSessionExpired && (
              <p className="text-sm text-gray-400 mb-6">
                ID do pedido procurado: {orderId}
              </p>
            )}
            <div className="flex flex-col sm:flex-row gap-4 justify-center">
              {isSessionExpired ? (
                <>
                  <Button onClick={handleLogin} className="bg-[#FFE000] text-black hover:bg-[#FFD700]">
                    Fazer Login
                  </Button>
                  <Button onClick={handleContinueShopping} variant="outline">
                    Continuar Comprando
                  </Button>
                </>
              ) : (
                <>
                  <Button onClick={handleBack} variant="outline">
                    <ArrowLeft className="w-4 h-4 mr-2" />
                    Voltar para Pedidos
                  </Button>
                  <Button onClick={handleContinueShopping} className="bg-[#FFE000] text-black hover:bg-[#FFD700]">
                    Continuar Comprando
                  </Button>
                </>
              )}
            </div>
          </div>
        </div>
      </section>
    );
  }

  return (
    <section className="bg-[#1a1a1a] text-white min-h-screen">
      <div className="max-w-[1800px] mx-auto flex flex-col gap-4 p-6">
        {/* Header */}
        <div className="flex items-center gap-4">
          <Button
            onClick={handleBack}
            variant="ghost"
            size="icon"
            className="text-white hover:bg-white/10"
          >
            <ArrowLeft className="w-5 h-5" />
          </Button>
          <h1 className="text-2xl font-bold">Pagamento Realizado</h1>
        </div>

        {/* Success Message */}
        <div className="rounded-xl bg-[#202020] p-6 border border-green-500/30">
          <div className="flex items-center gap-4 mb-4">
            <div className="rounded-full bg-green-500/20 p-3">
              <CheckCircle2 className="w-8 h-8 text-green-500" />
            </div>
            <div>
              <h2 className="text-xl font-semibold text-green-500">Pagamento Confirmado!</h2>
              <p className="text-gray-400">Seu pedido foi processado com sucesso.</p>
            </div>
          </div>
        </div>

        {/* Order Details */}
        <div className="rounded-xl bg-[#202020] p-6">
          <div className="flex items-center justify-between mb-6">
            <div className="flex items-center gap-3">
              <Package className="w-6 h-6 text-[#FFE000]" />
              <h2 className="text-xl font-semibold">Detalhes do Pedido</h2>
            </div>
            <Badge className="bg-green-500/20 text-green-500 border-green-500/30">
              {order.status === 'paid' ? 'Pago' : order.status === 'pending' ? 'Pendente' : order.status}
            </Badge>
          </div>

          <div className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <p className="text-sm text-gray-400 mb-1">ID do Pedido</p>
                <p className="font-mono font-semibold">{order.order_id}</p>
              </div>
              <div>
                <p className="text-sm text-gray-400 mb-1">Data</p>
                <p>{formatDate(order.created_at)}</p>
              </div>
              {order.paid_at && (
                <div>
                  <p className="text-sm text-gray-400 mb-1">Data de Pagamento</p>
                  <p>{formatDate(order.paid_at)}</p>
                </div>
              )}
            </div>

            {/* Order Items */}
            <div className="mt-6">
              <h3 className="text-lg font-semibold mb-4">Itens do Pedido</h3>
              <div className="space-y-4">
                {order.items.map((item) => (
                  <div
                    key={item.id}
                    className="flex items-center gap-4 p-4 rounded-lg bg-[#1a1a1a] border border-white/10"
                  >
                    {item.item_image_url && (
                      <div className="w-24 h-24 sm:w-32 sm:h-32 rounded-lg overflow-hidden flex-shrink-0 bg-black/20 flex items-center justify-center">
                        <ImageWithFallback
                          src={item.item_image_url}
                          alt={item.item_name || 'Item'}
                          className="w-full h-full object-contain p-1"
                        />
                      </div>
                    )}
                    <div className="flex-1 min-w-0">
                      <p className="font-semibold truncate">{item.item_name || 'Item'}</p>
                      <p className="text-sm text-gray-400">
                        Quantidade: {item.quantity} × {formatBRL(item.unit_price)}
                      </p>
                    </div>
                    <div className="text-right">
                      <p className="font-semibold">{formatBRL(item.total_price)}</p>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Order Summary */}
            <div className="mt-6 pt-6 border-t border-white/10">
              <div className="space-y-2">
                <div className="flex justify-between text-gray-400">
                  <span>Subtotal</span>
                  <span>{formatBRL(order.subtotal)}</span>
                </div>
                {order.discount_amount && parseFloat(order.discount_amount) > 0 && (
                  <div className="flex justify-between text-green-500">
                    <span>Desconto</span>
                    <span>-{formatBRL(order.discount_amount)}</span>
                  </div>
                )}
                <div className="flex justify-between text-xl font-bold pt-2 border-t border-white/10">
                  <span>Total</span>
                  <span className="text-[#FFE000]">{formatBRL(order.total)}</span>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Actions */}
        <div className="flex flex-col sm:flex-row gap-4">
          <Button
            onClick={handleBack}
            variant="outline"
            className="flex-1 border-white/20 text-white hover:bg-white/10"
          >
            <ArrowLeft className="w-4 h-4 mr-2" />
            Voltar para Pedidos
          </Button>
          <Button
            onClick={handleContinueShopping}
            className="flex-1 bg-[#FFE000] text-black hover:bg-[#FFD700]"
          >
            Continuar Comprando
          </Button>
        </div>
      </div>
    </section>
  );
}
