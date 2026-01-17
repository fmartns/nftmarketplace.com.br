import { useEffect, useState } from 'react';
import { fetchNFTItems, type NFTItem } from '@/api/nft';
import { NFTCard } from './NFTCard';

export function PromotionsPage() {
  const [items, setItems] = useState<NFTItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Local navigation helper (same pattern used in Header)
  const goTo = (to: string) => {
    const target = to.startsWith('/') ? to : `/${to}`;
    if (window.location.pathname !== target) {
      window.history.pushState({}, '', target);
      window.scrollTo({ top: 0, behavior: 'smooth' });
      window.dispatchEvent(new PopStateEvent('popstate'));
    }
  };

  useEffect(() => {
    let mounted = true;
    (async () => {
      try {
        setLoading(true);
        const res = await fetchNFTItems({ promo_only: 1, ordering: '-updated_at', page_size: 60 });
        if (mounted) setItems(res.results || []);
      } catch (e: any) {
        if (mounted) setError('Falha ao carregar promoções');
      } finally {
        if (mounted) setLoading(false);
      }
    })();
    return () => { mounted = false; };
  }, []);

  return (
    <div className="container mx-auto px-4 lg:px-8 py-8 lg:py-12">
      <div className="mb-6">
        <h1 className="text-3xl font-bold">Promoções</h1>
        <p className="text-muted-foreground">Itens com margem inferior à margem padrão</p>
      </div>

      {error && <div className="text-red-500 mb-4">{error}</div>}

      {loading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
          {Array.from({ length: 8 }).map((_, i) => (
            <div key={i} className="h-64 bg-muted/20 rounded-lg animate-pulse" />
          ))}
        </div>
      ) : items.length === 0 ? (
        <div className="text-muted-foreground">
          Nenhum item em promoção no momento.
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
          {items.map((it) => (
            <div key={it.id}>
              <NFTCard
                id={String(it.id)}
                name={it.name || it.product_code || 'NFT'}
                image={it.image_url || ''}
                price={Number(it.last_price_brl || 0).toLocaleString('pt-BR', { minimumFractionDigits: 2 })}
                collection={it.collection_name || it.collection_slug || ''}
                onClick={() => {
                  if (it.collection_slug && it.product_code) {
                    goTo(`/${it.collection_slug}/${it.product_code}`);
                  } else if (it.collection_slug) {
                    goTo(`/${it.collection_slug}`);
                  }
                }}
              />
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
