import { useEffect, useState, useMemo } from 'react';
import { 
  ChevronDownIcon, 
  Package, 
  Clock, 
  CheckCircle2, 
  XCircle, 
  Truck, 
  Filter,
  ShoppingBag,
  Calendar,
  Receipt,
  CreditCard
} from 'lucide-react';
import { ImageWithFallback } from './figma/ImageWithFallback';
import { fetchUserOrders, type Order } from '@/api/orders';
import { createBilling } from '@/api/payments';
import { Skeleton } from './ui/skeleton';
import { Badge } from './ui/badge';
import { Button } from './ui/button';
import { Card, CardContent, CardHeader } from './ui/card';
import { cn } from './ui/utils';

// Função para determinar o status de exibição baseado no estado do pedido
function getDisplayStatus(order: Order): {
  label: string;
  color: string;
  icon: React.ReactNode;
} {
  // Status especiais (cancelado e reembolsado)
  if (order.status === 'cancelled') {
    return {
      label: 'Cancelado',
      color: 'bg-red-500/20 text-red-500 border-red-500/30',
      icon: <XCircle className="size-4" />,
    };
  }
  
  if (order.status === 'refunded') {
    return {
      label: 'Reembolsado',
      color: 'bg-gray-500/20 text-gray-500 border-gray-500/30',
      icon: <Receipt className="size-4" />,
    };
  }

  // Status do fluxo normal
  if (order.delivered && order.delivered_at) {
    return {
      label: 'Produto entregue',
      color: 'bg-green-500/20 text-green-500 border-green-500/30',
      icon: <Truck className="size-4" />,
    };
  }
  
  if (order.paid_at || order.status === 'paid' || order.status === 'delivered' || order.status === 'processing') {
    return {
      label: 'Pagamento confirmado, aguardando entrega',
      color: 'bg-blue-500/20 text-blue-500 border-blue-500/30',
      icon: <Package className="size-4" />,
    };
  }
  
  // Status padrão: aguardando pagamento
  return {
    label: 'Aguardando pagamento',
    color: 'bg-yellow-500/20 text-yellow-500 border-yellow-500/30',
    icon: <Clock className="size-4" />,
  };
}

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

function getTimeRemaining(createdAt: string): { minutes: number; seconds: number; expired: boolean } {
  const created = new Date(createdAt);
  const now = new Date();
  const elapsed = now.getTime() - created.getTime();
  const fiveMinutes = 5 * 60 * 1000;
  const remaining = fiveMinutes - elapsed;
  
  if (remaining <= 0) {
    return { minutes: 0, seconds: 0, expired: true };
  }
  
  return {
    minutes: Math.floor(remaining / 60000),
    seconds: Math.floor((remaining % 60000) / 1000),
    expired: false,
  };
}

export function OrdersPage() {
  const [orders, setOrders] = useState<Order[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [expandedOrderId, setExpandedOrderId] = useState<string | null>(null);
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const [timeRemaining, setTimeRemaining] = useState<Record<string, { minutes: number; seconds: number; expired: boolean }>>({});
  const [processingPayment, setProcessingPayment] = useState<Record<string, boolean>>({});

  // Atualiza contador de tempo para pedidos pendentes
  useEffect(() => {
    const pendingOrders = orders.filter(o => o.status === 'pending' && !o.paid_at);
    if (pendingOrders.length === 0) return;

    const interval = setInterval(() => {
      const updates: Record<string, { minutes: number; seconds: number; expired: boolean }> = {};
      pendingOrders.forEach(order => {
        updates[order.order_id] = getTimeRemaining(order.created_at);
      });
      setTimeRemaining(prev => ({ ...prev, ...updates }));
    }, 1000);

    // Inicializa os valores
    const initial: Record<string, { minutes: number; seconds: number; expired: boolean }> = {};
    pendingOrders.forEach(order => {
      initial[order.order_id] = getTimeRemaining(order.created_at);
    });
    setTimeRemaining(initial);

    return () => clearInterval(interval);
  }, [orders]);

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

  // Função auxiliar para determinar o tipo de status de exibição
  const getStatusType = (order: Order): string => {
    if (order.status === 'cancelled') return 'cancelled';
    if (order.status === 'refunded') return 'refunded';
    if (order.delivered && order.delivered_at) return 'delivered';
    if (order.paid_at || order.status === 'paid' || order.status === 'delivered' || order.status === 'processing') {
      return 'paid';
    }
    return 'pending';
  };

  const filteredOrders = useMemo(() => {
    if (statusFilter === 'all') return orders;
    return orders.filter(order => {
      const statusType = getStatusType(order);
      return statusType === statusFilter;
    });
  }, [orders, statusFilter]);

  const statusCounts = useMemo(() => {
    const counts: Record<string, number> = {
      all: orders.length,
      pending: 0,
      paid: 0,
      delivered: 0,
      cancelled: 0,
      refunded: 0,
    };
    orders.forEach(order => {
      const statusType = getStatusType(order);
      counts[statusType] = (counts[statusType] || 0) + 1;
    });
    return counts;
  }, [orders]);

  // Função para processar pagamento
  const handlePayment = async (order: Order) => {
    const orderId = order.order_id;
    
    // Verificar se já está processando
    if (processingPayment[orderId]) {
      return;
    }

    setProcessingPayment(prev => ({ ...prev, [orderId]: true }));

    try {
      // Criar cobrança
      const billing = await createBilling({
        order_id: orderId,
        description: `Pagamento do pedido ${orderId}`,
        metadata: {
          order_id: orderId,
        },
      });

      // Abrir URL de pagamento em nova aba
      if (billing.payment_url) {
        window.open(billing.payment_url, '_blank', 'noopener,noreferrer');
      } else {
        alert('Cobrança criada com sucesso! Verifique seus pedidos para mais detalhes.');
      }
    } catch (error: any) {
      console.error('Erro ao processar pagamento:', error);
      const errorMessage = error?.message || 'Erro ao processar pagamento. Tente novamente.';
      alert(errorMessage);
    } finally {
      setProcessingPayment(prev => ({ ...prev, [orderId]: false }));
    }
  };

  if (loading) {
    return (
      <div className="relative w-full min-h-screen">
        <div className="relative h-64 lg:h-80 overflow-hidden">
          <Skeleton className="w-full h-full" />
        </div>
        <div className="container mx-auto px-4 lg:px-8 py-8">
          <div className="max-w-6xl mx-auto space-y-4">
            <Skeleton className="h-10 w-64" />
            <Skeleton className="h-32 w-full" />
            <Skeleton className="h-32 w-full" />
            <Skeleton className="h-32 w-full" />
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="relative w-full min-h-screen">
        <div className="relative h-64 lg:h-80 overflow-hidden">
          <ImageWithFallback
            src="https://collectibles.habbo.com/hero-bg-xl.png"
            alt="Orders cover"
            className="w-full h-full object-cover opacity-50"
          />
          <div className="absolute inset-0 bg-gradient-to-t from-black/60 via-black/20 to-transparent" />
        </div>
        <div className="container mx-auto px-4 lg:px-8 py-16">
          <div className="max-w-2xl mx-auto text-center">
            <Card className="p-8">
              <XCircle className="size-16 text-destructive mx-auto mb-4" />
              <h2 className="text-2xl font-bold mb-2">Erro ao carregar pedidos</h2>
              <p className="text-muted-foreground">{error}</p>
            </Card>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="relative w-full min-h-screen bg-background">
      {/* Hero Section */}
      <div className="relative h-64 lg:h-80 overflow-hidden">
        <ImageWithFallback
          src="https://collectibles.habbo.com/hero-bg-xl.png"
          alt="Orders cover"
          className="w-full h-full object-cover"
        />
        <div className="absolute inset-0 bg-gradient-to-t from-black/80 via-black/40 to-transparent" />
        <div className="absolute inset-0 flex items-center justify-center">
          <div className="text-center text-white px-4">
            <ShoppingBag className="size-12 lg:size-16 mx-auto mb-4 opacity-90" />
            <h1 className="text-3xl lg:text-5xl font-bold mb-2">Meus Pedidos</h1>
            <p className="text-lg text-white/80">
              {orders.length === 0 
                ? 'Acompanhe seus pedidos aqui' 
                : `${orders.length} ${orders.length === 1 ? 'pedido' : 'pedidos'} encontrado${orders.length === 1 ? '' : 's'}`}
            </p>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="container mx-auto px-4 lg:px-8 py-8 lg:py-12">
        <div className="max-w-6xl mx-auto">
          {/* Filters */}
          {orders.length > 0 && (
            <div className="mb-8">
              <div className="flex items-center gap-2 mb-4">
                <Filter className="size-5 text-muted-foreground" />
                <h2 className="text-lg font-semibold">Filtrar por status</h2>
              </div>
              <div className="flex flex-wrap gap-2">
                {[
                  { key: 'all', label: 'Todos' },
                  { key: 'pending', label: 'Aguardando pagamento' },
                  { key: 'paid', label: 'Pagamento confirmado, aguardando entrega' },
                  { key: 'delivered', label: 'Produto entregue' },
                  { key: 'cancelled', label: 'Cancelado' },
                ].map(({ key, label }) => (
                  <Button
                    key={key}
                    variant={statusFilter === key ? 'default' : 'outline'}
                    size="sm"
                    onClick={() => setStatusFilter(key)}
                    className={cn(
                      'relative',
                      statusFilter === key && 'bg-[#FFE000] text-black hover:bg-[#FFD700]'
                    )}
                  >
                    {label}
                    {statusCounts[key] > 0 && (
                      <Badge 
                        variant="secondary" 
                        className={cn(
                          'ml-2 h-5 min-w-5 px-1.5 text-xs',
                          statusFilter === key ? 'bg-black/20 text-black' : ''
                        )}
                      >
                        {statusCounts[key]}
                      </Badge>
                    )}
                  </Button>
                ))}
              </div>
            </div>
          )}

          {/* Orders List */}
          {filteredOrders.length === 0 ? (
            <Card className="p-12 lg:p-16">
              <div className="text-center">
                <div className="inline-flex items-center justify-center size-20 rounded-full bg-muted mb-6">
                  <ShoppingBag className="size-10 text-muted-foreground" />
                </div>
                <h3 className="text-2xl font-bold mb-2">
                  {orders.length === 0 ? 'Nenhum pedido ainda' : 'Nenhum pedido encontrado'}
                </h3>
                <p className="text-muted-foreground mb-6 max-w-md mx-auto">
                  {orders.length === 0
                    ? 'Quando você realizar um pedido, ele aparecerá aqui para acompanhamento.'
                    : `Não há pedidos com o status selecionado.`}
                </p>
                {orders.length === 0 && (
                  <Button
                    variant="default"
                    onClick={() => window.location.href = '/nfts'}
                    className="bg-[#FFE000] text-black hover:bg-[#FFD700]"
                  >
                    Explorar Marketplace
                  </Button>
                )}
              </div>
            </Card>
          ) : (
            <div className="space-y-4">
              {filteredOrders.map((order) => {
                const isExpanded = expandedOrderId === order.order_id;
                const timeRem = timeRemaining[order.order_id];
                const isPending = order.status === 'pending' && !order.paid_at;
                const showTimer = isPending && timeRem && !timeRem.expired;
                const displayStatus = getDisplayStatus(order);
                const isAwaitingPayment = displayStatus.label === 'Aguardando pagamento';
                const isProcessingPayment = processingPayment[order.order_id] || false;
                
                return (
                  <Card
                    key={order.id}
                    className={cn(
                      "overflow-hidden transition-all duration-200 hover:shadow-lg",
                      isExpanded && "ring-2 ring-[#FFE000]/30"
                    )}
                  >
                    <CardHeader
                      className={cn(
                        "cursor-pointer select-none transition-colors",
                        isExpanded && "bg-muted/30"
                      )}
                      onClick={() => setExpandedOrderId(isExpanded ? null : order.order_id)}
                    >
                      <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4">
                        <div className="flex-1 space-y-3">
                          {/* Order ID and Status */}
                          <div className="flex items-center gap-3 flex-wrap">
                            <div className="flex items-center gap-2">
                              <Receipt className="size-5 text-muted-foreground" />
                              <h2 className="text-xl lg:text-2xl font-bold">
                                Pedido {order.order_id}
                              </h2>
                            </div>
                            {(() => {
                              return (
                                <Badge
                                  variant="outline"
                                  className={cn(
                                    "flex items-center gap-1.5",
                                    displayStatus.color
                                  )}
                                >
                                  {displayStatus.icon}
                                  {displayStatus.label}
                                </Badge>
                              );
                            })()}
                            {/* Botão de Pagamento - Aparece quando aguardando pagamento */}
                            {isAwaitingPayment && (
                              <Button
                                onClick={(e) => {
                                  e.stopPropagation();
                                  handlePayment(order);
                                }}
                                disabled={isProcessingPayment}
                                className="bg-[#FFE000] text-black hover:bg-[#FFD700] flex items-center gap-2"
                              >
                                <CreditCard className="size-4" />
                                {isProcessingPayment ? 'Processando...' : 'Pagar Agora'}
                              </Button>
                            )}
                          </div>

                          {/* Date and Items Count */}
                          <div className="flex items-center gap-4 text-sm text-muted-foreground flex-wrap">
                            <div className="flex items-center gap-1.5">
                              <Calendar className="size-4" />
                              {formatDate(order.created_at)}
                            </div>
                            {!isExpanded && order.items.length > 0 && (
                              <div className="flex items-center gap-1.5">
                                <Package className="size-4" />
                                {order.items.length} {order.items.length === 1 ? 'item' : 'itens'}
                              </div>
                            )}
                          </div>

                          {/* Timer for Pending Orders */}
                          {showTimer && (
                            <div className="flex items-center gap-2 text-sm">
                              <Clock className="size-4 text-yellow-500 animate-pulse" />
                              <span className="font-medium text-yellow-600 dark:text-yellow-400">
                                Tempo restante para pagamento: {String(timeRem.minutes).padStart(2, '0')}:
                                {String(timeRem.seconds).padStart(2, '0')}
                              </span>
                            </div>
                          )}
                        </div>

                        {/* Price and Expand Icon */}
                        <div className="flex items-center gap-4 lg:flex-col lg:items-end">
                          <div className="text-right">
                            <p className="text-2xl lg:text-3xl font-bold text-[#FFE000]">
                              {formatBRL(order.total)}
                            </p>
                            {order.discount_amount && parseFloat(order.discount_amount) > 0 && (
                              <div className="flex items-center gap-2 justify-end mt-1">
                                <p className="text-sm text-muted-foreground line-through">
                                  {formatBRL(order.subtotal)}
                                </p>
                                <Badge variant="secondary" className="text-xs">
                                  -{formatBRL(order.discount_amount)}
                                </Badge>
                              </div>
                            )}
                          </div>
                          <ChevronDownIcon
                            className={cn(
                              "size-5 lg:size-6 text-muted-foreground transition-transform duration-200 flex-shrink-0",
                              isExpanded && "rotate-180"
                            )}
                          />
                        </div>
                      </div>
                    </CardHeader>

                    {/* Expanded Details */}
                    {isExpanded && (
                      <CardContent className="pt-0 pb-6 animate-in slide-in-from-top-2 duration-200">
                        <div className="space-y-6">
                          {/* Order Items */}
                          <div>
                            <h3 className="text-sm font-semibold text-muted-foreground uppercase tracking-wide mb-4 flex items-center gap-2">
                              <Package className="size-4" />
                              Itens do Pedido
                            </h3>
                            <div className="space-y-3">
                              {order.items.map((item) => (
                                <div
                                  key={item.id}
                                  className="flex items-center gap-4 p-4 bg-muted/30 rounded-lg hover:bg-muted/50 transition-colors"
                                >
                                  {item.item_image_url && (
                                    <div className="w-20 h-20 lg:w-24 lg:h-24 rounded-lg overflow-hidden bg-black/20 flex-shrink-0 flex items-center justify-center border border-border">
                                      <ImageWithFallback
                                        src={item.item_image_url}
                                        alt={item.item_name || 'Item'}
                                        className="w-full h-full object-contain p-1"
                                      />
                                    </div>
                                  )}
                                  <div className="flex-1 min-w-0">
                                    <p className="font-semibold truncate">{item.item_name || 'Item sem nome'}</p>
                                    <div className="flex items-center gap-2 mt-1 flex-wrap">
                                      <Badge variant="outline" className="text-xs">
                                        {item.item_type === 'legacy' ? 'Legacy' : 'NFT'}
                                      </Badge>
                                      <span className="text-sm text-muted-foreground">
                                        Quantidade: {item.quantity}
                                      </span>
                                    </div>
                                  </div>
                                  <div className="text-right flex-shrink-0">
                                    <p className="font-bold text-lg">{formatBRL(item.total_price)}</p>
                                    {item.quantity > 1 && (
                                      <p className="text-xs text-muted-foreground mt-1">
                                        {formatBRL(item.unit_price)} cada
                                      </p>
                                    )}
                                  </div>
                                </div>
                              ))}
                            </div>
                          </div>

                          {/* Additional Info - Cupom only */}
                          {order.coupon && (
                            <div className="pt-4 border-t">
                              <div className="text-sm">
                                <span className="text-muted-foreground">Cupom aplicado: </span>
                                <Badge variant="secondary" className="ml-1">
                                  {order.coupon}
                                </Badge>
                              </div>
                            </div>
                          )}

                          {/* Order Summary */}
                          <div className="pt-4 border-t">
                            <div className="flex justify-between items-center text-sm">
                              <span className="text-muted-foreground">Subtotal:</span>
                              <span className="font-medium">{formatBRL(order.subtotal)}</span>
                            </div>
                            {order.discount_amount && parseFloat(order.discount_amount) > 0 && (
                              <div className="flex justify-between items-center text-sm mt-2">
                                <span className="text-muted-foreground">Desconto:</span>
                                <span className="font-medium text-green-600 dark:text-green-400">
                                  -{formatBRL(order.discount_amount)}
                                </span>
                              </div>
                            )}
                            <div className="flex justify-between items-center text-lg font-bold mt-4 pt-4 border-t">
                              <span>Total:</span>
                              <span className="text-[#FFE000]">{formatBRL(order.total)}</span>
                            </div>
                          </div>

                          {/* Botão de Pagamento - Na seção expandida */}
                          {isAwaitingPayment && (
                            <div className="pt-4 border-t">
                              <Button
                                onClick={() => handlePayment(order)}
                                disabled={isProcessingPayment}
                                className="w-full bg-[#FFE000] text-black hover:bg-[#FFD700] flex items-center justify-center gap-2 py-6 text-lg font-semibold"
                                size="lg"
                              >
                                <CreditCard className="size-5" />
                                {isProcessingPayment ? 'Processando pagamento...' : 'Realizar Pagamento'}
                              </Button>
                            </div>
                          )}
                        </div>
                      </CardContent>
                    )}
                  </Card>
                );
              })}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
