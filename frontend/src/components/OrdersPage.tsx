import { useEffect, useState } from 'react';
import { ChevronDownIcon } from 'lucide-react';
import { ImageWithFallback } from './figma/ImageWithFallback';
import { fetchUserOrders, type Order } from '@/api/orders';
import { Skeleton } from './ui/skeleton';
import { Badge } from './ui/badge';
import { cn } from './ui/utils';

const statusLabels: Record<string, string> = {
  pending: 'Pendente',
  paid: 'Pago',
  processing: 'Processando',
  delivered: 'Entregue',
  cancelled: 'Cancelado',
  refunded: 'Reembolsado',
};

const statusColors: Record<string, string> = {
  pending: 'bg-yellow-500/20 text-yellow-500 border-yellow-500/30',
  paid: 'bg-blue-500/20 text-blue-500 border-blue-500/30',
  processing: 'bg-purple-500/20 text-purple-500 border-purple-500/30',
  delivered: 'bg-green-500/20 text-green-500 border-green-500/30',
  cancelled: 'bg-red-500/20 text-red-500 border-red-500/30',
  refunded: 'bg-gray-500/20 text-gray-500 border-gray-500/30',
};

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
    const day = date.getDate().toString().padStart(2, '0');
    const month = date.toLocaleDateString('pt-BR', { month: 'long' });
    const year = date.getFullYear();
    const hours = date.getHours().toString().padStart(2, '0');
    const minutes = date.getMinutes().toString().padStart(2, '0');
    return `${day} de ${month} de ${year} às ${hours}:${minutes}`;
  } catch {
    return dateString;
  }
}

export function OrdersPage() {
  const [orders, setOrders] = useState<Order[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [expandedOrderId, setExpandedOrderId] = useState<string | null>(null);

  useEffect(() => {
    let mounted = true;
    setLoading(true);
    setError(null);

    (async () => {
      try {
        await new Promise(resolve => setTimeout(resolve, 200));
        
        const token = localStorage.getItem('access_token') || localStorage.getItem('token');
        if (!token) {
          if (!mounted) return;
          setError('Usuário não autenticado');
          setLoading(false);
          return;
        }

        const data = await fetchUserOrders();
        if (!mounted) return;
        // Ensure data is always an array
        setOrders(Array.isArray(data) ? data : []);
        setError(null);
      } catch (e: any) {
        if (!mounted) return;
        console.error('Erro ao buscar pedidos:', e);
        if (e?.message?.includes('401') || e?.message?.includes('403')) {
          setError('Usuário não autenticado. Por favor, faça login novamente.');
          localStorage.removeItem('access_token');
          localStorage.removeItem('refresh_token');
          localStorage.removeItem('token');
        } else {
          setError(e?.message || 'Falha ao carregar pedidos');
        }
      } finally {
        if (mounted) setLoading(false);
      }
    })();

    return () => {
      mounted = false;
    };
  }, []);

  if (loading) {
    return (
      <div className="relative w-full">
        <div className="relative h-64 lg:h-80 overflow-hidden">
          <ImageWithFallback
            src="https://collectibles.habbo.com/hero-bg-xl.png"
            alt="Profile cover"
            className="w-full h-full object-cover opacity-50"
          />
          <div className="absolute inset-0 bg-gradient-to-t from-black/60 via-black/20 to-transparent" />
          <div className="absolute inset-0 bg-muted/30" />
        </div>
        <div className="container mx-auto px-4 lg:px-8">
          <div className="relative mt-12 lg:mt-16">
            <div className="max-w-4xl mx-auto space-y-4">
              <Skeleton className="h-32 w-full" />
              <Skeleton className="h-32 w-full" />
              <Skeleton className="h-32 w-full" />
            </div>
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="relative w-full">
        <div className="relative h-64 lg:h-80 overflow-hidden">
          <ImageWithFallback
            src="https://collectibles.habbo.com/hero-bg-xl.png"
            alt="Profile cover"
            className="w-full h-full object-cover"
          />
          <div className="absolute inset-0 bg-gradient-to-t from-black/60 via-black/20 to-transparent" />
        </div>
        <div className="container mx-auto px-4 lg:px-8 pb-16 lg:pb-24">
          <div className="relative mt-12 lg:mt-16">
            <div className="max-w-2xl mx-auto text-center">
              <h2 className="text-2xl font-bold mb-4">Erro ao carregar pedidos</h2>
              <p className="text-muted-foreground">{error}</p>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="relative w-full">
      {/* Cover Image */}
      <div className="relative h-64 lg:h-80 overflow-hidden">
        <ImageWithFallback
          src="https://collectibles.habbo.com/hero-bg-xl.png"
          alt="Orders cover"
          className="w-full h-full object-cover"
        />
        <div className="absolute inset-0 bg-gradient-to-t from-black/60 via-black/20 to-transparent" />
      </div>

      {/* Orders List */}
      <div className="container mx-auto px-4 lg:px-8 pb-16 lg:pb-24">
        <div className="relative mt-12 lg:mt-16">
          <div className="max-w-4xl mx-auto">
            <h1 className="text-3xl lg:text-4xl font-bold mb-8">Meus Pedidos</h1>

            {orders.length === 0 ? (
              <div className="text-center py-16">
                <p className="text-lg text-muted-foreground">Você ainda não realizou nenhum pedido.</p>
              </div>
            ) : (
              <div className="space-y-4">
                {orders.map((order) => {
                  const isExpanded = expandedOrderId === order.order_id;
                  
                  return (
                    <div
                      key={order.id}
                      className="bg-card border border-border rounded-xl overflow-hidden hover:border-[#FFE000]/30 transition-colors"
                    >
                      {/* Order Header - Clickable */}
                      <div
                        onClick={() => setExpandedOrderId(isExpanded ? null : order.order_id)}
                        className="p-6 cursor-pointer select-none"
                      >
                        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
                          <div className="flex-1">
                            <div className="flex items-center gap-3 mb-2 flex-wrap">
                              <h2 className="text-xl font-bold">Pedido #{order.order_id}</h2>
                              <Badge
                                variant="outline"
                                className={statusColors[order.status] || 'bg-gray-500/20 text-gray-500 border-gray-500/30'}
                              >
                                {statusLabels[order.status] || order.status}
                              </Badge>
                            </div>
                            <p className="text-sm text-muted-foreground">
                              {formatDate(order.created_at)}
                            </p>
                            {!isExpanded && order.items.length > 0 && (
                              <p className="text-sm text-muted-foreground mt-1">
                                {order.items.length} {order.items.length === 1 ? 'item' : 'itens'}
                              </p>
                            )}
                          </div>
                          <div className="flex items-center gap-4">
                            <div className="text-right">
                              <p className="text-2xl font-bold text-[#FFE000]">
                                {formatBRL(order.total)}
                              </p>
                              {order.discount_amount && parseFloat(order.discount_amount) > 0 && (
                                <p className="text-sm text-muted-foreground line-through">
                                  {formatBRL(order.subtotal)}
                                </p>
                              )}
                            </div>
                            <ChevronDownIcon
                              className={cn(
                                "size-5 text-muted-foreground transition-transform duration-200 flex-shrink-0",
                                isExpanded && "rotate-180"
                              )}
                            />
                          </div>
                        </div>
                      </div>

                      {/* Order Details - Expandable */}
                      {isExpanded && (
                        <div className="px-6 pb-6 border-t border-border/50 animate-in slide-in-from-top-2 duration-200">
                          {/* Order Items */}
                          <div className="space-y-3 mt-4 mb-4">
                            <h3 className="text-sm font-semibold text-muted-foreground uppercase tracking-wide">
                              Itens do Pedido
                            </h3>
                            {order.items.map((item) => (
                              <div
                                key={item.id}
                                className="flex items-center gap-4 p-3 bg-muted/30 rounded-lg"
                              >
                                {item.item_image_url && (
                                  <div className="w-24 h-24 sm:w-32 sm:h-32 rounded-lg overflow-hidden bg-black/20 flex-shrink-0 flex items-center justify-center">
                                    <ImageWithFallback
                                      src={item.item_image_url}
                                      alt={item.item_name}
                                      className="w-full h-full object-contain p-1"
                                    />
                                  </div>
                                )}
                                <div className="flex-1 min-w-0">
                                  <p className="font-medium truncate">{item.item_name}</p>
                                  <p className="text-sm text-muted-foreground">
                                    {item.item_type === 'legacy' ? 'Legacy' : 'NFT'} • Qtd: {item.quantity}
                                  </p>
                                </div>
                                <div className="text-right flex-shrink-0">
                                  <p className="font-medium">{formatBRL(item.total_price)}</p>
                                  {item.quantity > 1 && (
                                    <p className="text-xs text-muted-foreground">
                                      {formatBRL(item.unit_price)} cada
                                    </p>
                                  )}
                                </div>
                              </div>
                            ))}
                          </div>

                          {/* Order Footer */}
                          <div className="pt-4 border-t border-border/50 space-y-3">
                            {/* Payment and Delivery Details */}
                            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                              <div className="p-3 rounded-lg bg-muted/20">
                                <div className="text-xs text-muted-foreground mb-1">Status do Pagamento</div>
                                {order.paid_at || order.status === 'paid' || order.status === 'delivered' ? (
                                  <div className="flex items-center gap-2">
                                    <Badge className="bg-green-500/20 text-green-500 border-green-500/30">
                                      Confirmado
                                    </Badge>
                                    {order.paid_at && (
                                      <span className="text-xs text-muted-foreground">
                                        em {formatDate(order.paid_at)}
                                      </span>
                                    )}
                                  </div>
                                ) : (
                                  <Badge className="bg-yellow-500/20 text-yellow-500 border-yellow-500/30">
                                    Pendente
                                  </Badge>
                                )}
                              </div>
                              
                              <div className="p-3 rounded-lg bg-muted/20">
                                <div className="text-xs text-muted-foreground mb-1">Status da Entrega</div>
                                {order.delivered && order.delivered_at ? (
                                  <div className="flex items-center gap-2">
                                    <Badge className="bg-blue-500/20 text-blue-500 border-blue-500/30">
                                      Entregue
                                    </Badge>
                                    <span className="text-xs text-muted-foreground">
                                      em {formatDate(order.delivered_at)}
                                    </span>
                                  </div>
                                ) : order.paid_at || order.status === 'paid' || order.status === 'delivered' ? (
                                  <Badge className="bg-orange-500/20 text-orange-500 border-orange-500/30">
                                    Aguardando Entrega
                                  </Badge>
                                ) : (
                                  <Badge className="bg-gray-500/20 text-gray-500 border-gray-500/30">
                                    Aguardando Pagamento
                                  </Badge>
                                )}
                              </div>
                            </div>
                            
                            {order.coupon && (
                              <div className="text-sm">
                                <span className="text-muted-foreground">Cupom aplicado: </span>
                                <span className="font-medium text-foreground">{order.coupon}</span>
                              </div>
                            )}
                            {order.items.length > 0 && (
                              <div className="text-sm text-muted-foreground">
                                Total de itens: <span className="font-medium text-foreground">{order.items.length}</span>
                              </div>
                            )}
                          </div>
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

