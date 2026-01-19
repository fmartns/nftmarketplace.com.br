import { useEffect, useMemo, useState } from 'react';
import { Button } from './ui/button';
import { ImageWithFallback } from './figma/ImageWithFallback';
import { ArrowLeft, Share2, Heart, AlertCircle } from 'lucide-react';
import { Line, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid, ComposedChart, Bar, Legend, Label, ReferenceLine, Area } from 'recharts';
import { fetchLegacyItem, type LegacyItem } from '@/api/legacy';
import { Skeleton } from './ui/skeleton';
import { ShareModal } from './ShareModal';
import { fetchUserProfile, User } from '@/api/accounts';
import { createOrder } from '@/api/orders';
import { createBilling } from '@/api/payments';
import { useSEO } from '@/hooks/useSEO';
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from './ui/alert-dialog';

interface LegacyItemPageProps {
  slug: string;
  onBack: () => void;
}

function formatBRL(n: number) {
  return n.toLocaleString('pt-BR', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}

interface PriceHistoryData {
  period_days: number;
  total_points: number;
  original_points: number;
  compression_applied: boolean;
  prices: {
    price: number[];
    average: number[];
    quantity: number[];
    dates: number[];
  };
}

export function LegacyItemPage({ slug, onBack }: LegacyItemPageProps) {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [item, setItem] = useState<LegacyItem | null>(null);
  const [isShareModalOpen, setIsShareModalOpen] = useState(false);
  const [user, setUser] = useState<User | null>(null);
  const [isProfileIncompleteDialogOpen, setIsProfileIncompleteDialogOpen] = useState(false);
  const [isPurchasing, setIsPurchasing] = useState(false);
  const [missingFields, setMissingFields] = useState<string[]>([]);

  // Load user profile
  useEffect(() => {
    const token = localStorage.getItem('access_token') || localStorage.getItem('token');
    if (token) {
      fetchUserProfile()
        .then(setUser)
        .catch(() => setUser(null));
    }
  }, []);

  useEffect(() => {
    let mounted = true;
    setLoading(true);
    setItem(null);
    setError(null);

    (async () => {
      try {
        const data = await fetchLegacyItem(slug);
        if (!mounted) return;
        setItem(data);
        setError(null);
      } catch (e: any) {
        if (!mounted) return;
        setError(e?.message || 'Falha ao carregar item');
      } finally {
        if (mounted) setLoading(false);
      }
    })();

    return () => {
      mounted = false;
    };
  }, [slug]);

  const priceHistory = useMemo(() => {
    if (!item?.price_history) return null;
    // Se price_history for uma string JSON, parsear
    if (typeof item.price_history === 'string') {
      try {
        return JSON.parse(item.price_history) as PriceHistoryData;
      } catch {
        return null;
      }
    }
    return item.price_history as PriceHistoryData;
  }, [item]);

  // SEO para página do produto Legacy
  const seoTitle = useMemo(() => {
    if (item?.name) return `${item.name} - Legacy Item | NFT Marketplace`;
    if (slug) return `Item Legacy ${slug} - NFT Marketplace`;
    return undefined;
  }, [item?.name, slug]);

  const seoDescription = useMemo(() => {
    if (item?.name) {
      const priceText = item?.last_price ? `Preço: R$ ${formatBRL(item.last_price)}.` : '';
      return `Compre ${item.name} no NFT Marketplace. ${priceText} Item Legacy Habbo com histórico de preços completo.`.trim();
    }
    if (slug) {
      return `Item Legacy ${slug} disponível no NFT Marketplace. Explore e compre itens únicos do Habbo.`;
    }
    return undefined;
  }, [item?.name, item?.last_price, slug]);

  useSEO({
    title: seoTitle,
    description: seoDescription,
    image: item?.image_url || undefined,
    url: typeof window !== 'undefined' ? window.location.href : undefined,
    type: 'product',
    productImage: item?.image_url || undefined, // Usar imagem do produto como favicon
  });

  const chartData = useMemo(() => {
    if (!item?.price_history) return [];
    
    // Tentar parsear se for string
    let ph: any = priceHistory;
    if (!ph && item.price_history) {
      if (typeof item.price_history === 'string') {
        try {
          ph = JSON.parse(item.price_history);
        } catch {
          ph = item.price_history;
        }
      } else {
        ph = item.price_history;
      }
    }
    
    if (!ph?.prices) return [];
    
    const pricesObj = ph.prices;
    const prices = pricesObj?.price;
    const average = pricesObj?.average;
    const quantity = pricesObj?.quantity;
    const dates = pricesObj?.dates;
    
    // Verificar se todos os arrays existem e têm dados
    if (!prices || !Array.isArray(prices) || prices.length === 0) return [];
    if (!average || !Array.isArray(average)) return [];
    if (!quantity || !Array.isArray(quantity)) return [];
    if (!dates || !Array.isArray(dates)) return [];
    
    // Garantir que todos os arrays tenham o mesmo tamanho
    const minLength = Math.min(prices.length, average.length, quantity.length, dates.length);
    
    if (minLength === 0) return [];
    
    return prices.slice(0, minLength).map((price, index) => {
      const timestamp = dates[index] * 1000; // Convert to milliseconds
      const date = new Date(timestamp);
      const dateStr = date.toLocaleDateString('pt-BR', { day: '2-digit', month: '2-digit' });
      
      return {
        date: dateStr,
        price: Number(price) || 0,
        average: Number(average[index]) || 0,
        volume: Number(quantity[index]) || 0,
      };
    });
  }, [item, priceHistory]);

  const avgPrice = useMemo(() => {
    if (!item) return 0;
    return item.average_price || 0;
  }, [item]);

  const itemUrl = `${window.location.origin}/legacy/${slug}`;

  const whatsappUrl = `https://wa.me/5511987120592?text=${encodeURIComponent(
    `Olá! Tenho interesse no item ${item?.name || slug}.\nVi por R$ ${item ? formatBRL(item.last_price) : '0,00'}.\nLink: ${itemUrl}`
  )}`;

  // Validação de perfil
  // Validar se o perfil do usuário está completo para comprar
  // Nota: Esta validação é específica para compra, não usa perfil_completo do backend
  // que requer mais campos (telefone, nick_habbo, wallet_address)
  const validateProfile = (userProfile: User | null): { isValid: boolean; missingFields: string[] } => {
    if (!userProfile) {
      return { isValid: false, missingFields: ['CPF', 'Nome completo', 'Email', 'Data de nascimento'] };
    }

    const missing: string[] = [];
    
    // CPF: verifica se existe e não está vazio (necessário para pagamento)
    const cpf = userProfile.cpf;
    if (!cpf || (typeof cpf === 'string' && cpf.trim() === '')) {
      missing.push('CPF');
    }
    
    // Nome completo: verifica first_name E last_name (necessário para pagamento)
    const firstName = userProfile.first_name;
    const lastName = userProfile.last_name;
    if (!firstName || (typeof firstName === 'string' && firstName.trim() === '') ||
        !lastName || (typeof lastName === 'string' && lastName.trim() === '')) {
      missing.push('Nome completo');
    }
    
    // Email: verifica se existe e não está vazio (necessário para comunicação)
    const email = userProfile.email;
    if (!email || (typeof email === 'string' && email.trim() === '')) {
      missing.push('Email');
    }
    
    // Data de nascimento: verifica se existe (pode ser string de data ou null)
    // Necessário para validação de idade e documentos
    const dataNascimento = userProfile.data_nascimento;
    if (!dataNascimento || (typeof dataNascimento === 'string' && dataNascimento.trim() === '')) {
      missing.push('Data de nascimento');
    }

    return {
      isValid: missing.length === 0,
      missingFields: missing,
    };
  };

  // Função para comprar
  const handlePurchase = async () => {
    // Verificar autenticação
    const token = localStorage.getItem('access_token') || localStorage.getItem('token');
    if (!token) {
      alert('Você precisa estar autenticado para comprar. Faça login primeiro.');
      return;
    }

    // Buscar perfil atualizado
    let currentUser = user;
    if (!currentUser) {
      try {
        currentUser = await fetchUserProfile();
        setUser(currentUser);
      } catch (error) {
        alert('Erro ao buscar perfil. Tente fazer login novamente.');
        return;
      }
    }

    // Validar perfil
    const validation = validateProfile(currentUser);
    if (!validation.isValid) {
      setMissingFields(validation.missingFields);
      setIsProfileIncompleteDialogOpen(true);
      return;
    }

    // Verificar se temos o item
    if (!item || !item.id) {
      alert('Aguarde o carregamento completo do item antes de comprar.');
      return;
    }

    setIsPurchasing(true);
    try {
      // 1. Criar pedido
      const order = await createOrder({
        items: [
          {
            item_type: 'legacy',
            item_id: item.id,
            quantity: 1,
          },
        ],
        notes: `Compra do Legacy Item: ${item.name}`,
      });

      // 2. Criar cobrança na AbacatePay
      const billing = await createBilling({
        order_id: order.order_id,
        description: `Compra do Legacy Item: ${item.name}`,
        metadata: {
          slug: slug,
          item_name: item.name,
        },
      });

      // 3. Redirecionar para página de pagamento
      if (billing.payment_url) {
        window.open(billing.payment_url, '_blank', 'noopener,noreferrer');
      } else {
        alert('Cobrança criada com sucesso! Verifique seus pedidos para mais detalhes.');
      }
    } catch (error: any) {
      console.error('Erro ao processar compra:', error);
      const errorMessage = error?.message || 'Erro ao processar compra. Tente novamente.';
      alert(errorMessage);
    } finally {
      setIsPurchasing(false);
    }
  };

  if (loading) {
    return (
      <section className="bg-[#1a1a1a] text-white min-h-screen">
        <div className="max-w-[1800px] mx-auto flex flex-col gap-4 p-6">
          <div className="flex items-center justify-between">
            <Skeleton className="h-10 w-32" />
            <Skeleton className="h-10 w-32" />
          </div>
          <div className="flex flex-col lg:flex-row gap-6 justify-center">
            <div className="flex-[3] space-y-4">
              <div className="rounded-xl bg-[#202020] p-4 w-full">
                <Skeleton className="w-full h-[400px] rounded-lg" />
              </div>
              <div className="rounded-xl bg-[#202020] p-4 w-full">
                <Skeleton className="h-5 w-40 mb-3" />
                <Skeleton className="h-[340px] w-full" />
              </div>
            </div>
            <div className="flex-[2] space-y-4">
              <div className="rounded-xl bg-[#202020] p-4 w-full">
                <Skeleton className="h-12 w-3/4 mb-4" />
                <Skeleton className="h-20 w-full" />
              </div>
            </div>
          </div>
        </div>
      </section>
    );
  }

  if (error || !item) {
    return (
      <section className="bg-[#1a1a1a] text-white min-h-screen">
        <div className="max-w-[1800px] mx-auto flex flex-col gap-4 p-6">
          <div className="flex items-center justify-between">
            <Button onClick={onBack} className="bg-[#FFE000] hover:bg-[#FFD700] text-black">
              <ArrowLeft className="w-4 h-4 mr-2" /> Voltar
            </Button>
          </div>
          <div className="text-center py-16">
            <h2 className="text-2xl font-bold mb-4">Erro ao carregar item</h2>
            <p className="text-muted-foreground">{error || 'Item não encontrado'}</p>
          </div>
        </div>
      </section>
    );
  }

  return (
    <>
      <ShareModal
        isOpen={isShareModalOpen}
        onClose={() => setIsShareModalOpen(false)}
        url={itemUrl}
        title={item.name}
      />
      <AlertDialog open={isProfileIncompleteDialogOpen} onOpenChange={setIsProfileIncompleteDialogOpen}>
        <AlertDialogContent className="bg-[#202020] border-white/10 text-white">
          <AlertDialogHeader>
            <AlertDialogTitle className="text-[#FFE000] flex items-center gap-2">
              <AlertCircle className="w-5 h-5" />
              Perfil Incompleto
            </AlertDialogTitle>
            <AlertDialogDescription className="text-gray-300">
              Para realizar uma compra, você precisa completar seu perfil com as seguintes informações:
            </AlertDialogDescription>
          </AlertDialogHeader>
          <div className="py-4">
            <ul className="list-disc list-inside space-y-2 text-sm text-gray-300">
              {missingFields.map((field) => (
                <li key={field} className="text-gray-300">
                  {field}
                </li>
              ))}
            </ul>
            <p className="mt-4 text-sm text-gray-400">
              Complete seu perfil nas configurações da conta para continuar com a compra.
            </p>
          </div>
          <AlertDialogFooter>
            <AlertDialogCancel className="bg-transparent border-white/20 text-white hover:bg-white/10">
              Cancelar
            </AlertDialogCancel>
            <AlertDialogAction
              onClick={() => {
                setIsProfileIncompleteDialogOpen(false);
                window.location.href = '/configuracoes';
              }}
              className="bg-[#FFE000] text-black hover:bg-[#FFD700]"
            >
              Completar Perfil
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
      <section className="bg-[#1a1a1a] text-white min-h-screen">
        <div className="max-w-[1800px] mx-auto flex flex-col gap-4 p-6">
          <div className="flex items-center justify-between">
            <Button onClick={onBack} className="bg-[#FFE000] hover:bg-[#FFD700] text-black">
              <ArrowLeft className="w-4 h-4 mr-2" /> Voltar
            </Button>
            <div className="flex items-center gap-2">
              <Button size="sm" variant="outline" className="h-9 w-9 p-0">
                <Heart className="w-4 h-4" />
              </Button>
              <Button
                size="sm"
                variant="outline"
                className="h-9 w-9 p-0"
                onClick={() => setIsShareModalOpen(true)}
              >
                <Share2 className="w-4 h-4" />
              </Button>
            </div>
          </div>

          <div className="flex flex-col lg:flex-row gap-6 scroll-smooth justify-center">
            {/* Left Column */}
            <div className="flex-[3] lg:max-h-[calc(100vh-160px)] lg:overflow-y-auto scroll-smooth space-y-4">
              {/* Image - Fixed 400x400px */}
              <div className="rounded-xl bg-[#202020] p-4 w-full">
                <div className="w-[400px] h-[400px] mx-auto rounded-lg overflow-hidden bg-black/20 flex items-center justify-center" style={{ width: '400px', height: '400px', minWidth: '400px', minHeight: '400px', maxWidth: '400px', maxHeight: '400px' }}>
                  <ImageWithFallback
                    src={item.image_url || ''}
                    alt={item.name}
                    className="max-w-full max-h-full w-auto h-auto object-contain p-4"
                  />
                </div>
              </div>

              {/* Chart */}
              {chartData && chartData.length > 0 ? (
                <div className="rounded-xl bg-[#202020] p-4 w-full">
                  <div className="flex items-center justify-between mb-3">
                    <h3 className="font-medium">Preço médio diário</h3>
                  </div>
                  <div className="order-chart-wrapper w-full" style={{ width: '100%', height: 340 }}>
                    <ResponsiveContainer width="100%" height="100%">
                      <ComposedChart data={chartData} className="time-series-chart">
                        <defs>
                          <linearGradient id="priceLineGradient" x1="0" y1="0" x2="1" y2="0">
                            <stop offset="0%" stopColor="#FFE000"/>
                            <stop offset="100%" stopColor="#FFD700"/>
                          </linearGradient>
                          <linearGradient id="averageLineGradient" x1="0" y1="0" x2="1" y2="0">
                            <stop offset="0%" stopColor="#f59e0b"/>
                            <stop offset="100%" stopColor="#d97706"/>
                          </linearGradient>
                          <linearGradient id="volumeBarGradient" x1="0" y1="0" x2="0" y2="1">
                            <stop offset="0%" stopColor="#4dabf7" stopOpacity={0.95} />
                            <stop offset="100%" stopColor="#4dabf7" stopOpacity={0.6} />
                          </linearGradient>
                        </defs>
                        <CartesianGrid strokeDasharray="4 4" stroke="rgba(255,255,255,0.10)" />
                        <XAxis
                          dataKey="date"
                          stroke="#9ca3af"
                          tick={{ fill: '#9ca3af' }}
                          style={{ fontSize: '12px' }}
                          angle={-25}
                          textAnchor="end"
                          height={32}
                          axisLine={false}
                          tickLine={false}
                        />
                        <YAxis
                          stroke="#9ca3af"
                          tick={{ fill: '#f5d85c' }}
                          style={{ fontSize: '12px' }}
                          tickFormatter={(v) => `R$ ${formatBRL(Number(v))}`}
                          domain={[(dataMin: number) => (dataMin && dataMin > 0 ? dataMin * 0.9 : 0), (dataMax: number) => (dataMax && dataMax > 0 ? dataMax * 1.1 : 1)]}
                          axisLine={false}
                          tickLine={false}
                        >
                          <Label value="Preço (BRL)" angle={-90} position="insideLeft" fill="#f5d85c" style={{ fontSize: '12px' }} />
                        </YAxis>
                        <YAxis yAxisId="volume" orientation="right" hide domain={[0, 'auto']} />
                        <Tooltip
                          contentStyle={{ backgroundColor: '#202020', border: '1px solid rgba(255,224,0,0.2)', borderRadius: 8 }}
                          labelStyle={{ color: '#FFE000' }}
                          formatter={(val: any, name: any) => {
                            if (name === 'Preço' || name === 'Média') return [`R$ ${formatBRL(Number(val))}`, name];
                            if (name === 'Volume') return [String(val), 'Volume'];
                            return [String(val), name];
                          }}
                        />
                        <Legend verticalAlign="top" align="right" wrapperStyle={{ right: 8, top: 0, color: '#cbd5e1' }} />
                        <Bar name="Volume" yAxisId="volume" dataKey="volume" barSize={10} fill="url(#volumeBarGradient)" radius={[6, 6, 0, 0]} />
                        <Line name="Preço" type="monotone" dataKey="price" stroke="url(#priceLineGradient)" strokeWidth={2.5} dot={{ r: 2.2, stroke: '#FFE000', fill: '#FFE000' }} activeDot={{ r: 4 }} />
                        <Line name="Média" type="monotone" dataKey="average" stroke="url(#averageLineGradient)" strokeWidth={2} strokeDasharray="6 6" dot={{ r: 1.5, stroke: '#f59e0b', fill: '#f59e0b' }} />
                        {avgPrice > 0 && (
                          <ReferenceLine y={avgPrice} stroke="#f59e0b" strokeDasharray="6 6" ifOverflow="extendDomain" label={{ value: 'média geral', position: 'right', fill: '#f59e0b', fontSize: 11 }} />
                        )}
                      </ComposedChart>
                    </ResponsiveContainer>
                  </div>
                </div>
              ) : (
                <div className="rounded-xl bg-[#202020] p-4 w-full">
                  <div className="flex items-center justify-between mb-3">
                    <h3 className="font-medium">Preço médio diário</h3>
                  </div>
                  <div className="text-center py-8 text-gray-400">
                    <p>Nenhum dado de histórico disponível</p>
                  </div>
                </div>
              )}
            </div>

            {/* Right Column */}
            <div className="flex-[2] lg:max-h-[calc(100vh-160px)] lg:overflow-y-auto scroll-smooth space-y-4">
              {/* Header Card */}
              <div className="rounded-xl bg-[#202020] p-4 w-full">
                <div className="flex items-start justify-between gap-4">
                  <div>
                    <h1 className="text-2xl lg:text-3xl font-bold">{item.name}</h1>
                    <div className="mt-1 text-sm text-gray-400">
                      {item.available_offers > 0 ? `${item.available_offers} ofertas disponíveis` : 'Legacy Item'}
                    </div>
                  </div>
                </div>
              </div>

              {/* Action Panel */}
              <div className="rounded-xl bg-[#202020] p-4 w-full">
                <div className="space-y-4">
                  <div className="grid grid-cols-1 gap-3">
                    <div className="rounded-lg bg-black/20 p-3 text-center">
                      <div className="text-xs text-gray-400">Preço</div>
                      <div className="text-xl font-bold text-[#FFE000]">R$ {formatBRL(item.last_price)}</div>
                    </div>
                  </div>

                  <div className="grid grid-cols-2 gap-3">
                    <Button 
                      onClick={handlePurchase}
                      disabled={isPurchasing || !item}
                      className="bg-[#FFE000] text-black h-11 text-base hover:bg-[#FFD700] disabled:opacity-60 disabled:cursor-not-allowed"
                    >
                      {isPurchasing ? 'Processando...' : 'Comprar'}
                    </Button>
                    <Button
                      onClick={() => window.open(whatsappUrl, '_blank', 'noopener,noreferrer')}
                      variant="outline"
                      className="h-11 text-base border-[#25D366]/50 text-[#25D366] hover:bg-[#25D366]/10"
                    >
                      WhatsApp
                    </Button>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>
    </>
  );
}
