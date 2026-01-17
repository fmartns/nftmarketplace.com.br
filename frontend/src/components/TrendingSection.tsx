import { useEffect, useState } from 'react';
import { Button } from './ui/button';
import { Badge } from './ui/badge';
import { TrendingUp } from 'lucide-react';
import { NFTCard } from './NFTCard';
import { type NFTItem, fetchTrendingByAccess } from '@/api/nft';
import { Skeleton } from './ui/skeleton';

export function TrendingSection() {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [trending, setTrending] = useState<NFTItem[]>([]);

  useEffect(() => {
    let mounted = true;
    (async () => {
      try {
        setLoading(true);
        setError(null);
        const t = await fetchTrendingByAccess({ limit: 4 });
        if (!mounted) return;
        setTrending(t.results || []);
      } catch (e) {
        if (!mounted) return;
        setError('Falha ao carregar itens em tendência');
      } finally {
        if (mounted) setLoading(false);
      }
    })();
    return () => { mounted = false; };
  }, []);

  const toCardProps = (item: NFTItem) => ({
    id: String(item.id),
    name: item.name,
    image: item.image_url,
    price: Number(item.last_price_brl || 0).toLocaleString('pt-BR', { minimumFractionDigits: 2 }),
    collection: item.collection_name || undefined,
    rarity: item.rarity || undefined,
    priceChange: item.seven_day_price_change_pct ? parseFloat(item.seven_day_price_change_pct) : 0,
    volume7d: `R$ ${Number(item.seven_day_volume_brl || 0).toLocaleString('pt-BR', { minimumFractionDigits: 2 })}`,
    onClick: () => {
      if (item.collection_slug && item.product_code) {
        const to = `/${item.collection_slug}/${item.product_code}`;
        if (window.location.pathname !== to) {
          window.history.pushState({}, '', to);
          window.scrollTo({ top: 0, behavior: 'smooth' });
          window.dispatchEvent(new PopStateEvent('popstate'));
        }
      }
    }
  });

  const renderGrid = (items: NFTItem[]) => (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
      {items.map((it) => (
        <div key={it.id}>
          <NFTCard {...toCardProps(it)} />
        </div>
      ))}
    </div>
  );

  const renderSkeletons = (n = 8) => (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
      {Array.from({ length: n }).map((_, i) => (
        <div key={i} className="space-y-3">
          <Skeleton className="w-full h-48" />
          <Skeleton className="h-5 w-3/4" />
          <Skeleton className="h-4 w-1/2" />
          <Skeleton className="h-6 w-1/3" />
        </div>
      ))}
    </div>
  );

  return (
    <section className="py-16 lg:py-24 bg-background">
      <div className="container mx-auto px-4 lg:px-8">
        <div className="text-center space-y-4 mb-12">
          <Badge className="bg-[#FFE000] text-black border-0 w-fit mx-auto">
            <TrendingUp className="w-3 h-3 mr-1" />
            Em Destaque
          </Badge>
          <h2 className="text-3xl lg:text-4xl font-bold">
            Items em <span className="text-[#FFE000]">Tendência</span>
          </h2>
          <p className="text-lg text-muted-foreground max-w-2xl mx-auto">
            Descubra os itens mais populares e valiosos do universo Habbo
          </p>
        </div>

        {loading ? renderSkeletons() : error ? (
          <p className="text-center text-muted-foreground">{error}</p>
        ) : renderGrid(trending)}

        <div className="text-center mt-12">
          <Button 
            size="lg" 
            variant="outline"
            className="border-[#FFE000]/30 hover:bg-[#FFE000]/10 hover:border-[#FFE000]/50"
            onClick={() => {
              const to = '/collections';
              if (window.location.pathname !== to) {
                window.history.pushState({}, '', to);
                window.scrollTo({ top: 0, behavior: 'smooth' });
                window.dispatchEvent(new PopStateEvent('popstate'));
              }
            }}
          >
            Ver Mais Items
          </Button>
        </div>
      </div>
    </section>
  );
}