import { useEffect, useMemo, useRef, useState, useCallback } from 'react';
import { CollectionBanner } from './CollectionBanner';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Badge } from './ui/badge';
import { Card, CardContent } from './ui/card';
import { Separator } from './ui/separator';
import { NFTCard } from './NFTCard';
import { NFTDetailModal } from './NFTDetailModal';
import { Drawer, DrawerContent, DrawerHeader, DrawerTitle, DrawerTrigger, DrawerClose } from './ui/drawer';
import { ArrowLeft, Search, Grid3X3, List, ShoppingCart, Trash2, Filter, X } from 'lucide-react';
import { fetchCollectionDetail, fetchNFTItems, NftCollection, Paginated, NFTItem } from '@/api/nft';

interface CollectionDetailSectionProps {
  collectionId: string; // now treated as slug
  onBack: () => void;
}

// Baseado no model NFTItem do Django
const rarityOptions = [
  { id: 'comum', name: 'Comum', color: 'bg-gray-500' },
  { id: 'incomum', name: 'Incomum', color: 'bg-green-500' },
  { id: 'raro', name: 'Raro', color: 'bg-blue-500' },
  { id: 'epico', name: 'Épico', color: 'bg-purple-500' },
  { id: 'lendario', name: 'Lendário', color: 'bg-yellow-500' },
  { id: 'ultra-raro', name: 'Ultra Raro', color: 'bg-red-500' }
];

const itemTypeOptions = [
  { id: 'mobilia', name: 'Mobília' },
  { id: 'decoracao', name: 'Decoração' },
  { id: 'pets', name: 'Pets' },
  { id: 'wallpaper', name: 'Papel de Parede' },
  { id: 'piso', name: 'Piso' },
  { id: 'efeitos', name: 'Efeitos' },
  { id: 'badge', name: 'Badge' },
];

const itemSubTypeOptions = [
  { id: 'cadeira', name: 'Cadeira', parent: 'mobilia' },
  { id: 'mesa', name: 'Mesa', parent: 'mobilia' },
  { id: 'cama', name: 'Cama', parent: 'mobilia' },
  { id: 'sofa', name: 'Sofá', parent: 'mobilia' },
  { id: 'estante', name: 'Estante', parent: 'mobilia' },
  { id: 'luminaria', name: 'Luminária', parent: 'decoracao' },
  { id: 'quadro', name: 'Quadro', parent: 'decoracao' },
  { id: 'planta', name: 'Planta', parent: 'decoracao' },
  { id: 'tapete', name: 'Tapete', parent: 'decoracao' },
];

const materialOptions = [
  { id: 'madeira', name: 'Madeira' },
  { id: 'metal', name: 'Metal' },
  { id: 'tecido', name: 'Tecido' },
  { id: 'plastico', name: 'Plástico' },
  { id: 'vidro', name: 'Vidro' },
  { id: 'cristal', name: 'Cristal' },
  { id: 'ouro', name: 'Ouro' },
  { id: 'prata', name: 'Prata' },
];

const sourceOptions = [
  { id: 'catalogo', name: 'Catálogo' },
  { id: 'evento', name: 'Evento Especial' },
  { id: 'limitado', name: 'Edição Limitada' },
  { id: 'raro', name: 'Achado Raro' },
  { id: 'exclusivo', name: 'Exclusivo' },
  { id: 'seasonal', name: 'Sazonal' },
];

function formatPriceBRL(value: string | number | null | undefined) {
  const num = Number(value || 0);
  return num.toLocaleString('pt-BR', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}

export function CollectionDetailSection({ collectionId, onBack }: CollectionDetailSectionProps) {
  // Chave única para o sessionStorage baseada no collectionId
  const storageKey = `collection_${collectionId}_state`;
  const scrollKey = `collection_${collectionId}_scroll`;

  // Função para carregar estado do sessionStorage
  const loadState = () => {
    try {
      const saved = sessionStorage.getItem(storageKey);
      if (saved) {
        return JSON.parse(saved);
      }
    } catch (e) {
      console.warn('Erro ao carregar estado do sessionStorage:', e);
    }
    return null;
  };

  // Carregar estado inicial do sessionStorage
  const savedState = loadState();
  const [viewMode, setViewMode] = useState<'grid' | 'list'>(savedState?.viewMode || 'grid');
  const [sortBy, setSortBy] = useState(savedState?.sortBy || 'price_low');
  const [filterRarity, setFilterRarity] = useState(savedState?.filterRarity || 'all');
  const [searchQuery, setSearchQuery] = useState(savedState?.searchQuery || '');
  const [selectedItems, setSelectedItems] = useState<string[]>(savedState?.selectedItems || []);
  const [priceRange, setPriceRange] = useState(savedState?.priceRange || { min: '', max: '' });
  const [showSelectedOnly, setShowSelectedOnly] = useState(savedState?.showSelectedOnly || false);
  const [selectedItemType, setSelectedItemType] = useState(savedState?.selectedItemType || 'all');
  const [selectedItemSubType, setSelectedItemSubType] = useState(savedState?.selectedItemSubType || 'all');
  const [selectedMaterial, setSelectedMaterial] = useState(savedState?.selectedMaterial || 'all');
  const [selectedSource, setSelectedSource] = useState(savedState?.selectedSource || 'all');
  const [showCraftedOnly, setShowCraftedOnly] = useState(savedState?.showCraftedOnly || false);
  const [showCraftMaterialsOnly, setShowCraftMaterialsOnly] = useState(savedState?.showCraftMaterialsOnly || false);
  const [selectedItemForModal, setSelectedItemForModal] = useState<any>(null);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [isFiltersDrawerOpen, setIsFiltersDrawerOpen] = useState(false);

  const [collection, setCollection] = useState<NftCollection | null>(null);
  const [items, setItems] = useState<NFTItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [isInitialLoad, setIsInitialLoad] = useState(true);
  const [isUpdatingItems, setIsUpdatingItems] = useState(false); // Estado separado para atualização de itens
  const [serverCount, setServerCount] = useState<number>(0);
  const [page, setPage] = useState<number>(1);
  const [hasMore, setHasMore] = useState<boolean>(false);
  const [loadingMore, setLoadingMore] = useState<boolean>(false);
  const loadMoreRef = useRef<HTMLDivElement | null>(null);
  const [error, setError] = useState<string | null>(null);

  // Salvar estado no sessionStorage sempre que mudar
  useEffect(() => {
    const stateToSave = {
      viewMode,
      sortBy,
      filterRarity,
      searchQuery,
      selectedItems,
      priceRange,
      showSelectedOnly,
      selectedItemType,
      selectedItemSubType,
      selectedMaterial,
      selectedSource,
      showCraftedOnly,
      showCraftMaterialsOnly,
    };
    try {
      sessionStorage.setItem(storageKey, JSON.stringify(stateToSave));
    } catch (e) {
      console.warn('Erro ao salvar estado no sessionStorage:', e);
    }
  }, [storageKey, viewMode, sortBy, filterRarity, searchQuery, selectedItems, priceRange, showSelectedOnly, selectedItemType, selectedItemSubType, selectedMaterial, selectedSource, showCraftedOnly, showCraftMaterialsOnly]);

  // Restaurar posição do scroll ao montar
  useEffect(() => {
    const savedScroll = sessionStorage.getItem(scrollKey);
    if (savedScroll) {
      const scrollY = parseInt(savedScroll, 10);
      // Aguardar um pouco para garantir que o conteúdo foi renderizado
      setTimeout(() => {
        window.scrollTo({ top: scrollY, behavior: 'auto' });
      }, 100);
    }
  }, [scrollKey]);

  // Salvar posição do scroll antes de sair da página
  useEffect(() => {
    const handleScroll = () => {
      sessionStorage.setItem(scrollKey, String(window.scrollY));
    };
    
    // Salvar scroll periodicamente (a cada 500ms) e ao sair
    const scrollInterval = setInterval(handleScroll, 500);
    window.addEventListener('beforeunload', handleScroll);
    
    return () => {
      clearInterval(scrollInterval);
      window.removeEventListener('beforeunload', handleScroll);
      // Salvar uma última vez ao desmontar
      handleScroll();
    };
  }, [scrollKey]);

  // Load collection detail (only when slug changes)
  useEffect(() => {
    let mounted = true;
    setCollection(null);
    fetchCollectionDetail(collectionId)
      .then((col) => { if (mounted) setCollection(col); })
      .catch(() => {})
    return () => { mounted = false; };
  }, [collectionId]);

  // Build API params from current filters
  const mapOrdering = (s: string) => {
    switch (s) {
      case 'price_low': return 'last_price_brl';
      case 'price_high': return '-last_price_brl';
      case 'name': return 'name';
      case 'rarity': return 'rarity';
      default: return 'name';
    }
  };

  const buildParams = (pageNum: number) => ({
    collection_slug: collectionId,
    page: pageNum,
    page_size: 50,
    ordering: mapOrdering(sortBy),
    search: searchQuery || undefined,
    rarity: filterRarity !== 'all' ? filterRarity : undefined,
    item_type: selectedItemType !== 'all' ? selectedItemType : undefined,
    item_sub_type: selectedItemSubType !== 'all' ? selectedItemSubType : undefined,
    material: selectedMaterial !== 'all' ? selectedMaterial : undefined,
    source: selectedSource !== 'all' ? selectedSource : undefined,
    is_crafted_item: showCraftedOnly ? true : undefined,
    is_craft_material: showCraftMaterialsOnly ? true : undefined,
    min_price_brl: priceRange.min ? Number(priceRange.min) : undefined,
    max_price_brl: priceRange.max ? Number(priceRange.max) : undefined,
  });

  // Debounced fetch of first page whenever filters/search/order change
  useEffect(() => {
    let mounted = true;
    const t = setTimeout(() => {
      // Só mostrar loading full screen na primeira carga
      if (isInitialLoad) {
        setLoading(true);
      } else {
        // Para atualizações de filtros, usar estado separado que não afeta o resto da página
        setIsUpdatingItems(true);
      }
      setPage(1);
      setHasMore(false);
      fetchNFTItems(buildParams(1))
        .then((list) => {
          if (!mounted) return;
          // Atualizar itens apenas quando a resposta chegar
          setItems(list.results || []);
          setServerCount(list.count || 0);
          setHasMore(Boolean(list.next));
          setError(null);
          setIsInitialLoad(false); // Marcar que a primeira carga foi concluída
        })
        .catch((e: any) => {
          if (!mounted) return;
          setError(e?.message || 'Falha ao carregar itens');
          setIsInitialLoad(false);
        })
        .finally(() => {
          if (mounted) {
            setLoading(false);
            setIsUpdatingItems(false);
          }
        });
    }, 250);
    return () => { mounted = false; clearTimeout(t); };
  }, [collectionId, searchQuery, filterRarity, selectedItemType, selectedItemSubType, selectedMaterial, selectedSource, showCraftedOnly, showCraftMaterialsOnly, priceRange.min, priceRange.max, sortBy]);

  // Infinite scroll: load next pages when sentinel appears (with current filters)
  useEffect(() => {
    if (!hasMore || loading || loadingMore) return;
    const el = loadMoreRef.current;
    if (!el) return;
    const observer = new IntersectionObserver((entries) => {
      const first = entries[0];
      if (first && first.isIntersecting) {
        // Load next page
        setLoadingMore(true);
        const nextPage = page + 1;
        fetchNFTItems(buildParams(nextPage))
          .then((res) => {
            setItems(prev => [...prev, ...(res.results || [])]);
            setPage(nextPage);
            setHasMore(Boolean(res.next));
          })
          .finally(() => setLoadingMore(false));
      }
    }, { rootMargin: '200px' });
    observer.observe(el);
    return () => observer.disconnect();
  }, [hasMore, loading, loadingMore, page, collectionId]);

  // Todos os hooks devem ser chamados antes de qualquer return condicional
  // Handlers memoizados para evitar re-renders desnecessários
  const clearAllFilters = useCallback(() => {
    setFilterRarity('all');
    setSelectedItemType('all');
    setSelectedItemSubType('all');
    setSelectedMaterial('all');
    setSelectedSource('all');
    setPriceRange({ min: '', max: '' });
    setShowCraftedOnly(false);
    setShowCraftMaterialsOnly(false);
    setSearchQuery('');
    // Limpar sessionStorage também
    sessionStorage.removeItem(storageKey);
    sessionStorage.removeItem(scrollKey);
  }, [storageKey, scrollKey]);

  const handleSearchChange = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    setSearchQuery(e.target.value);
  }, []);

  const handlePriceMinChange = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    setPriceRange(prev => ({ ...prev, min: e.target.value }));
  }, []);

  const handlePriceMaxChange = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    setPriceRange(prev => ({ ...prev, max: e.target.value }));
  }, []);

  const handleClearFilters = useCallback(() => {
    clearAllFilters();
    setIsFiltersDrawerOpen(false);
  }, [clearAllFilters]);

  // Mostrar loading full screen apenas na primeira carga
  if (loading && isInitialLoad) {
    return (
      <div className="py-16 lg:py-24 text-center">
        <div className="container mx-auto px-4 lg:px-8 text-muted-foreground">Carregando coleção...</div>
      </div>
    );
  }

  if (error || !collection) {
    return (
      <div className="py-16 lg:py-24">
        <div className="container mx-auto px-4 lg:px-8 text-center">
          <h2 className="text-2xl font-bold mb-4">Coleção não encontrada</h2>
          <Button onClick={onBack} className="bg-[#FFE000] hover:bg-[#FFD700] text-black">
            <ArrowLeft className="w-4 h-4 mr-2" />
            Voltar
          </Button>
        </div>
      </div>
    );
  }

  // Items come pre-filtered and pre-ordered from API; optionally filter by selection-only toggle
  let filteredItems = items;
  if (showSelectedOnly) {
    filteredItems = filteredItems.filter((item: any) => selectedItems.includes(String(item.id)));
  }

  const handleItemSelect = (itemId: string) => {
    setSelectedItems(prev => 
      prev.includes(itemId) 
        ? prev.filter(id => id !== itemId)
        : [...prev, itemId]
    );
  };

  const handleSelectAll = () => {
    if (selectedItems.length === filteredItems.length) {
      setSelectedItems([]);
    } else {
      setSelectedItems(filteredItems.map((item: any) => String(item.id)));
    }
  };

  const clearSelection = () => {
    setSelectedItems([]);
    setShowSelectedOnly(false);
  };

  const getTotalSelectedPrice = () => {
    return selectedItems.reduce((total, itemId) => {
      const item = items.find((i: any) => String(i.id) === itemId);
      const val = Number(item?.last_price_brl || 0);
      return total + val;
    }, 0).toLocaleString('pt-BR', { minimumFractionDigits: 2 });
  };

  const handleItemClick = (item: any) => {
    // Prefer navigating to item page route /:slug/:product_code
    const slug = collection?.slug || collectionId;
    const productCode = item?.product_code;
    if (slug && productCode) {
      const target = `/${slug}/${productCode}`;
      if (window.location.pathname !== target) {
        window.history.pushState({}, '', target);
        window.scrollTo({ top: 0, behavior: 'smooth' });
        window.dispatchEvent(new PopStateEvent('popstate'));
      }
      return;
    }
    // Fallback to modal if route data is missing
    setSelectedItemForModal(item);
    setIsModalOpen(true);
  };

  return (
    <div>
      <NFTDetailModal 
        item={selectedItemForModal}
        isOpen={isModalOpen}
        onClose={() => {
          setIsModalOpen(false);
          setSelectedItemForModal(null);
        }}
      />
      
      {/* Mobile Filters Drawer */}
      <Drawer open={isFiltersDrawerOpen} onOpenChange={setIsFiltersDrawerOpen}>
        <DrawerContent className="max-h-[85vh]">
          <DrawerHeader className="border-b border-border/40">
            <div className="flex items-center justify-between">
              <DrawerTitle className="text-lg font-semibold">Filtros</DrawerTitle>
              <DrawerClose asChild>
                <Button variant="ghost" size="icon" className="h-8 w-8">
                  <X className="h-4 w-4" />
                </Button>
              </DrawerClose>
            </div>
          </DrawerHeader>
          <div className="overflow-y-auto p-6">
            <div className="space-y-6">
              {/* Price Range */}
              <div>
                <label className="text-sm font-medium mb-3 block text-[#FFE000]">Preço (R$)</label>
                <div className="grid grid-cols-2 gap-2">
                  <Input
                    placeholder="Mín"
                    type="number"
                    value={priceRange.min}
                    onChange={handlePriceMinChange}
                    className="bg-muted/30 border-border/40 text-sm"
                    autoComplete="off"
                  />
                  <Input
                    placeholder="Máx"
                    type="number"
                    value={priceRange.max}
                    onChange={handlePriceMaxChange}
                    className="bg-muted/30 border-border/40 text-sm"
                    autoComplete="off"
                  />
                </div>
              </div>

              <Separator className="border-border/40" />

              <div className="space-y-2">
                <Button 
                  className="w-full bg-muted text-muted-foreground cursor-default"
                  disabled
                  title="Filtros aplicados automaticamente"
                >
                  <Filter className="w-4 h-4 mr-2" />
                  Filtros aplicados automaticamente
                </Button>
                <Button 
                  variant="outline"
                  className="w-full"
                  onClick={handleClearFilters}
                >
                  Limpar Filtros
                </Button>
              </div>
            </div>
          </div>
        </DrawerContent>
      </Drawer>
      
      {/* Collection Banner */}
      {(() => {
        const isHabbo = (collection.creator_name || '').trim().toLowerCase() === 'habbo hotel';
        const bannerCover = isHabbo
          ? 'https://collectibles.habbo.com/hero-bg-xl.png'
          : (collection.profile_image || collection.cover_image || collection.name);
        const bannerLogo = collection.cover_image || collection.profile_image || collection.name;
        return (
          <CollectionBanner
            name={collection.name}
            description={collection.description}
            coverImage={bannerCover}
            logoImage={bannerLogo}
            creator={collection.author}
            isVerified={false}
          />
        );
      })()}

      {/* Marketplace Section */}
      <section className="py-8 lg:py-16 bg-background">
        <div className="container mx-auto px-4 lg:px-8">
          {/* Selection Summary */}
          {selectedItems.length > 0 && (
            <div className="mb-8">
              <Card className="bg-[#FFE000]/10 border-[#FFE000]/30">
                <CardContent className="p-4">
                  <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
                    <div className="flex items-center space-x-4">
                      <div className="flex items-center space-x-2">
                        <ShoppingCart className="w-5 h-5 text-[#FFE000]" />
                        <span className="font-medium">
                          {selectedItems.length} item{selectedItems.length > 1 ? 's' : ''} selecionado{selectedItems.length > 1 ? 's' : ''}
                        </span>
                      </div>
                      <div className="text-2xl font-bold text-[#FFE000]">
                        R$ {getTotalSelectedPrice()}
                      </div>
                    </div>
                    <div className="flex items-center space-x-2">
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={() => setShowSelectedOnly(!showSelectedOnly)}
                        className="border-[#FFE000]/30 hover:bg-[#FFE000]/10"
                      >
                        {showSelectedOnly ? 'Mostrar Todos' : 'Mostrar Selecionados'}
                      </Button>
                      <Button
                        size="sm"
                        className="bg-[#FFE000] hover:bg-[#FFD700] text-black"
                        disabled
                      >
                        Comprar Selecionados
                      </Button>
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={clearSelection}
                        className="border-red-500/30 hover:bg-red-500/10 text-red-500"
                      >
                        <Trash2 className="w-4 h-4" />
                      </Button>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </div>
          )}

          <div className="grid lg:grid-cols-4 gap-8">
            {/* Sidebar com Filtros - Desktop Only */}
            <div className="hidden lg:block lg:col-span-1">
              <Card className="bg-card/50 backdrop-blur border-border/40 sticky top-24">
                <CardContent className="p-6">
                  <div className="space-y-6">
                    {/* Search - Desktop Only */}
                    <div>
                      <label className="text-sm font-medium mb-2 block">Buscar</label>
                      <div className="relative">
                        <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-muted-foreground h-4 w-4" />
                        <Input
                          placeholder="Nome ou código..."
                          value={searchQuery}
                          onChange={handleSearchChange}
                          className="pl-10 bg-muted/30 border-border/40"
                          autoComplete="off"
                        />
                      </div>
                    </div>

                    <Separator className="border-border/40" />

                    {/* Price Range */}
                    <div>
                      <label className="text-sm font-medium mb-3 block text-[#FFE000]">Preço (R$)</label>
                      <div className="grid grid-cols-2 gap-2">
                        <Input
                          placeholder="Mín"
                          type="number"
                          value={priceRange.min}
                          onChange={handlePriceMinChange}
                          className="bg-muted/30 border-border/40 text-sm"
                          autoComplete="off"
                        />
                        <Input
                          placeholder="Máx"
                          type="number"
                          value={priceRange.max}
                          onChange={handlePriceMaxChange}
                          className="bg-muted/30 border-border/40 text-sm"
                          autoComplete="off"
                        />
                      </div>
                    </div>

                    <Separator className="border-border/40" />

                    <div className="space-y-2">
                      <Button 
                        className="w-full bg-muted text-muted-foreground cursor-default"
                        disabled
                        title="Filtros aplicados automaticamente"
                      >
                        <Filter className="w-4 h-4 mr-2" />
                        Filtros aplicados automaticamente
                      </Button>
                      <Button 
                        variant="outline"
                        className="w-full"
                        onClick={clearAllFilters}
                      >
                        Limpar Filtros
                      </Button>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </div>

            {/* Main Content */}
            <div className="lg:col-span-3">
              {/* Mobile Search - Always Visible */}
              <div className="lg:hidden mb-4">
                <div className="relative">
                  <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-muted-foreground h-4 w-4" />
                  <Input
                    placeholder="Buscar por nome ou código..."
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    className="pl-10 bg-muted/30 border-border/40"
                  />
                </div>
              </div>

              {/* Toolbar */}
              <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 mb-8">
                {/* Mobile Filter Button */}
                <Button
                  variant="outline"
                  className="lg:hidden flex items-center gap-2"
                  onClick={() => setIsFiltersDrawerOpen(true)}
                >
                  <Filter className="w-4 h-4" />
                  Filtros
                  {(priceRange.min || priceRange.max) && (
                    <Badge variant="secondary" className="ml-2 h-5 px-1.5 text-xs">
                      {[priceRange.min, priceRange.max].filter(Boolean).length}
                    </Badge>
                  )}
                </Button>
                
                <div className="flex items-center space-x-4 w-full sm:w-auto">
                  <span className="text-sm text-muted-foreground">
                    {items.length} de {serverCount} itens
                  </span>
                  {filterRarity !== 'all' && (
                    <Badge variant="outline" className="border-[#FFE000]/30 text-[#FFE000]">
                      {rarityOptions.find(r => r.id === filterRarity)?.name}
                    </Badge>
                  )}
                </div>

                <div className="flex items-center space-x-2">
                  <select
                    value={sortBy}
                    onChange={(e) => setSortBy(e.target.value)}
                    className="p-2 bg-muted/30 border border-border/40 rounded-lg text-sm"
                  >
                    <option value="price_low">Menor Preço</option>
                    <option value="price_high">Maior Preço</option>
                    <option value="name">Nome</option>
                    <option value="rarity">Raridade</option>
                  </select>

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

                  <Button
                    size="sm"
                    variant="outline"
                    onClick={handleSelectAll}
                    className="border-[#FFE000]/30"
                  >
                    {selectedItems.length === filteredItems.length ? 'Desmarcar Todos' : 'Selecionar Todos'}
                  </Button>
                </div>
              </div>

              {/* Items Grid */}
              <div className="relative">
                {/* Loading overlay sutil - apenas quando está atualizando itens e há itens */}
                {isUpdatingItems && filteredItems.length > 0 && (
                  <div className="absolute inset-0 bg-background/50 backdrop-blur-sm z-10 rounded-lg flex items-center justify-center">
                    <div className="flex flex-col items-center gap-2">
                      <div className="w-8 h-8 border-2 border-[#FFE000] border-t-transparent rounded-full animate-spin" />
                      <span className="text-sm text-muted-foreground">Atualizando...</span>
                    </div>
                  </div>
                )}
                
                {filteredItems.length > 0 ? (
                  <div className={`grid gap-6 ${
                    viewMode === 'grid' 
                      ? 'grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-6' 
                      : 'grid-cols-1'
                  } ${isUpdatingItems ? 'opacity-60' : 'opacity-100'} transition-opacity duration-200`}>
                    {filteredItems.map((item: any) => (
                      <div key={item.id}>
                        <NFTCard
                          id={String(item.id)}
                          name={item.name}
                          image={item.image_url || collection.name}
                          price={formatPriceBRL(item.last_price_brl)}
                          collection={collection.name}
                          category={item.item_type}
                          rarity={item.rarity}
                          lastSale={"—"}
                          isAuction={false}
                          onClick={() => handleItemClick(item)}
                        />
                      </div>
                    ))}
                  </div>
                ) : !loading ? (
                <Card className="p-12 text-center">
                  <div className="flex justify-center mb-4">
                    <Search className="w-14 h-14 text-[#FFE000]" />
                  </div>
                  <h3 className="text-xl font-semibold mb-2">Nenhum item encontrado</h3>
                  <p className="text-muted-foreground mb-4">
                    Tente ajustar seus filtros para encontrar mais resultados
                  </p>
                  <Button
                    onClick={clearAllFilters}
                    className="bg-[#FFE000] hover:bg-[#FFD700] text-black"
                  >
                    Limpar Filtros
                  </Button>
                </Card>
              ) : (
                // Mostrar skeleton apenas quando está carregando e não há itens
                <div className={`grid gap-6 ${
                  viewMode === 'grid' 
                    ? 'grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-6' 
                    : 'grid-cols-1'
                }`}>
                  {Array.from({ length: 6 }).map((_, i) => (
                    <div key={i} className="h-72 bg-muted/30 rounded-xl animate-pulse" />
                  ))}
                </div>
              )}
              </div>

              {/* Infinite loader sentinel */}
              <div ref={loadMoreRef} className="h-12 flex items-center justify-center mt-6">
                {loadingMore && (
                  <span className="text-sm text-muted-foreground">Carregando mais itens...</span>
                )}
                {!hasMore && items.length > 0 && (
                  <span className="text-sm text-muted-foreground">Todos os itens carregados</span>
                )}
              </div>
            </div>
          </div>
        </div>
      </section>
    </div>
  );
}
