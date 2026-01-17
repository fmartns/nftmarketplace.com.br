import { useEffect, useState } from 'react';
import { Button } from './ui/button';
import { Badge } from './ui/badge';
import { ArrowRight, TrendingUp, Users, Zap } from 'lucide-react';
import { ImageWithFallback } from './figma/ImageWithFallback';
import { fetchNFTItems, type NFTItem } from '@/api/nft';
import { Skeleton } from './ui/skeleton';

export function HeroSection() {
  const [featured, setFeatured] = useState<NFTItem | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let mounted = true;
    (async () => {
      try {
        setLoading(true);
        // Fetch a small batch and pick one at random each page load
        const batch = await fetchNFTItems({ ordering: '-updated_at', page_size: 24 });
        if (!mounted) return;
        const list = batch.results || [];
        if (list.length > 0) {
          const idx = Math.floor(Math.random() * list.length);
          setFeatured(list[idx]);
        } else {
          const top = await fetchNFTItems({ ordering: '-last_price_brl', page_size: 1 });
          if (!mounted) return;
          setFeatured(top.results?.[0] || null);
        }
      } catch (e) {
        if (!mounted) return;
        setFeatured(null);
      } finally {
        if (mounted) setLoading(false);
      }
    })();
    return () => { mounted = false; };
  }, []);

  const goToFeatured = () => {
    if (!featured) return;
    if (featured.collection_slug && featured.product_code) {
      const to = `/${featured.collection_slug}/${featured.product_code}`;
      if (window.location.pathname !== to) {
        window.history.pushState({}, '', to);
        window.scrollTo({ top: 0, behavior: 'smooth' });
        window.dispatchEvent(new PopStateEvent('popstate'));
      }
    }
  };
  return (
    <section className="relative overflow-hidden bg-background">
      {/* Background Pattern */}
      <div className="absolute inset-0 bg-grid-pattern opacity-5"></div>
      
      <div className="container mx-auto px-4 lg:px-8 py-16 lg:py-24">
        <div className="grid lg:grid-cols-2 gap-12 items-center">
          {/* Content */}
          <div className="space-y-8">
            <div className="space-y-6">
              <Badge className="bg-[#FFE000] text-black border-0 w-fit">
                <Zap className="w-3 h-3 mr-1" />
                Marketplace Habbo Brasil
              </Badge>
              
              <h1 className="text-4xl lg:text-6xl font-bold leading-tight">
                Descubra e Compre{' '}
                <span className="text-[#FFE000]">
                  Items Raros
                </span>
                {' '}em Real (BRL)
              </h1>
              
              <p className="text-lg text-muted-foreground max-w-lg">
                Compre itens do Habbo direto em Real. Explore 
                mobis raros, pets exclusivos e acessórios únicos.
              </p>
            </div>

            <div className="flex flex-col sm:flex-row gap-4">
              <Button 
                size="lg" 
                className="bg-[#FFE000] hover:bg-[#FFD700] text-black border-0"
              >
                Explorar Items
                <ArrowRight className="w-4 h-4 ml-2" />
              </Button>
            </div>

            {/* Stats */}
            <div className="grid grid-cols-3 gap-6 pt-8">
              <div className="text-center sm:text-left">
                <div className="flex items-center justify-center sm:justify-start space-x-2 text-[#FFE000] mb-1">
                  <TrendingUp className="w-4 h-4" />
                  <span className="text-2xl font-bold">15K+</span>
                </div>
                <p className="text-sm text-muted-foreground">Itens Únicos</p>
              </div>
              <div className="text-center sm:text-left">
                <div className="flex items-center justify-center sm:justify-start space-x-2 text-[#FFE000] mb-1">
                  <Users className="w-4 h-4" />
                  <span className="text-2xl font-bold">8K+</span>
                </div>
                <p className="text-sm text-muted-foreground">Habbos Ativos</p>
              </div>
              <div className="text-center sm:text-left">
                <div className="flex items-center justify-center sm:justify-start space-x-2 text-[#FFE000] mb-1">
                  <Zap className="w-4 h-4" />
                  <span className="text-2xl font-bold">25K+</span>
                </div>
                <p className="text-sm text-muted-foreground">Transações</p>
              </div>
            </div>
          </div>

          {/* Featured NFT */}
          <div className="relative">
            <div className="relative max-w-md mx-auto lg:max-w-none">
              {/* Floating elements */}
              <div className="absolute -top-4 -right-4 w-20 h-20 bg-[#FFE000] rounded-2xl opacity-20 animate-pulse"></div>
              <div className="absolute -bottom-8 -left-8 w-32 h-32 bg-[#FFE000] rounded-full opacity-10 animate-pulse"></div>
              
              {/* Main NFT Card */}
              <div className="relative bg-card/80 backdrop-blur rounded-2xl p-6 border border-border/40 shadow-2xl">
                {loading ? (
                  <div className="space-y-4">
                    <Skeleton className="w-full h-64 rounded-xl" />
                    <Skeleton className="h-6 w-2/3" />
                    <div className="flex items-center justify-between">
                      <Skeleton className="h-6 w-24" />
                      <Skeleton className="h-9 w-28" />
                    </div>
                  </div>
                ) : featured ? (
                  <div className="space-y-4">
                    <ImageWithFallback
                      src={featured.image_url || ''}
                      alt={featured.name}
                      className="w-full h-64 object-cover rounded-xl"
                    />
                    
                    <div className="space-y-3">
                      <div className="flex items-center justify-between">
                        <h3 className="font-semibold line-clamp-1">{featured.name}</h3>
                        <Badge className="bg-[#FFE000]/20 text-[#FFE000] border-[#FFE000]/30">
                          {featured.rarity || 'Item'}
                        </Badge>
                      </div>
                      
                      <div className="flex items-center justify-between">
                        <div>
                          <p className="text-sm text-muted-foreground">Preço atual</p>
                          <p className="font-bold text-[#FFE000]">
                            R$ {Number(featured.last_price_brl || 0).toLocaleString('pt-BR', { minimumFractionDigits: 2 })}
                          </p>
                        </div>
                        <Button size="sm" className="bg-[#FFE000] hover:bg-[#FFD700] text-black border-0" onClick={goToFeatured}>
                          Ver Detalhes
                        </Button>
                      </div>
                    </div>
                  </div>
                ) : (
                  <div className="space-y-2 text-center text-muted-foreground">
                    <p>Não há item em destaque no momento.</p>
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}