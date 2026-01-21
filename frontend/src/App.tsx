import { useEffect, useMemo, useState } from 'react';
import { Header } from './components/Header';
import { HeroSection } from './components/HeroSection';
import { TrendingSection } from './components/TrendingSection';
import { AllItemsMarketplace } from './components/AllItemsMarketplace';
import { AllCollectionsSection } from './components/AllCollectionsSection';
import { CollectionDetailSection } from './components/CollectionDetailSection';
import { NFTItemPage } from './components/NFTItemPage';
import { LegacyListPage } from './components/LegacyListPage';
import { LegacyItemPage } from './components/LegacyItemPage';
import { UserSettingsPage } from './components/UserSettingsPage';
import { OrdersPage } from './components/OrdersPage';
import { PaymentSuccessPage } from './components/PaymentSuccessPage';
import { Footer } from './components/Footer';
import { Toaster } from './components/ui/sonner';
import { useSEO } from './hooks/useSEO';

export default function App() {
  const [path, setPath] = useState(() => window.location.pathname || '/');

  useEffect(() => {
    const onPop = () => setPath(window.location.pathname || '/');
    const onLocationChange = (e: CustomEvent) => {
      setPath(e.detail.path || '/');
    };
    window.addEventListener('popstate', onPop);
    window.addEventListener('locationchange', onLocationChange as EventListener);
    return () => {
      window.removeEventListener('popstate', onPop);
      window.removeEventListener('locationchange', onLocationChange as EventListener);
    };
  }, []);

  // Scroll to top when path changes
  useEffect(() => {
    window.scrollTo({ top: 0, behavior: 'smooth' });
  }, [path]);

  const navigate = (to: string) => {
    const target = to.startsWith('/') ? to : `/${to}`;
    if (window.location.pathname !== target) {
      window.history.pushState({}, '', target);
      setPath(target);
      // Scroll to top immediately on navigation
      window.scrollTo({ top: 0, behavior: 'smooth' });
    }
  };

  const activeTab = useMemo(() => {
    if (path === '/' || path === '/home') return 'home';
    if (path === '/nfts') return 'nfts';
    if (path === '/legacy' || path.startsWith('/legacy/')) return 'legacy';
    if (path === '/collections') return 'collections';
    return 'collections'; // highlight Collections when viewing a collection slug
  }, [path]);

  const handleLogoClick = () => navigate('/');
  const handleTabChange = (tab: string) => {
    if (tab === 'home') navigate('/');
    else if (tab === 'nfts') navigate('/nfts');
    else if (tab === 'collections') navigate('/collections');
    else if (tab === 'legacy') navigate('/legacy');
  };

  // Check payment routes first
  const paymentRoute = useMemo(() => {
    const p = (path || '/').replace(/\/+$/, '');
    if (p.startsWith('/payment/')) {
      return p;
    }
    return null;
  }, [path]);

  // Match routes: /, /collections, /:slug, /:slug/:productCode
  const itemRoute = useMemo(() => {
    // Skip if it's a payment route
    if (paymentRoute) return null;
    
    const p = (path || '/').replace(/\/+$/, '');
    const segments = p.split('/').filter(Boolean);
    if (segments.length === 2) {
      return { slug: segments[0], productCode: segments[1] };
    }
    return null;
  }, [path, paymentRoute]);

  const slugFromPath = useMemo(() => {
    const p = (path || '/').replace(/\/+$/, ''); // remove trailing slash
    if (!p || p === '/') return null;
    if (p === '/collections' || p === '/home' || p === '/nfts' || p === '/legacy' || p === '/configuracoes' || p === '/pedidos' || p.startsWith('/legacy/') || p.startsWith('/payment/')) return null;
    // Treat any single-segment path as a collection slug
    const segments = p.split('/').filter(Boolean);
    if (segments.length === 1) return segments[0];
    return null;
  }, [path]);

  // Check if path is a legacy item route: /legacy/:slug
  const legacyRoute = useMemo(() => {
    const p = (path || '/').replace(/\/+$/, '');
    if (p.startsWith('/legacy/')) {
      const segments = p.split('/').filter(Boolean);
      if (segments.length === 2 && segments[0] === 'legacy') {
        return { slug: segments[1] };
      }
    }
    return null;
  }, [path]);

  // SEO para Home
  const isHome = path === '/' || path === '/home';
  useSEO({
    title: isHome 
      ? 'NFT Marketplace - Compre e Venda NFTs Habbo'
      : undefined,
    description: isHome
      ? 'Marketplace de NFTs Habbo. Compre e venda NFTs únicos com segurança. Explore coleções, itens raros e muito mais.'
      : undefined,
    url: typeof window !== 'undefined' ? window.location.href : undefined,
  });

  return (
    <div className="min-h-screen bg-background">
      <Header 
        onLogoClick={handleLogoClick}
        activeTab={activeTab}
        onTabChange={handleTabChange}
      />

      <main>
        {paymentRoute && paymentRoute.startsWith('/payment/success') ? (
          <PaymentSuccessPage onBack={() => navigate('/pedidos')} />
        ) : legacyRoute ? (
          <LegacyItemPage
            slug={legacyRoute.slug}
            onBack={() => navigate('/legacy')}
          />
        ) : itemRoute ? (
          <NFTItemPage
            slug={itemRoute.slug}
            productCode={itemRoute.productCode}
            onBack={() => window.history.back()}
          />
        ) : slugFromPath ? (
          <CollectionDetailSection 
            collectionId={slugFromPath}
            onBack={() => navigate('/nfts')}
          />
        ) : path === '/nfts' ? (
          <AllCollectionsSection onCollectionSelect={(slug) => navigate(`/${slug}`)} />
        ) : path === '/legacy' ? (
          <LegacyListPage />
        ) : path === '/collections' ? (
          <AllCollectionsSection onCollectionSelect={(slug) => navigate(`/${slug}`)} />
        ) : path === '/configuracoes' ? (
          <UserSettingsPage />
        ) : path === '/pedidos' ? (
          <OrdersPage />
        ) : (
          <>
            <HeroSection />
            <TrendingSection />
            <AllItemsMarketplace />
            {/* StatsSection removed per request */}
          </>
        )}
      </main>

      <Footer />
      <Toaster />
    </div>
  );
}