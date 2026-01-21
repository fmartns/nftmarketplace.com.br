import { useEffect, useMemo, useState } from 'react';
import { Button } from './ui/button';
import { ImageWithFallback } from './figma/ImageWithFallback';
import { ArrowLeft, Heart, Share2, ShoppingCart, MessageCircle, Info, AlertCircle } from 'lucide-react';
import { fetchImmutableItem, fetchImmutableListings, ImmutableItemView, ImmutableListingView, fetchImmutableAsset, metadataToAttributes } from '@/api/immutable';
import { Tabs, TabsContent } from './ui/tabs';
import { Line, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid, ComposedChart, Bar, Legend, Label, ReferenceLine } from 'recharts';
import { upsertNFTByProductCode, fetchNFTByProductCode, recordNFTView, NFTItem } from '@/api/nft';
import { Skeleton } from './ui/skeleton';
import { Tooltip as UITooltip, TooltipContent as UITooltipContent, TooltipTrigger as UITooltipTrigger } from './ui/tooltip';
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

interface NFTItemPageProps {
  slug: string;
  productCode: string;
  onBack: () => void;
}

function formatBRL(n: number) {
  return n.toLocaleString('pt-BR', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}

export function NFTItemPage({ slug, productCode, onBack }: NFTItemPageProps) {
  const [loadingBasicInfo, setLoadingBasicInfo] = useState(true);
  const [loadingPrice, setLoadingPrice] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [item, setItem] = useState<ImmutableItemView | null>(null);
  const [listings, setListings] = useState<ImmutableListingView[]>([]);
  const [sevenDayAvgBRL, setSevenDayAvgBRL] = useState<number | null>(null);
  const [isShareModalOpen, setIsShareModalOpen] = useState(false);
  const [user, setUser] = useState<User | null>(null);
  const [nftItem, setNftItem] = useState<NFTItem | null>(null);
  const [isProfileIncompleteDialogOpen, setIsProfileIncompleteDialogOpen] = useState(false);
  const [isPurchasing, setIsPurchasing] = useState(false);
  const [missingFields, setMissingFields] = useState<string[]>([]);
  const [profileFetchedAt, setProfileFetchedAt] = useState<number | null>(null);
  const [purchaseMessage, setPurchaseMessage] = useState<{ type: 'error' | 'success'; text: string } | null>(null);

  // Load user profile
  useEffect(() => {
    const token = localStorage.getItem('access_token') || localStorage.getItem('token');
    if (token) {
      fetchUserProfile()
        .then((profile) => {
          setUser(profile);
          setProfileFetchedAt(Date.now());
        })
        .catch(() => setUser(null));
    }
  }, []);

  // Carregar informações básicas primeiro (nome, foto, atributos)
  useEffect(() => {
    let mounted = true;
    setLoadingBasicInfo(true);
    // fire-and-forget record view for trending by access
    recordNFTView({ product_code: productCode }).catch(() => {});
    
    (async () => {
      try {
        // 1) Buscar dados básicos do backend IMEDIATAMENTE (sem esperar upsert)
        // Isso permite exibir nome e foto o mais rápido possível
        const backendItemPromise = fetchNFTByProductCode(productCode).catch(() => null);
        
        // 2) Fazer upsert em paralelo (não bloqueia a exibição)
        const upsertPromise = Promise.race([
          upsertNFTByProductCode(productCode),
          new Promise((_, reject) => setTimeout(() => reject(new Error('upsert-timeout')), 5000)),
        ]).catch((e: any) => {
          if (!mounted) return;
          const msg = String(e?.message || 'erro');
          const isHardFail = msg.includes(' 400 ') || msg.toLowerCase().includes('coleção') || msg.toLowerCase().includes('nao cadastrada') || msg.toLowerCase().includes('não cadastrada');
          if (isHardFail) {
            setError('Coleção não cadastrada para este produto.');
          }
          return null;
        });
        
        // 3) Buscar item do backend (pode ter dados antigos, mas exibe imediatamente)
        const backendItem = await backendItemPromise;
        
        if (!mounted) return;
        
        if (backendItem) {
          setNftItem(backendItem);
          
          // Criar item básico com dados do backend - EXIBIR IMEDIATAMENTE
          const basicItem: ImmutableItemView = {
            name: backendItem.name || productCode,
            image_url: backendItem.image_url || '',
            product_code: productCode,
            last_price_eth: 0,
            last_price_usd: 0,
            last_price_brl: backendItem.last_price_brl ? Number(backendItem.last_price_brl) : 0,
            attributes: [],
          } as ImmutableItemView;
          
          setItem(basicItem);
          setError(null);
          setLoadingBasicInfo(false); // Parar loading assim que tiver dados básicos - NOME E FOTO JÁ VISÍVEIS
        } else {
          // Se não tem backend, tentar Immutable
          try {
            const immutableItem = await fetchImmutableItem(productCode);
            if (mounted && immutableItem) {
              setItem(immutableItem);
              setError(null);
              setLoadingBasicInfo(false);
            }
          } catch {
            // Se falhar, manter loading até ter algo
            if (mounted) {
              setError('Item não encontrado');
              setLoadingBasicInfo(false);
            }
          }
        }
        
        // 4) Aguardar upsert completar (em background, não bloqueia UI)
        await upsertPromise;
        
        // 5) Se o upsert completou, buscar item atualizado (com preço novo)
        if (mounted) {
          const updatedItem = await fetchNFTByProductCode(productCode).catch(() => null);
          if (updatedItem && mounted) {
            setNftItem(updatedItem);
            // Atualizar preço se mudou
            if (updatedItem.last_price_brl) {
              setItem(prev => prev ? {
                ...prev,
                last_price_brl: Number(updatedItem.last_price_brl),
              } : prev);
            }
          }
        }
        
        // 6) Enriquecer com dados da Immutable em background (sem bloquear)
        if (mounted) {
          try {
            const immutableItem = await fetchImmutableItem(productCode);
            if (mounted && immutableItem) {
              setItem(prev => prev ? {
                ...prev,
                name: immutableItem.name || prev.name,
                image_url: immutableItem.image_url || prev.image_url,
                attributes: immutableItem.attributes || prev.attributes,
              } : immutableItem);
            }
          } catch {
            // Ignorar erro, já temos dados básicos
          }
        }
      } catch (e: any) {
        if (mounted) {
          setError(e?.message || 'Falha ao carregar informações básicas');
          setLoadingBasicInfo(false);
        }
      }
    })();
    
    return () => {
      mounted = false;
    };
  }, [productCode]);

  // Carregar preços e listagens separadamente
  useEffect(() => {
    let mounted = true;
    setLoadingPrice(true);
    
    const withTimeout = <T,>(p: Promise<T>, ms = 4000): Promise<T> =>
      Promise.race([
        p,
        new Promise<T>((_, reject) => setTimeout(() => reject(new Error('timeout')), ms)) as Promise<T>,
      ]);
    
    (async () => {
      try {
        if (!mounted) return;

        // 1) Primeiro, garantir que o backend está atualizado (refresh do preço)
        // Isso garante que temos o preço mais recente mesmo se o primeiro useEffect não completou o upsert
        try {
          await Promise.race([
            upsertNFTByProductCode(productCode),
            new Promise((_, reject) => setTimeout(() => reject(new Error('upsert-timeout')), 3000)),
          ]);
        } catch {
          // Ignorar erro, continua mesmo se falhar
        }

        if (!mounted) return;

        // 2) Buscar preços e listagens em paralelo (agora com backend atualizado)
        const listingsPromise = fetchImmutableListings(productCode);
        const backendPromise = fetchNFTByProductCode(productCode).catch(() => null);

        // 3) Carregar listagens (usando mesma lógica de markup do backend)
        let ls: ImmutableListingView[] = [];
        try {
          const lsRaw = await withTimeout(listingsPromise, 5000);
          if (!mounted) return;
          ls = (lsRaw || [])
            .filter(l => typeof l.price_brl === 'number' && isFinite(l.price_brl) && l.price_brl > 0)
            .sort((a, b) => a.price_brl - b.price_brl);
          if (mounted) setListings(ls);
        } catch (e) {
          // manter ls = []
        }

        // 4) Atualizar preços do backend (agora com dados atualizados)
        try {
          const bi = await backendPromise;
          if (mounted) {
            let backendItemPriceBRL: number | null = null;
            if (bi && (bi as any).last_price_brl != null) backendItemPriceBRL = Number((bi as any).last_price_brl);
            
            // Capturar média 7d do backend, se disponível
            const avgStr = bi && (bi as any).seven_day_avg_price_brl != null ? String((bi as any).seven_day_avg_price_brl) : null;
            if (avgStr) {
              const avgNum = Number(avgStr);
              if (isFinite(avgNum) && avgNum > 0) setSevenDayAvgBRL(avgNum);
            }

            // Atualizar preço no item - usar sempre o preço do backend
            // O backend já calcula o menor preço da Immutable com markup aplicado
            if (backendItemPriceBRL != null && isFinite(backendItemPriceBRL) && backendItemPriceBRL >= 0) {
              setItem(prev => {
                if (!prev) return prev;
                // Usar sempre o preço do backend, que já vem com o menor preço da Immutable + markup
                return { ...prev, last_price_brl: backendItemPriceBRL };
              });
              
              // Também atualizar nftItem se existir
              if (bi) {
                setNftItem(bi as NFTItem);
              }
            }
          }
        } catch {
          // Ignorar erro
        }
      } catch (e: any) {
        if (mounted) {
          // Não definir erro aqui, apenas logar
          console.error('Erro ao carregar preços:', e);
        }
      } finally {
        if (mounted) setLoadingPrice(false);
      }
    })();
    
    return () => {
      mounted = false;
    };
  }, [productCode]);

  const immutableSearchUrl = useMemo(() => {
    const params = new URLSearchParams({
      status: 'active',
      // usar os mesmos parâmetros base do backend
      sell_metadata: JSON.stringify({ productCode: [productCode] }),
      order_by: 'buy_quantity',
      direction: 'asc',
      page_size: '200',
    });
    return `https://api.x.immutable.com/v3/orders?${params.toString()}`;
  }, [productCode]);

  useEffect(() => {
    // Debug logging removed; keep hook in case of future side-effects
  }, [immutableSearchUrl]);

  const displayPriceBRL = useMemo(() => {
    // Usar sempre o preço do backend (que já vem com o menor preço da Immutable + markup aplicado)
    // Isso garante consistência com o card que também usa last_price_brl do backend
    const itemBRL = typeof item?.last_price_brl === 'number' ? item.last_price_brl : null;
    return itemBRL ?? 0;
  }, [item]);

  const lowestListingBRL = useMemo(() => {
    const valid = listings.filter(l => typeof l.price_brl === 'number' && isFinite(l.price_brl) && l.price_brl > 0);
    if (!valid.length) return null;
    return valid.reduce((min, l) => (l.price_brl < min ? l.price_brl : min), valid[0].price_brl);
  }, [listings]);

  const adjustedListings = useMemo(() => {
    if (!listings.length) return [];
    const lowest = lowestListingBRL ?? 0;
    const base = displayPriceBRL ?? 0;
    if (lowest <= 0 || base <= 0) {
      return listings.map(l => ({ ...l, display_price_brl: l.price_brl }));
    }
    const scale = base / lowest;
    return listings.map(l => {
      const scaled = +(l.price_brl * scale).toFixed(2);
      return { ...l, display_price_brl: scaled };
    });
  }, [listings, lowestListingBRL, displayPriceBRL]);

  const displayListings = useMemo(() => {
    return adjustedListings.filter(
      l => typeof l.display_price_brl === 'number' && isFinite(l.display_price_brl) && l.display_price_brl > 0
    );
  }, [adjustedListings]);

  const lowestDisplayListingBRL = useMemo(() => {
    if (!displayListings.length) return null;
    return displayListings.reduce(
      (min, l) => (l.display_price_brl < min ? l.display_price_brl : min),
      displayListings[0].display_price_brl
    );
  }, [displayListings]);

  const chartData = useMemo(() => {
    // Base do gráfico alinhada ao preço exibido (prioriza menor listagem se existir, senão usa backend)
    const itemBRL = typeof item?.last_price_brl === 'number' ? item.last_price_brl : null;
    const listBRL = lowestDisplayListingBRL ?? null;
    const base = (listBRL != null) ? listBRL : (itemBRL ?? 0);
    const mk = (v: number) => +v.toFixed(2);
    const b = base > 0 ? base : 10; // fallback baseline to avoid collapsed axis
    const series = [
      { date: 'D-6', price: b ? mk(b * 0.90) : 0, volume: 12 },
      { date: 'D-5', price: b ? mk(b * 0.95) : 0, volume: 3 },
      { date: 'D-4', price: b ? mk(b * 0.92) : 0, volume: 8 },
      { date: 'D-3', price: b ? mk(b * 0.98) : 0, volume: 5 },
      { date: 'D-2', price: b ? mk(b * 1.02) : 0, volume: 10 },
      { date: 'D-1', price: b ? mk(b * 1.05) : 0, volume: 4 },
      { date: 'Hoje', price: b ? mk(b * 1.00) : 0, volume: 6 },
    ];
    return series;
  }, [item, lowestListingBRL]);

  const avgPrice = useMemo(() => {
    if (sevenDayAvgBRL != null) return +Number(sevenDayAvgBRL).toFixed(2);
    if (!chartData.length) return 0;
    const sum = chartData.reduce((s, d) => s + (d.price || 0), 0);
    return +(sum / chartData.length).toFixed(2);
  }, [chartData, sevenDayAvgBRL]);

  // SEO para página do produto NFT
  const seoTitle = useMemo(() => {
    if (item?.name) return `${item.name} - NFT Marketplace`;
    if (productCode) return `NFT ${productCode} - NFT Marketplace`;
    return undefined;
  }, [item?.name, productCode]);

  const seoDescription = useMemo(() => {
    if (item?.name) {
      const priceText = displayPriceBRL > 0 ? `Preço: R$ ${formatBRL(displayPriceBRL)}.` : '';
      const attributesText = item.attributes?.length 
        ? `Atributos: ${item.attributes.map(a => `${a.trait}: ${a.value}`).join(', ')}.`
        : '';
      return `Compre ${item.name} no NFT Marketplace. ${priceText} ${attributesText}`.trim();
    }
    if (productCode) {
      return `NFT ${productCode} disponível no NFT Marketplace. Explore e compre NFTs únicos do Habbo.`;
    }
    return undefined;
  }, [item?.name, item?.attributes, productCode, displayPriceBRL]);

  useSEO({
    title: seoTitle,
    description: seoDescription,
    image: item?.image_url || undefined,
    url: typeof window !== 'undefined' ? window.location.href : undefined,
    type: 'product',
  });

  const whatsappUrl = useMemo(() => {
    const phone = '5511987120592'; // +55 11 98712-0592
    const currentUrl = typeof window !== 'undefined' ? window.location.href : '';
    const priceText = `R$ ${formatBRL(displayPriceBRL || 0)}`;
    const msg = `Olá! Tenho interesse no item ${item?.name || productCode} (${productCode}).\nVi por ${priceText}.\nLink: ${currentUrl}`;
    return `https://wa.me/${phone}?text=${encodeURIComponent(msg)}`;
  }, [item?.name, productCode, displayPriceBRL]);

  // Generate item URL for sharing
  const itemUrl = useMemo(() => {
    return `${window.location.origin}/${slug}/${productCode}`;
  }, [slug, productCode]);

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
    if (isPurchasing) return;
    setPurchaseMessage(null);
    // Verificar autenticação
    const token = localStorage.getItem('access_token') || localStorage.getItem('token');
    if (!token) {
      setPurchaseMessage({
        type: 'error',
        text: 'Você precisa estar autenticado para comprar. Faça login primeiro.',
      });
      return;
    }

    // Buscar perfil atualizado antes de validar
    let currentUser = user;
    const now = Date.now();
    const shouldRefreshProfile = !currentUser || !profileFetchedAt || (now - profileFetchedAt) > 30_000;
    if (shouldRefreshProfile) {
      try {
        currentUser = await fetchUserProfile();
        setUser(currentUser);
        setProfileFetchedAt(Date.now());
      } catch (error) {
        setPurchaseMessage({
          type: 'error',
          text: 'Não foi possível carregar seu perfil agora. Tente novamente em instantes.',
        });
        return;
      }
    }

    // Validar perfil com dados atualizados
    const validation = validateProfile(currentUser);
    if (!validation.isValid) {
      setMissingFields(validation.missingFields);
      setIsProfileIncompleteDialogOpen(true);
      return;
    }

    // Verificar se temos o item do backend
    if (!nftItem || !nftItem.id) {
      setPurchaseMessage({
        type: 'error',
        text: 'Aguarde o carregamento completo do item antes de comprar.',
      });
      return;
    }

    setIsPurchasing(true);
    try {
      const withTimeout = <T,>(p: Promise<T>, ms = 12_000): Promise<T> =>
        Promise.race([
          p,
          new Promise<T>((_, reject) => setTimeout(() => reject(new Error('timeout')), ms)) as Promise<T>,
        ]);

      const mapPurchaseError = (err: any): string => {
        const status = err?.status;
        const msg = String(err?.message || '');
        if (msg.toLowerCase().includes('timeout')) {
          return 'A compra está demorando mais que o esperado. Tente novamente em instantes.';
        }
        if (msg.toLowerCase().includes('failed to fetch')) {
          return 'Não foi possível conectar ao servidor. Verifique sua conexão e tente novamente.';
        }
        if (status === 401) return 'Sua sessão expirou. Faça login novamente para continuar.';
        if (status === 403) return 'Você não tem permissão para realizar esta compra.';
        if (status === 400) return 'Não foi possível processar a compra. Verifique seus dados e tente novamente.';
        return msg || 'Erro ao processar compra. Tente novamente.';
      };

      // 1. Criar pedido
      const order = await withTimeout(createOrder({
        items: [
          {
            item_type: 'nft',
            item_id: nftItem.id,
            quantity: 1,
          },
        ],
        notes: `Compra do NFT: ${item?.name || productCode}`,
      }), 12_000);

      // 2. Criar cobrança na AbacatePay
      const billing = await withTimeout(createBilling({
        order_id: order.order_id,
        description: `Compra do NFT: ${item?.name || productCode}`,
        metadata: {
          product_code: productCode,
          slug: slug,
        },
      }), 12_000);

      // 3. Redirecionar para página de pagamento
      if (billing.payment_url) {
        window.open(billing.payment_url, '_blank', 'noopener,noreferrer');
        setPurchaseMessage({
          type: 'success',
          text: 'Cobrança gerada. Abrimos o pagamento em uma nova aba.',
        });
      } else {
        setPurchaseMessage({
          type: 'success',
          text: 'Cobrança criada com sucesso! Verifique seus pedidos para mais detalhes.',
        });
      }
    } catch (error: any) {
      console.error('Erro ao processar compra:', error);
      setPurchaseMessage({
        type: 'error',
        text: mapPurchaseError(error),
      });
    } finally {
      setIsPurchasing(false);
    }
  };

  return (
    <section className="bg-[#1a1a1a] text-white">
  <div className="max-w-[1800px] mx-auto flex flex-col gap-4 p-6">
        <div className="flex items-center justify-between">
          <Button onClick={onBack} className="bg-[#FFE000] hover:bg-[#FFD700] text-black">
            <ArrowLeft className="w-4 h-4 mr-2" /> Voltar
          </Button>
          {/* Removed 'Ver na Immutable' button as requested */}
        </div>

        {error && !item && !nftItem && !loadingBasicInfo ? (
          <div className="text-center text-red-500 py-10">{error}</div>
        ) : (item || nftItem) ? (
          <div className="flex flex-col lg:flex-row gap-6 scroll-smooth justify-center">
            {/* Left Column */}
            <div className="flex-[3] lg:max-h-[calc(100vh-160px)] lg:overflow-y-auto scroll-smooth space-y-4">
              <div className="rounded-xl bg-[#202020] p-4 w-full">
                <div className="relative w-full h-[70vh] rounded-lg overflow-hidden bg-black/20 flex items-center justify-center">
                  {(item?.image_url || nftItem?.image_url) ? (
                    <ImageWithFallback
                      src={item?.image_url || nftItem?.image_url || ''}
                      alt={item?.name || nftItem?.name || productCode}
                      className="max-h-full max-w-full object-contain"
                    />
                  ) : (
                    <Skeleton className="w-full h-full rounded-lg" />
                  )}
                </div>
              </div>

              <div className="rounded-xl bg-[#202020] p-4 w-full">
                <div className="flex items-center justify-between mb-3">
                  <h3 className="font-medium">Preço médio diário</h3>
                </div>
                {loadingPrice ? (
                  <div className="w-full h-[340px] space-y-3">
                    <Skeleton className="h-[260px] w-full" />
                    <div className="flex gap-2">
                      <Skeleton className="h-4 w-24" />
                      <Skeleton className="h-4 w-20" />
                      <Skeleton className="h-4 w-16" />
                    </div>
                  </div>
                ) : (
                  <div className="order-chart-wrapper w-full" style={{ width: '100%', height: 340 }}>
                    <ResponsiveContainer width="100%" height="100%">
                      <ComposedChart data={chartData} className="time-series-chart">
                      <defs>
                        <linearGradient id="priceLineGradient" x1="0" y1="0" x2="1" y2="0">
                          <stop offset="0%" stopColor="#FFE000"/>
                          <stop offset="100%" stopColor="#FFD700"/>
                        </linearGradient>
                        <linearGradient id="priceAreaGradient" x1="0" y1="0" x2="0" y2="1">
                          <stop offset="0%" stopColor="#FFE000" stopOpacity={0.25} />
                          <stop offset="100%" stopColor="#FFE000" stopOpacity={0} />
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
                          if (name === 'Preço') return [`R$ ${formatBRL(Number(val))}`, 'Preço'];
                          if (name === 'Volume') return [String(val), 'Volume'];
                          return [String(val), name];
                        }}
                      />
                      <Legend verticalAlign="top" align="right" wrapperStyle={{ right: 8, top: 0, color: '#cbd5e1' }} />
                      <Bar name="Volume" yAxisId="volume" dataKey="volume" barSize={10} fill="url(#volumeBarGradient)" radius={[6, 6, 0, 0]} />
                      <Line name="Preço" type="monotone" dataKey="price" stroke="url(#priceLineGradient)" strokeWidth={2.5} dot={{ r: 2.2, stroke: '#FFE000', fill: '#FFE000' }} activeDot={{ r: 4 }} />
                      {avgPrice > 0 && (
                        <ReferenceLine y={avgPrice} stroke="#f59e0b" strokeDasharray="6 6" ifOverflow="extendDomain" label={{ value: 'média', position: 'right', fill: '#f59e0b', fontSize: 11 }} />
                      )}
                      </ComposedChart>
                    </ResponsiveContainer>
                  </div>
                )}
              </div>
            </div>

            {/* Right Column */}
            <div className="flex-[2] lg:max-h-[calc(100vh-160px)] lg:overflow-y-auto scroll-smooth space-y-4">
              {/* Header Card */}
              <div className="rounded-xl bg-[#202020] p-4 w-full">
                <div className="flex items-start justify-between gap-4">
                  <div>
                    {(item?.name || nftItem?.name) ? (
                      <h1 className="text-2xl lg:text-3xl font-bold">{item?.name || nftItem?.name || productCode}</h1>
                    ) : (
                      <Skeleton className="h-7 w-64 mb-2" />
                    )}
                    <div className="mt-1 text-sm text-gray-400">
                      {loadingPrice ? (
                        <Skeleton className="h-3 w-24 inline-block" />
                      ) : (
                        `${listings.length} listados`
                      )}
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    {/* Histórico de vendas removido por solicitação */}
                    <Button size="sm" variant="outline" className="h-9 w-9 p-0"><Heart className="w-4 h-4" /></Button>
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
              </div>

              {/* Action Panel */}
              <div className="rounded-xl bg-[#202020] p-4 w-full">
                <Tabs defaultValue="buy">
                  <TabsContent value="buy" className="mt-1 space-y-4">
                    <div className="grid grid-cols-1 gap-3">
                    <div className="rounded-lg bg-black/20 p-3 text-center">
                      <div className="text-xs text-gray-400">Preço</div>
                      {loadingPrice ? (
                        <Skeleton className="h-7 w-32 mx-auto mt-1" />
                      ) : (
                        <>
                          <div className="text-xl font-bold text-[#FFE000]">R$ {formatBRL(displayPriceBRL)}</div>
                          {displayPriceBRL > 100 && (
                            <div className="mt-1 text-[11px] text-gray-300 flex items-center justify-center gap-1">
                              <span>
                                3x de R$ {formatBRL((displayPriceBRL / 3))}
                              </span>
                              <UITooltip>
                                <UITooltipTrigger asChild>
                                  <span className="inline-flex items-center justify-center align-middle">
                                    <Info className="w-3.5 h-3.5 text-gray-400 hover:text-gray-300 cursor-help" />
                                  </span>
                                </UITooltipTrigger>
                                <UITooltipContent sideOffset={6} className="bg-black text-white border border-white/20">
                                  Para parcelamento, chame no WhatsApp para mais informações.
                                </UITooltipContent>
                              </UITooltip>
                            </div>
                          )}
                        </>
                      )}
                    </div>
                    </div>
                    {/* Quantity and currency controls removed as requested */}
                    <div className="grid grid-cols-2 gap-3">
                      <Button 
                        onClick={handlePurchase}
                        disabled={isPurchasing || !nftItem || loadingPrice}
                        className="bg-[#FFE000] text-black h-11 text-base hover:bg-[#FFD700] disabled:opacity-60 disabled:cursor-not-allowed"
                      >
                        <ShoppingCart className="w-5 h-5 mr-2" />
                        {isPurchasing ? 'Processando...' : 'Comprar'}
                      </Button>
                      <Button 
                        onClick={() => window.open(whatsappUrl, '_blank', 'noopener,noreferrer')} 
                        disabled={loadingPrice}
                        variant="outline" 
                        className="h-11 text-base border-[#25D366]/50 text-[#25D366] hover:bg-[#25D366]/10 disabled:opacity-60"
                      >
                        <MessageCircle className="w-5 h-5 mr-2" /> WhatsApp
                      </Button>
                    </div>
                    {purchaseMessage && (
                      <div
                        className={`rounded-md px-3 py-2 text-sm ${
                          purchaseMessage.type === 'success'
                            ? 'bg-emerald-500/10 text-emerald-300 border border-emerald-500/30'
                            : 'bg-red-500/10 text-red-300 border border-red-500/30'
                        }`}
                      >
                        {purchaseMessage.text}
                      </div>
                    )}
                  </TabsContent>
                </Tabs>
              </div>

              {/* Tabela À venda */}
              <div className="rounded-xl bg-[#202020] p-4 w-full">
                <h3 className="font-medium mb-3">À venda</h3>
                <div className="grid grid-cols-4 gap-2 text-xs text-gray-400 px-2 py-2 font-medium">
                  <div>Preço</div>
                  <div>Qtd</div>
                  <div className="hidden sm:block">Expira em</div>
                  <div className="hidden sm:block">Comprar</div>
                </div>
                {loadingPrice ? (
                  <div className="space-y-2 max-h-80 overflow-y-auto">
                    {[...Array(3)].map((_, i) => (
                      <div key={i} className="grid grid-cols-4 gap-2 items-center p-3 bg-black/20 rounded-lg">
                        <Skeleton className="h-4 w-24" />
                        <Skeleton className="h-4 w-8" />
                        <Skeleton className="h-4 w-24 hidden sm:block" />
                        <div className="hidden sm:block text-right">
                          <Skeleton className="h-8 w-20 ml-auto" />
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="space-y-2 max-h-80 overflow-y-auto">
                    {displayListings.map((l) => (
                      <div key={l.id} className="grid grid-cols-4 gap-2 items-center p-3 bg-black/20 rounded-lg">
                        <div className="font-medium text-[#FFE000]">R$ {formatBRL(l.display_price_brl)}</div>
                        <div>{l.quantity}</div>
                        <div className="hidden sm:block text-xs text-gray-400">{l.expiration ? new Date(l.expiration).toLocaleDateString('pt-BR') : '—'}</div>
                        <div className="hidden sm:block text-right">
                          <Button disabled size="sm" variant="outline" className="h-8 px-3 opacity-60 cursor-not-allowed">Comprar</Button>
                        </div>
                      </div>
                    ))}
                    {displayListings.length === 0 && (
                      <div className="text-center text-sm text-gray-400 py-6">Sem anúncios ativos para este item.</div>
                    )}
                  </div>
                )}
              </div>

              {/* Offers removed as requested */}

              {/* Atributos */}
              {item?.attributes && item.attributes.length > 0 && (
                <div className="rounded-xl bg-[#202020] p-4 w-full">
                  <h3 className="font-medium mb-3">Atributos</h3>
                  <div className="grid grid-cols-2 gap-3">
                    {item.attributes.map((attr, idx) => (
                      <div key={idx} className="bg-black/20 rounded-lg p-3 border border-white/5">
                        <div className="text-xs text-gray-400 mb-1">{attr.trait}</div>
                        <div className="text-sm font-medium truncate" title={attr.value}>{attr.value}</div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </div>
        ) : null}
      </div>
      
      {/* Share Modal */}
      <ShareModal
        isOpen={isShareModalOpen}
        onClose={() => setIsShareModalOpen(false)}
        collectionName={item?.name || nftItem?.name || productCode}
        collectionUrl={itemUrl}
      />

      {/* Profile Incomplete Dialog */}
      <AlertDialog open={isProfileIncompleteDialogOpen} onOpenChange={setIsProfileIncompleteDialogOpen}>
        <AlertDialogContent className="bg-[#202020] border-white/10 text-white">
          <AlertDialogHeader>
            <AlertDialogTitle className="flex items-center gap-2 text-[#FFE000]">
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
                <li key={field} className="text-gray-300">{field}</li>
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
              className="bg-[#FFE000] text-black hover:bg-[#FFD700]"
              onClick={() => {
                setIsProfileIncompleteDialogOpen(false);
                // Redirecionar para página de configurações
                window.location.href = '/configuracoes';
              }}
            >
              Completar Perfil
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </section>
  );
}
