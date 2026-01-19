import { useEffect, useMemo, useState } from 'react';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Badge } from './ui/badge';
import { Card, CardContent } from './ui/card';
import { Separator } from './ui/separator';
import { Checkbox } from './ui/checkbox';
import { Search, Filter, Grid3X3, List, ShoppingCart, Trash2 } from 'lucide-react';
import { NFTCard } from './NFTCard';
import { NFTDetailModal } from './NFTDetailModal';
import { fetchNFTItems, fetchCollections, type NFTItem, type NftCollection } from '@/api/nft';
import { Skeleton } from './ui/skeleton';


// Coleções serão carregadas do backend

// Mock items com campos do model NFTItem
const allItems = [
  {
    id: '1',
    name: 'Trono de Ouro Imperial',
    image: 'golden luxury throne chair',
    price: '3.100',
    last_price_brl: 3100,
    collection: { id: '1', name: 'Habbo Rares' },
    rarity: 'lendario',
    item_type: 'mobilia',
    item_sub_type: 'cadeira',
    material: 'ouro',
    source: 'limitado',
    is_crafted_item: false,
    is_craft_material: false,
    product_code: 'THR-GOLD-001',
  },
  {
    id: '2',
    name: 'Sofá Vintage Retrô',
    image: 'retro pixel sofa furniture',
    price: '1.640',
    last_price_brl: 1640,
    collection: { id: '2', name: 'Móveis Clássicos' },
    rarity: 'raro',
    item_type: 'mobilia',
    item_sub_type: 'sofa',
    material: 'tecido',
    source: 'catalogo',
    is_crafted_item: false,
    is_craft_material: false,
    product_code: 'SOF-VIN-002',
  },
  {
    id: '3',
    name: 'Dragão Místico Azul',
    image: 'fantasy dragon creature pet',
    price: '5.000',
    last_price_brl: 5000,
    collection: { id: '4', name: 'Pets Raros' },
    rarity: 'ultra-raro',
    item_type: 'pets',
    item_sub_type: null,
    material: null,
    source: 'evento',
    is_crafted_item: false,
    is_craft_material: false,
    product_code: 'PET-DRG-003',
  },
  {
    id: '4',
    name: 'Cadeira Gamer Neon',
    image: 'neon gaming chair furniture',
    price: '900',
    last_price_brl: 900,
    collection: { id: '3', name: 'Decoração Premium' },
    rarity: 'incomum',
    item_type: 'mobilia',
    item_sub_type: 'cadeira',
    material: 'plastico',
    source: 'catalogo',
    is_crafted_item: false,
    is_craft_material: false,
    product_code: 'CHR-GMR-004',
  },
  {
    id: '5',
    name: 'Coroa Real Deluxe',
    image: 'royal gold crown accessory',
    price: '3.740',
    last_price_brl: 3740,
    collection: { id: '1', name: 'Habbo Rares' },
    rarity: 'epico',
    item_type: 'decoracao',
    item_sub_type: null,
    material: 'ouro',
    source: 'limitado',
    is_crafted_item: false,
    is_craft_material: false,
    product_code: 'CRW-RYL-005',
  },
  {
    id: '6',
    name: 'Cama Vintage Clássica',
    image: 'vintage classic bed furniture',
    price: '1.360',
    last_price_brl: 1360,
    collection: { id: '2', name: 'Móveis Clássicos' },
    rarity: 'raro',
    item_type: 'mobilia',
    item_sub_type: 'cama',
    material: 'madeira',
    source: 'catalogo',
    is_crafted_item: false,
    is_craft_material: false,
    product_code: 'BED-VIN-006',
  },
  {
    id: '7',
    name: 'Lustre de Cristal',
    image: 'luxury crystal chandelier lighting',
    price: '4.200',
    last_price_brl: 4200,
    collection: { id: '3', name: 'Decoração Premium' },
    rarity: 'lendario',
    item_type: 'decoracao',
    item_sub_type: 'luminaria',
    material: 'cristal',
    source: 'limitado',
    is_crafted_item: true,
    is_craft_material: false,
    product_code: 'CHA-CRY-007',
  },
  {
    id: '8',
    name: 'Robô Pet Futurista',
    image: 'futuristic robot pet toy',
    price: '1.980',
    last_price_brl: 1980,
    collection: { id: '4', name: 'Pets Raros' },
    rarity: 'raro',
    item_type: 'pets',
    item_sub_type: null,
    material: 'metal',
    source: 'evento',
    is_crafted_item: false,
    is_craft_material: false,
    product_code: 'PET-RBT-008',
  },
  {
    id: '9',
    name: 'Mesa de Cristal Premium',
    image: 'crystal glass table modern',
    price: '2.850',
    last_price_brl: 2850,
    collection: { id: '3', name: 'Decoração Premium' },
    rarity: 'epico',
    item_type: 'mobilia',
    item_sub_type: 'mesa',
    material: 'cristal',
    source: 'exclusivo',
    is_crafted_item: false,
    is_craft_material: false,
    product_code: 'TBL-CRY-009',
  },
  {
    id: '10',
    name: 'Tapete Persa Luxo',
    image: 'luxury persian carpet rug',
    price: '1.850',
    last_price_brl: 1850,
    collection: { id: '2', name: 'Móveis Clássicos' },
    rarity: 'raro',
    item_type: 'decoracao',
    item_sub_type: 'tapete',
    material: 'tecido',
    source: 'catalogo',
    is_crafted_item: false,
    is_craft_material: false,
    product_code: 'RUG-PRS-010',
  },
];

export function AllItemsMarketplace() {
  // Chave única para o sessionStorage
  const storageKey = 'all_items_marketplace_state';

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

  // Função para salvar estado no sessionStorage
  const saveState = (state: any) => {
    try {
      sessionStorage.setItem(storageKey, JSON.stringify(state));
    } catch (e) {
      console.warn('Erro ao salvar estado no sessionStorage:', e);
    }
  };

  // Carregar estado inicial do sessionStorage
  const savedState = loadState();
  const [selectedCollections, setSelectedCollections] = useState<string[]>(savedState?.selectedCollections || []); // Múltiplas coleções
  const [collections, setCollections] = useState<NftCollection[]>([]);
  const [viewMode, setViewMode] = useState<'grid' | 'list'>(savedState?.viewMode || 'grid');
  const [sortBy, setSortBy] = useState(savedState?.sortBy || 'popular');
  const [searchQuery, setSearchQuery] = useState(savedState?.searchQuery || '');
  const [priceRange, setPriceRange] = useState(savedState?.priceRange || { min: '', max: '' });
  const [selectedItems, setSelectedItems] = useState<string[]>(savedState?.selectedItems || []);
  const [showSelectedOnly, setShowSelectedOnly] = useState(savedState?.showSelectedOnly || false);
  const [selectedItemForModal, setSelectedItemForModal] = useState<any>(null);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [items, setItems] = useState<NFTItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [page, setPage] = useState(1);
  const [hasMore, setHasMore] = useState(true);

  // Buscar coleções do backend
  useEffect(() => {
    let mounted = true;
    fetchCollections().then((data) => {
      if (!mounted) return;
      setCollections(data);
    }).catch(() => {
      // Ignora erros silenciosamente
    });
    return () => { mounted = false; };
  }, []);

  // Salvar estado no sessionStorage sempre que os filtros mudarem
  useEffect(() => {
    saveState({
      selectedCollections,
      viewMode,
      sortBy,
      searchQuery,
      priceRange,
      selectedItems,
      showSelectedOnly,
    });
  }, [selectedCollections, viewMode, sortBy, searchQuery, priceRange, selectedItems, showSelectedOnly]);

  // Reset paginação quando filtros mudarem
  useEffect(() => {
    setPage(1);
  }, [selectedCollections, priceRange.min, priceRange.max, searchQuery]);

  // Buscar itens do backend
  useEffect(() => {
    let mounted = true;
    (async () => {
      try {
        setLoading(true);
        setError(null);
        const params: any = { page_size: 12, page };
        if (selectedCollections.length > 0) {
          params.collection_slug = selectedCollections.join(',');
        }
        if (priceRange.min) params.min_price_brl = priceRange.min;
        if (priceRange.max) params.max_price_brl = priceRange.max;
        if (searchQuery) params.search = searchQuery;
        const res = await fetchNFTItems(params);
        if (!mounted) return;
        const nextItems = res.results || [];
        setItems(prev => page === 1 ? nextItems : [...prev, ...nextItems]);
        setHasMore(Boolean(res.next));
      } catch (e: any) {
        if (!mounted) return;
        setError('Falha ao carregar itens');
      } finally {
        if (mounted) setLoading(false);
      }
    })();
    return () => { mounted = false; };
  }, [page, selectedCollections, priceRange.min, priceRange.max, searchQuery]);

  const filteredItems = useMemo(() => items.filter((item: any) => {
    // Se nenhuma coleção está selecionada, mostra todos os itens
    const matchesCollection = selectedCollections.length === 0 || 
      (item.collection_slug && selectedCollections.includes(item.collection_slug));
    const q = searchQuery.toLowerCase();
    const matchesSearch = !q ||
      (item.name && item.name.toLowerCase().includes(q)) ||
      (item.original_name && String(item.original_name).toLowerCase().includes(q)) ||
      (item.collection_name && item.collection_name.toLowerCase().includes(q)) ||
      (item.product_code && item.product_code.toLowerCase().includes(q));
    const matchesSelection = !showSelectedOnly || selectedItems.includes(String(item.id));
    const itemPrice = Number(item.last_price_brl || 0);
    const matchesMinPrice = !priceRange.min || itemPrice >= parseFloat(priceRange.min);
    const matchesMaxPrice = !priceRange.max || itemPrice <= parseFloat(priceRange.max);
    return matchesCollection && matchesSearch && matchesSelection && matchesMinPrice && matchesMaxPrice;
  }), [items, selectedCollections, searchQuery, selectedItems, priceRange.min, priceRange.max, showSelectedOnly]);

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
      setSelectedItems(filteredItems.map(item => item.id));
    }
  };

  const clearSelection = () => {
    setSelectedItems([]);
    setShowSelectedOnly(false);
  };

  const getTotalSelectedPrice = () => {
    return selectedItems.reduce((total, itemId) => {
      const item = items.find((i: any) => String(i.id) === String(itemId));
      const price = Number((item as any)?.last_price_brl || 0);
      return total + price;
    }, 0).toLocaleString('pt-BR', { minimumFractionDigits: 2 });
  };

  const goToItem = (item: any) => {
    // Salvar estado antes de navegar
    saveState({
      selectedCollections,
      viewMode,
      sortBy,
      searchQuery,
      priceRange,
      selectedItems,
      showSelectedOnly,
    });
    
    const slug = (item as any).collection_slug;
    const code = (item as any).product_code;
    if (slug && code) {
      const to = `/${slug}/${code}`;
      if (window.location.pathname !== to) {
        window.history.pushState({}, '', to);
        window.scrollTo({ top: 0, behavior: 'smooth' });
        window.dispatchEvent(new PopStateEvent('popstate'));
      }
    }
  };

  const clearAllFilters = () => {
    setSelectedCollections([]);
    setPriceRange({ min: '', max: '' });
    setSearchQuery('');
    // Limpar sessionStorage também
    sessionStorage.removeItem(storageKey);
  };

  const handleCollectionToggle = (collectionSlug: string) => {
    setSelectedCollections(prev => 
      prev.includes(collectionSlug)
        ? prev.filter(slug => slug !== collectionSlug)
        : [...prev, collectionSlug]
    );
  };

  const handleSelectAllCollections = () => {
    if (selectedCollections.length === collections.length) {
      setSelectedCollections([]);
    } else {
      setSelectedCollections(collections.map(c => c.slug));
    }
  };

  return (
    <>
      <NFTDetailModal 
        item={selectedItemForModal}
        isOpen={isModalOpen}
        onClose={() => {
          setIsModalOpen(false);
          setSelectedItemForModal(null);
        }}
      />
    <section className="py-8 lg:py-16 bg-background">
      <div className="container mx-auto px-4 lg:px-8">
        {/* Header */}
        <div className="text-center mb-8">
          <h2 className="text-3xl lg:text-4xl font-bold mb-4">
            Explore o <span className="text-[#FFE000]">Marketplace</span>
          </h2>
          <p className="text-lg text-muted-foreground max-w-2xl mx-auto">
            Descubra todos os itens NFT disponíveis de todas as coleções
          </p>
        </div>

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
          {/* Sidebar com Filtros */}
          <div className="lg:col-span-1">
            <Card className="bg-card/50 backdrop-blur border-border/40 sticky top-24">
              <CardContent className="p-6">
                <div className="space-y-6">
                  {/* Search */}
                  <div>
                    <label className="text-sm font-medium mb-2 block">Buscar</label>
                    <div className="relative">
                      <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-muted-foreground h-4 w-4" />
                      <Input
                        placeholder="Nome, coleção ou código..."
                        value={searchQuery}
                        onChange={(e) => setSearchQuery(e.target.value)}
                        className="pl-10 bg-muted/30 border-border/40"
                      />
                    </div>
                  </div>

                  <Separator className="border-border/40" />

                  {/* Collection Filter - Multi-select com checkboxes */}
                  <div>
                    <div className="flex items-center justify-between mb-3">
                      <label className="text-sm font-medium block">Coleção</label>
                      <Button
                        type="button"
                        variant="ghost"
                        size="sm"
                        onClick={handleSelectAllCollections}
                        className="h-auto p-1 text-xs text-muted-foreground hover:text-foreground"
                      >
                        {selectedCollections.length === collections.length ? 'Desmarcar' : 'Marcar todas'}
                      </Button>
                    </div>
                    <div className="space-y-2 max-h-48 overflow-y-auto">
                      {collections.length === 0 ? (
                        <p className="text-xs text-muted-foreground">Carregando coleções...</p>
                      ) : (
                        collections.map((collection) => (
                          <div key={collection.slug} className="flex items-center space-x-2">
                            <Checkbox
                              id={`collection-${collection.slug}`}
                              checked={selectedCollections.includes(collection.slug)}
                              onCheckedChange={() => handleCollectionToggle(collection.slug)}
                              className="mt-0.5"
                            />
                            <label
                              htmlFor={`collection-${collection.slug}`}
                              className="text-sm cursor-pointer flex-1 flex items-center justify-between"
                            >
                              <span>{collection.name}</span>
                              <span className="text-xs text-muted-foreground ml-2">
                                ({collection.items_count ?? 0})
                              </span>
                            </label>
                          </div>
                        ))
                      )}
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
                        onChange={(e) => setPriceRange(prev => ({ ...prev, min: e.target.value }))}
                        className="bg-muted/30 border-border/40 text-sm"
                      />
                      <Input
                        placeholder="Máx"
                        type="number"
                        value={priceRange.max}
                        onChange={(e) => setPriceRange(prev => ({ ...prev, max: e.target.value }))}
                        className="bg-muted/30 border-border/40 text-sm"
                      />
                    </div>
                  </div>

                  <Separator className="border-border/40" />

                  <div className="space-y-2">
                    <Button 
                      className="w-full bg-[#FFE000] hover:bg-[#FFD700] text-black border-0"
                      onClick={() => {/* Filtros já aplicam em tempo real */}}
                    >
                      <Filter className="w-4 h-4 mr-2" />
                      Aplicar Filtros
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
            {/* Toolbar */}
            <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 mb-8">
              <div className="flex items-center space-x-4">
                <span className="text-sm text-muted-foreground">
                  {filteredItems.length} items encontrados
                </span>
                {selectedCollections.length > 0 && (
                  <div className="flex flex-wrap gap-2">
                    {selectedCollections.map(slug => {
                      const collection = collections.find(c => c.slug === slug);
                      return collection ? (
                        <Badge key={slug} variant="outline" className="border-[#FFE000]/30 text-[#FFE000]">
                          {collection.name}
                        </Badge>
                      ) : null;
                    })}
                  </div>
                )}
              </div>

              <div className="flex items-center space-x-2">
                <select
                  value={sortBy}
                  onChange={(e) => setSortBy(e.target.value)}
                  className="p-2 bg-muted/30 border border-border/40 rounded-lg text-sm"
                >
                  <option value="popular">Mais Popular</option>
                  <option value="price-low">Menor Preço</option>
                  <option value="price-high">Maior Preço</option>
                  <option value="recent">Mais Recente</option>
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
            {loading ? (
              <div className={`grid gap-6 ${viewMode === 'grid' ? 'grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 xl:grid-cols-6' : 'grid-cols-1'}`}>
                {Array.from({ length: 12 }).map((_, i) => (
                  <Skeleton key={i} className="h-72 w-full rounded-xl" />
                ))}
              </div>
            ) : filteredItems.length > 0 ? (
              <div className={`grid gap-6 ${
                viewMode === 'grid' 
                  ? 'grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 xl:grid-cols-6' 
                  : 'grid-cols-1'
              }`}>
                {filteredItems.map((item) => {
                  const priceNumber = Number((item as any).last_price_brl ?? 0);
                  const priceStr = priceNumber.toLocaleString('pt-BR', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
                  const imageSrc = (item as any).image_url || '';
                  const collectionName = (item as any).collection_name || '';
                  return (
                    <div key={item.id}>
                      <NFTCard
                        id={String(item.id)}
                        name={(item as any).name}
                        image={imageSrc}
                        price={priceStr}
                        collection={collectionName}
                        category={(item as any).item_type}
                        rarity={(item as any).rarity}
                        lastSale={"—"}
                        isAuction={false}
                        onClick={() => goToItem(item)}
                      />
                    </div>
                  );
                })}
              </div>
            ) : (
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
    </>
  );
}
