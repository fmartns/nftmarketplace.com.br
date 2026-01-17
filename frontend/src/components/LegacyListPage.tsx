import { useEffect, useState } from 'react';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Card, CardContent } from './ui/card';
import { Separator } from './ui/separator';
import { Search, Grid3X3, List, X } from 'lucide-react';
import { NFTCard } from './NFTCard';
import { fetchLegacyItems, type LegacyItem } from '@/api/legacy';
import { Skeleton } from './ui/skeleton';
import { Label } from './ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from './ui/select';

type OrderingOption = 
  | 'name' 
  | '-name' 
  | 'last_price' 
  | '-last_price' 
  | 'average_price' 
  | '-average_price' 
  | 'available_offers' 
  | '-available_offers' 
  | 'created_at' 
  | '-created_at' 
  | 'updated_at' 
  | '-updated_at';

const orderingOptions: { value: OrderingOption; label: string }[] = [
  { value: 'name', label: 'Nome (A-Z)' },
  { value: '-name', label: 'Nome (Z-A)' },
  { value: 'last_price', label: 'Preço (Menor)' },
  { value: '-last_price', label: 'Preço (Maior)' },
  { value: 'average_price', label: 'Preço Médio (Menor)' },
  { value: '-average_price', label: 'Preço Médio (Maior)' },
  { value: 'available_offers', label: 'Ofertas (Menor)' },
  { value: '-available_offers', label: 'Ofertas (Maior)' },
  { value: 'created_at', label: 'Mais Antigo' },
  { value: '-created_at', label: 'Mais Recente' },
  { value: 'updated_at', label: 'Atualizado (Antigo)' },
  { value: '-updated_at', label: 'Atualizado (Recent)' },
];

export function LegacyListPage() {
  const [viewMode, setViewMode] = useState<'grid' | 'list'>('grid');
  const [searchQuery, setSearchQuery] = useState('');
  const [slugQuery, setSlugQuery] = useState('');
  const [priceRange, setPriceRange] = useState({ min: '', max: '' });
  const [minOffers, setMinOffers] = useState('');
  const [ordering, setOrdering] = useState<OrderingOption>('name');
  const [items, setItems] = useState<LegacyItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [page, setPage] = useState(1);
  const [hasMore, setHasMore] = useState(true);
  const [totalCount, setTotalCount] = useState(0);

  // Reset pagination when filters change
  useEffect(() => {
    setPage(1);
    setItems([]);
  }, [searchQuery, slugQuery, priceRange.min, priceRange.max, minOffers, ordering]);

  // Fetch items from backend
  useEffect(() => {
    let mounted = true;
    (async () => {
      try {
        setLoading(true);
        setError(null);
        const params: any = { page_size: 12, page, ordering };
        
        if (searchQuery.trim()) params.name = searchQuery.trim();
        if (slugQuery.trim()) params.slug = slugQuery.trim();
        if (priceRange.min) params.min_price = parseFloat(priceRange.min);
        if (priceRange.max) params.max_price = parseFloat(priceRange.max);
        if (minOffers) params.min_offers = parseInt(minOffers);
        
        const res = await fetchLegacyItems(params);
        if (!mounted) return;
        const nextItems = res.results || [];
        setItems(prev => page === 1 ? nextItems : [...prev, ...nextItems]);
        setHasMore(Boolean(res.next));
        setTotalCount(res.count || 0);
      } catch (e: any) {
        if (!mounted) return;
        setError('Falha ao carregar itens');
        console.error('Erro ao buscar itens:', e);
      } finally {
        if (mounted) setLoading(false);
      }
    })();
    return () => { mounted = false; };
  }, [page, searchQuery, slugQuery, priceRange.min, priceRange.max, minOffers, ordering]);

  const goToItem = (item: LegacyItem) => {
    const to = `/legacy/${item.slug}`;
    if (window.location.pathname !== to) {
      window.history.pushState({}, '', to);
      window.scrollTo({ top: 0, behavior: 'smooth' });
      window.dispatchEvent(new PopStateEvent('popstate'));
    }
  };

  const clearAllFilters = () => {
    setSearchQuery('');
    setSlugQuery('');
    setPriceRange({ min: '', max: '' });
    setMinOffers('');
    setOrdering('name');
  };

  const hasActiveFilters = searchQuery || slugQuery || priceRange.min || priceRange.max || minOffers || ordering !== 'name';

  const formatPrice = (price: number) => {
    return price.toLocaleString('pt-BR', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
  };

  return (
    <section className="py-8 lg:py-16 bg-background">
      <div className="container mx-auto px-4 lg:px-8">
        {/* Header */}
        <div className="text-center mb-8">
          <h2 className="text-3xl lg:text-4xl font-bold mb-4">
            Explore os <span className="text-[#FFE000]">Itens Legacy</span>
          </h2>
          <p className="text-lg text-muted-foreground max-w-2xl mx-auto">
            Descubra todos os itens Legacy disponíveis
          </p>
        </div>

        <div className="grid lg:grid-cols-4 gap-8">
          {/* Sidebar com Filtros */}
          <div className="lg:col-span-1">
            <Card className="bg-card/50 backdrop-blur border-border/40 sticky top-24">
              <CardContent className="p-6">
                <div className="space-y-6">
                  <div className="flex items-center justify-between mb-4">
                    <h3 className="text-lg font-semibold">Filtros</h3>
                    {hasActiveFilters && (
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={clearAllFilters}
                        className="h-8 px-2 text-xs"
                      >
                        <X className="w-3 h-3 mr-1" />
                        Limpar
                      </Button>
                    )}
                  </div>

                  {/* Search */}
                  <div>
                    <Label htmlFor="search" className="text-sm font-medium mb-2 block">Busca Geral</Label>
                    <div className="relative">
                      <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-muted-foreground h-4 w-4" />
                      <Input
                        id="search"
                        placeholder="Buscar por nome..."
                        value={searchQuery}
                        onChange={(e) => setSearchQuery(e.target.value)}
                        className="pl-10 bg-muted/30 border-border/40"
                      />
                    </div>
                  </div>

                  {/* Slug Search */}
                  <div>
                    <Label htmlFor="slug" className="text-sm font-medium mb-2 block">Slug</Label>
                    <div className="relative">
                      <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-muted-foreground h-4 w-4" />
                      <Input
                        id="slug"
                        placeholder="Buscar por slug..."
                        value={slugQuery}
                        onChange={(e) => setSlugQuery(e.target.value)}
                        className="pl-10 bg-muted/30 border-border/40"
                      />
                    </div>
                  </div>

                  <Separator className="border-border/40" />

                  {/* Price Range */}
                  <div>
                    <Label className="text-sm font-medium mb-3 block text-[#FFE000]">Preço (R$)</Label>
                    <div className="grid grid-cols-2 gap-2">
                      <div>
                        <Label htmlFor="min_price" className="text-xs text-muted-foreground mb-1 block">Mínimo</Label>
                        <Input
                          id="min_price"
                          placeholder="0.00"
                          type="number"
                          step="0.01"
                          min="0"
                          value={priceRange.min}
                          onChange={(e) => setPriceRange(prev => ({ ...prev, min: e.target.value }))}
                          className="bg-muted/30 border-border/40 text-sm"
                        />
                      </div>
                      <div>
                        <Label htmlFor="max_price" className="text-xs text-muted-foreground mb-1 block">Máximo</Label>
                        <Input
                          id="max_price"
                          placeholder="9999.99"
                          type="number"
                          step="0.01"
                          min="0"
                          value={priceRange.max}
                          onChange={(e) => setPriceRange(prev => ({ ...prev, max: e.target.value }))}
                          className="bg-muted/30 border-border/40 text-sm"
                        />
                      </div>
                    </div>
                  </div>

                  <Separator className="border-border/40" />

                  {/* Min Offers */}
                  <div>
                    <Label htmlFor="min_offers" className="text-sm font-medium mb-2 block">Ofertas Mínimas</Label>
                    <Input
                      id="min_offers"
                      placeholder="Ex: 1"
                      type="number"
                      min="0"
                      value={minOffers}
                      onChange={(e) => setMinOffers(e.target.value)}
                      className="bg-muted/30 border-border/40"
                    />
                    <p className="text-xs text-muted-foreground mt-1">
                      Mostrar apenas itens com pelo menos X ofertas
                    </p>
                  </div>

                  <Separator className="border-border/40" />

                  {/* Ordering */}
                  <div>
                    <Label htmlFor="ordering" className="text-sm font-medium mb-2 block">Ordenar por</Label>
                    <Select value={ordering} onValueChange={(value) => setOrdering(value as OrderingOption)}>
                      <SelectTrigger id="ordering" className="bg-muted/30 border-border/40">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        {orderingOptions.map((option) => (
                          <SelectItem key={option.value} value={option.value}>
                            {option.label}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Main Content */}
          <div className="lg:col-span-3">
            {/* Toolbar */}
            <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 mb-8">
              <div className="flex items-center space-x-4">
                <span className="text-sm text-muted-foreground">
                  {totalCount > 0 ? `${totalCount} item${totalCount !== 1 ? 's' : ''} encontrado${totalCount !== 1 ? 's' : ''}` : 'Nenhum item encontrado'}
                </span>
                {hasActiveFilters && (
                  <span className="text-xs text-[#FFE000] bg-[#FFE000]/10 px-2 py-1 rounded">
                    Filtros ativos
                  </span>
                )}
              </div>

              <div className="flex items-center space-x-2">
                <div className="flex items-center space-x-1 bg-muted/30 rounded-lg p-1">
                  <Button
                    size="sm"
                    variant={viewMode === 'grid' ? 'default' : 'ghost'}
                    className={viewMode === 'grid' ? 'bg-[#FFE000] text-black hover:bg-[#FFD700]' : ''}
                    onClick={() => setViewMode('grid')}
                  >
                    <Grid3X3 className="w-4 h-4" />
                  </Button>
                  <Button
                    size="sm"
                    variant={viewMode === 'list' ? 'default' : 'ghost'}
                    className={viewMode === 'list' ? 'bg-[#FFE000] text-black hover:bg-[#FFD700]' : ''}
                    onClick={() => setViewMode('list')}
                  >
                    <List className="w-4 h-4" />
                  </Button>
                </div>
              </div>
            </div>

            {/* Items Grid */}
            {loading && page === 1 ? (
              <div className={`grid gap-6 ${viewMode === 'grid' ? 'grid-cols-1 sm:grid-cols-2 lg:grid-cols-3' : 'grid-cols-1'}`}>
                {Array.from({ length: 12 }).map((_, i) => (
                  <Skeleton key={i} className="h-72 w-full rounded-xl" />
                ))}
              </div>
            ) : items.length > 0 ? (
              <div className={`grid gap-6 ${
                viewMode === 'grid' 
                  ? 'grid-cols-1 sm:grid-cols-2 lg:grid-cols-3' 
                  : 'grid-cols-1'
              }`}>
                {items.map((item) => (
                  <div key={item.id}>
                    <NFTCard
                      id={String(item.id)}
                      name={item.name}
                      image={item.image_url}
                      price={formatPrice(item.last_price)}
                      collection="Legacy"
                      onClick={() => goToItem(item)}
                    />
                  </div>
                ))}
              </div>
            ) : (
              <Card className="p-12 text-center">
                <div className="flex justify-center mb-4">
                  <Search className="w-14 h-14 text-[#FFE000]" />
                </div>
                <h3 className="text-xl font-semibold mb-2">Nenhum item encontrado</h3>
                <p className="text-muted-foreground mb-4">
                  {hasActiveFilters 
                    ? 'Tente ajustar seus filtros para encontrar mais resultados'
                    : 'Não há itens disponíveis no momento'}
                </p>
                {hasActiveFilters && (
                  <Button
                    onClick={clearAllFilters}
                    className="bg-[#FFE000] hover:bg-[#FFD700] text-black"
                  >
                    Limpar Filtros
                  </Button>
                )}
              </Card>
            )}

            {/* Load More */}
            {!loading && hasMore && (
              <div className="text-center mt-12">
                <Button 
                  size="lg" 
                  variant="outline"
                  onClick={() => setPage(p => p + 1)}
                  className="border-[#FFE000]/30 hover:bg-[#FFE000]/10 hover:border-[#FFE000]/50"
                >
                  Carregar Mais Items
                </Button>
              </div>
            )}
          </div>
        </div>
      </div>
    </section>
  );
}


