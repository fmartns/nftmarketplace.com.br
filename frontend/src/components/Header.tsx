import { useEffect, useRef, useState } from 'react';
import type React from 'react';
import { Button } from './ui/button';
import { Wallet, Search, Menu, X, User, LogOut, ShoppingBag, Settings } from 'lucide-react';
import { Input } from './ui/input';
import { fetchNFTByProductCode, fetchNFTItems, type NFTItem } from '@/api/nft';
import { ImageWithFallback } from './figma/ImageWithFallback';
import { generateAuthMessage, loginWithMetaMask, fetchUserProfile, type User } from '@/api/accounts';
import logoImage from '@/assets/logo.png';

interface HeaderProps {
  onLogoClick?: () => void;
  activeTab?: string;
  onTabChange?: (tab: string) => void;
}

export function Header({ onLogoClick, activeTab = 'home', onTabChange }: HeaderProps) {
  const [isConnected, setIsConnected] = useState(false);
  const [isMenuOpen, setIsMenuOpen] = useState(false);
  const [walletAddress, setWalletAddress] = useState('');
  const [user, setUser] = useState<User | null>(null);
  const [isConnecting, setIsConnecting] = useState(false);
  const [isDropdownOpen, setIsDropdownOpen] = useState(false);
  const [isOrdersHovered, setIsOrdersHovered] = useState(false);
  const [isSettingsHovered, setIsSettingsHovered] = useState(false);
  const [isDisconnectHovered, setIsDisconnectHovered] = useState(false);
  const [avatarImageError, setAvatarImageError] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);

  // Check if user is logged in on mount
  useEffect(() => {
    const checkAuth = async () => {
      const token = localStorage.getItem('access_token') || localStorage.getItem('token');
      if (token) {
        // Try to fetch user profile to verify token
        try {
          const userData = await fetchUserProfile();
          setUser(userData);
          setIsConnected(true);
          setWalletAddress(userData.wallet_address || '');
          setAvatarImageError(false); // Reset avatar error when user changes
        } catch (error: any) {
          console.error('Erro ao verificar token:', error);
          // Only clear token if it's a 401/403 error (unauthorized/forbidden)
          // Don't clear on network errors or other issues
          if (error?.message?.includes('401') || error?.message?.includes('403')) {
            localStorage.removeItem('access_token');
            localStorage.removeItem('refresh_token');
            localStorage.removeItem('token');
            setIsConnected(false);
            setWalletAddress('');
            setUser(null);
          }
        }
      }
    };

    // Small delay to ensure localStorage is fully updated after login
    const timer = setTimeout(() => {
      checkAuth();
    }, 100);

    // Listen for MetaMask account changes
    let handleAccountsChanged: ((accounts: string[]) => void) | null = null;
    let handleChainChanged: (() => void) | null = null;

    if (typeof window !== 'undefined' && (window as any).ethereum) {
      handleAccountsChanged = (accounts: string[]) => {
        if (accounts.length === 0) {
          // User disconnected MetaMask
          localStorage.removeItem('access_token');
          localStorage.removeItem('refresh_token');
          localStorage.removeItem('token');
          setIsConnected(false);
          setWalletAddress('');
          setUser(null);
          setIsDropdownOpen(false);
        } else {
          // Account changed, check if we need to reconnect
          const currentAddress = accounts[0].toLowerCase();
          const token = localStorage.getItem('access_token') || localStorage.getItem('token');
          const storedAddress = walletAddress || (user?.wallet_address || '').toLowerCase();
          if (token && storedAddress && currentAddress !== storedAddress) {
            // Different account, need to reconnect
            localStorage.removeItem('access_token');
            localStorage.removeItem('refresh_token');
            localStorage.removeItem('token');
            setIsConnected(false);
            setWalletAddress('');
            setUser(null);
            setIsDropdownOpen(false);
            if (window.location.pathname === '/configuracoes' || window.location.pathname === '/pedidos') {
              window.history.pushState({}, '', '/');
              window.scrollTo({ top: 0, behavior: 'smooth' });
              window.dispatchEvent(new PopStateEvent('popstate'));
            }
          }
        }
      };

      handleChainChanged = () => {
        // Reload page on chain change
        window.location.reload();
      };

      (window as any).ethereum.on('accountsChanged', handleAccountsChanged);
      (window as any).ethereum.on('chainChanged', handleChainChanged);
    }

    return () => {
      clearTimeout(timer);
      if ((window as any).ethereum && handleAccountsChanged && handleChainChanged) {
        (window as any).ethereum.removeListener('accountsChanged', handleAccountsChanged);
        (window as any).ethereum.removeListener('chainChanged', handleChainChanged);
      }
    };
  }, []);

  // Local navigation helper
  const goTo = (to: string) => {
    const target = to.startsWith('/') ? to : `/${to}`;
    if (window.location.pathname !== target) {
      window.history.pushState({}, '', target);
      window.scrollTo({ top: 0, behavior: 'smooth' });
      window.dispatchEvent(new PopStateEvent('popstate'));
      // Also trigger a custom event for App.tsx to catch
      window.dispatchEvent(new CustomEvent('locationchange', { detail: { path: target } }));
    }
  };

  const connectWallet = async () => {
    if (typeof window === 'undefined' || !(window as any).ethereum) {
      alert('MetaMask não encontrado. Por favor, instale a extensão MetaMask.');
      return;
    }

    setIsConnecting(true);
    try {
      // 1. Request account access
      const accounts = await (window as any).ethereum.request({
        method: 'eth_requestAccounts',
      });
      
      if (!accounts || accounts.length === 0) {
        throw new Error('Nenhuma conta encontrada');
      }

      const address = accounts[0].toLowerCase();
      setWalletAddress(address);

      // 2. Get authentication message from backend
      const { message } = await generateAuthMessage(address);

      // 3. Sign message with MetaMask
      const signature = await (window as any).ethereum.request({
        method: 'personal_sign',
        params: [message, address],
      });

      // 4. Send signature to backend for authentication
      const authResponse = await loginWithMetaMask({
        wallet_address: address,
        signature: signature,
        message: message,
      });

      // 5. Save tokens to localStorage
      localStorage.setItem('access_token', authResponse.access_token);
      localStorage.setItem('refresh_token', authResponse.refresh_token);

      // 6. Update user state
      setUser(authResponse.user);
      setIsConnected(true);
      setWalletAddress(authResponse.user.wallet_address || address);
      setAvatarImageError(false); // Reset avatar error on login

      // 7. Trigger a re-check of auth state after a brief delay
      // This ensures the UserProfilePage can fetch the user data
      setTimeout(() => {
        fetchUserProfile()
          .then((userData) => {
            setUser(userData);
            setWalletAddress(userData.wallet_address || address);
            setAvatarImageError(false); // Reset avatar error when user data updates
          })
          .catch((err) => {
            console.error('Erro ao buscar perfil após login:', err);
          });
      }, 200);

      // Show success message for new users only
      if (authResponse.is_new_user) {
        alert('Bem-vindo! Sua conta foi criada com sucesso.');
      }
    } catch (error: any) {
      console.error('Erro ao conectar carteira:', error);
      const errorMessage = error?.message || 'Erro ao conectar carteira. Por favor, tente novamente.';
      alert(errorMessage);
      setWalletAddress('');
      setIsConnected(false);
      setUser(null);
    } finally {
      setIsConnecting(false);
    }
  };

  const formatAddress = (address: string) => {
    if (!address) return '';
    return `${address.slice(0, 6)}...${address.slice(-4)}`;
  };

  const disconnectWallet = () => {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    localStorage.removeItem('token');
    setWalletAddress('');
    setIsConnected(false);
    setUser(null);
    setIsDropdownOpen(false);
    // Navigate to home if on settings or orders page
    if (window.location.pathname === '/configuracoes' || window.location.pathname === '/pedidos') {
      goTo('/');
    }
  };

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsDropdownOpen(false);
      }
    };
    if (isDropdownOpen) {
      document.addEventListener('mousedown', handleClickOutside);
    }
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, [isDropdownOpen]);

  // SearchBox component with typeahead suggestions (desktop and mobile reuse)
  function SearchBox({ className = '' }: { className?: string }) {
    const [query, setQuery] = useState('');
    const [loading, setLoading] = useState(false);
    const [items, setItems] = useState<NFTItem[]>([]);
    const [open, setOpen] = useState(false);
    const [highlight, setHighlight] = useState(-1);
    const wrapperRef = useRef<HTMLDivElement | null>(null);
    const timerRef = useRef<number | null>(null);

    // Close on outside click
    useEffect(() => {
      const onDown = (e: MouseEvent) => {
        if (!wrapperRef.current) return;
        if (!wrapperRef.current.contains(e.target as Node)) setOpen(false);
      };
      document.addEventListener('mousedown', onDown);
      return () => document.removeEventListener('mousedown', onDown);
    }, []);

    // Debounced fetch
    useEffect(() => {
      if (timerRef.current) {
        window.clearTimeout(timerRef.current);
        timerRef.current = null;
      }
      const q = query.trim();
      if (!q) {
        setItems([]);
        setOpen(false);
        setHighlight(-1);
        return;
      }
      timerRef.current = window.setTimeout(async () => {
        try {
          setLoading(true);
          const res = await fetchNFTItems({ search: q, page_size: 8, ordering: '-updated_at' });
          setItems(res.results || []);
          setOpen((res.results || []).length > 0);
          setHighlight(-1);
        } catch {
          setItems([]);
          setOpen(false);
          setHighlight(-1);
        } finally {
          setLoading(false);
        }
      }, 250);
      return () => {
        if (timerRef.current) {
          window.clearTimeout(timerRef.current);
          timerRef.current = null;
        }
      };
    }, [query]);

    const navigateToItem = (it: NFTItem) => {
      if (it.collection_slug && it.product_code) {
        goTo(`/${it.collection_slug}/${it.product_code}`);
      } else if (it.collection_slug) {
        goTo(`/${it.collection_slug}`);
      }
      setOpen(false);
    };

    const onSubmit = async () => {
      const q = query.trim();
      if (!q) return;
      // If there are suggestions and one is highlighted, go to it
      if (open && items.length > 0) {
        const index = highlight >= 0 ? highlight : 0;
        navigateToItem(items[index]);
        return;
      }
      // Try direct product_code match
      try {
        const direct = await fetchNFTByProductCode(q);
        if (direct) {
          navigateToItem(direct);
          return;
        }
      } catch {}
      // Fallback: if we had any items, go to the first
      if (items.length > 0) {
        navigateToItem(items[0]);
      }
      setOpen(false);
    };

    const onKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
      if (!open || items.length === 0) {
        if (e.key === 'Enter') {
          e.preventDefault();
          onSubmit();
        }
        return;
      }
      if (e.key === 'ArrowDown') {
        e.preventDefault();
        setHighlight((h) => (h + 1) % items.length);
      } else if (e.key === 'ArrowUp') {
        e.preventDefault();
        setHighlight((h) => (h <= 0 ? items.length - 1 : h - 1));
      } else if (e.key === 'Enter') {
        e.preventDefault();
        const idx = highlight >= 0 ? highlight : 0;
        navigateToItem(items[idx]);
      } else if (e.key === 'Escape') {
        setOpen(false);
      }
    };

    return (
      <div ref={wrapperRef} className={`relative ${className}`}>
        <div className="relative w-full">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-muted-foreground h-4 w-4" />
          <Input
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={onKeyDown}
            placeholder="Buscar NFTs, coleções..."
            className="pl-10 bg-muted/30 border-border/40"
          />
        </div>

        {open && (
          <div className="absolute z-50 mt-2 w-full bg-card border border-border/40 rounded-md shadow-md">
            <ul className="max-h-80 overflow-y-auto py-1">
              {items.map((it, idx) => (
                <li
                  key={it.id}
                  onMouseEnter={() => setHighlight(idx)}
                  onMouseLeave={() => setHighlight(-1)}
                  onMouseDown={(e) => { e.preventDefault(); navigateToItem(it); }}
                  className={`px-3 py-2 cursor-pointer flex items-center justify-between ${idx === highlight ? 'bg-muted/50' : ''}`}
                >
                  <div className="flex items-center min-w-0 mr-3 gap-3">
                    <div className="h-9 w-9 rounded-md overflow-hidden flex-shrink-0 bg-muted/40 border border-border/40">
                      <ImageWithFallback
                        src={it.image_url || ''}
                        alt={it.name || it.product_code || 'NFT'}
                        className="h-full w-full object-cover"
                      />
                    </div>
                    <div className="min-w-0">
                      <p className="text-sm font-medium truncate">{it.name || it.product_code}</p>
                      <p className="text-xs text-muted-foreground truncate">{it.collection_name || it.collection_slug}</p>
                    </div>
                  </div>
                  <div className="text-sm text-[#FFE000] font-semibold">
                    {typeof it.last_price_brl === 'string' || typeof it.last_price_brl === 'number' ? `R$ ${Number(it.last_price_brl || 0).toLocaleString('pt-BR', { minimumFractionDigits: 2 })}` : ''}
                  </div>
                </li>
              ))}
              {loading && (
                <li className="px-3 py-2 text-sm text-muted-foreground">Carregando…</li>
              )}
              {!loading && items.length === 0 && (
                <li className="px-3 py-2 text-sm text-muted-foreground">Nenhum resultado</li>
              )}
            </ul>
          </div>
        )}
      </div>
    );
  }

  return (
    <header className="sticky top-0 z-50 border-b border-border/40 bg-background/80 backdrop-blur supports-[backdrop-filter]:bg-background/60">
      <div className="container mx-auto px-4 lg:px-8">
        <div className="flex h-20 items-center justify-between">
          {/* Logo */}
          <button 
            className="flex items-center space-x-2 hover:opacity-80 transition-opacity flex-shrink-0"
            onClick={onLogoClick}
          >
            <img 
              src={logoImage} 
              alt="NFT Marketplace" 
              className="h-11 max-w-[190px] w-auto object-contain"
            />
          </button>

          {/* Navigation Menu - Desktop */}
          <div className="hidden lg:flex items-center mx-8">
            <div className="flex items-center space-x-1 bg-muted/30 rounded-lg p-1">
              <Button
                variant={activeTab === 'home' ? 'default' : 'ghost'}
                size="sm"
                className={`${activeTab === 'home' ? 'bg-[#FFE000] text-black hover:bg-[#FFD700]' : 'hover:bg-muted/50'}`}
                onClick={() => onTabChange?.('home')}
              >
                Home
              </Button>
              <Button
                variant={activeTab === 'nfts' ? 'default' : 'ghost'}
                size="sm"
                className={`${activeTab === 'nfts' ? 'bg-[#FFE000] text-black hover:bg-[#FFD700]' : 'hover:bg-muted/50'}`}
                onClick={() => onTabChange?.('nfts')}
              >
                NFTs
              </Button>
              <Button
                variant={activeTab === 'promocoes' ? 'default' : 'ghost'}
                size="sm"
                className={`${activeTab === 'promocoes' ? 'bg-[#FFE000] text-black hover:bg-[#FFD700]' : 'hover:bg-muted/50'}`}
                onClick={() => onTabChange?.('promocoes')}
              >
                Promoções
              </Button>
              <Button
                variant={activeTab === 'legacy' ? 'default' : 'ghost'}
                size="sm"
                className={`${activeTab === 'legacy' ? 'bg-[#FFE000] text-black hover:bg-[#FFD700]' : 'hover:bg-muted/50'}`}
                onClick={() => onTabChange?.('legacy')}
              >
                Legacy
              </Button>
            </div>
          </div>

          {/* Search Bar - Desktop */}
          <div className="hidden lg:flex items-center space-x-4 flex-1 max-w-lg">
            <SearchBox className="w-full" />
          </div>

          {/* Wallet Connection */}
          <div className="flex items-center space-x-4">
            {isConnected ? (
              <div className="relative" ref={dropdownRef}>
                <button
                  onClick={() => setIsDropdownOpen(!isDropdownOpen)}
                  style={{
                    width: '38px',
                    height: '38px',
                    borderRadius: '50%',
                    backgroundColor: 'hsla(0, 0%, 100%, .15)',
                    border: '1px solid transparent',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    cursor: 'pointer',
                    padding: 0,
                    overflow: 'hidden'
                  }}
                >
                  {user?.nick_habbo && !avatarImageError ? (
                    <img
                      src={`https://www.habbo.com.br/habbo-imaging/avatarimage?&user=${encodeURIComponent(user.nick_habbo)}&action=std&direction=4&head_direction=4&img_format=png&gesture=std&headonly=1&size=b`}
                      alt={user.username}
                      style={{
                        width: '100%',
                        height: '100%',
                        objectFit: 'cover'
                      }}
                      onError={() => setAvatarImageError(true)}
                    />
                  ) : (
                    <User className="w-4 h-4" style={{ color: 'white' }} />
                  )}
                </button>
                {isDropdownOpen && (
                  <div 
                    className="absolute right-0 mt-2 rounded-lg shadow-lg z-[9999] overflow-hidden"
                    style={{ 
                      width: '200px',
                      backgroundColor: '#171728',
                      transform: 'translateX(calc(-100% + 38px))'
                    }}
                  >
                    <button
                      onClick={() => {
                        goTo('/pedidos');
                        setIsDropdownOpen(false);
                      }}
                      onMouseEnter={() => setIsOrdersHovered(true)}
                      onMouseLeave={() => setIsOrdersHovered(false)}
                      className="w-full flex items-center px-3 py-2 transition-colors text-left"
                      style={{
                        color: isOrdersHovered ? '#FFE004' : 'white',
                        backgroundColor: isOrdersHovered ? 'rgba(255, 224, 4, 0.1)' : 'transparent'
                      }}
                    >
                      <ShoppingBag 
                        className="w-4 h-4 mr-2 transition-colors" 
                        style={{ color: isOrdersHovered ? '#FFE004' : 'white' }}
                      />
                      <span>Pedidos</span>
                    </button>
                    <button
                      onClick={() => {
                        goTo('/configuracoes');
                        setIsDropdownOpen(false);
                      }}
                      onMouseEnter={() => setIsSettingsHovered(true)}
                      onMouseLeave={() => setIsSettingsHovered(false)}
                      className="w-full flex items-center px-3 py-2 transition-colors text-left"
                      style={{
                        color: isSettingsHovered ? '#FFE004' : 'white',
                        backgroundColor: isSettingsHovered ? 'rgba(255, 224, 4, 0.1)' : 'transparent'
                      }}
                    >
                      <Settings 
                        className="w-4 h-4 mr-2 transition-colors" 
                        style={{ color: isSettingsHovered ? '#FFE004' : 'white' }}
                      />
                      <span>Configurações</span>
                    </button>
                    <div className="h-px bg-[#FFE004]/20"></div>
                    <button
                      onClick={() => {
                        disconnectWallet();
                        setIsDropdownOpen(false);
                      }}
                      onMouseEnter={() => setIsDisconnectHovered(true)}
                      onMouseLeave={() => setIsDisconnectHovered(false)}
                      className="w-full flex items-center px-3 py-2 transition-colors text-left"
                      style={{
                        color: isDisconnectHovered ? '#FFE004' : 'white',
                        backgroundColor: isDisconnectHovered ? 'rgba(255, 224, 4, 0.1)' : 'transparent'
                      }}
                    >
                      <LogOut 
                        className="w-4 h-4 mr-2 transition-colors" 
                        style={{ color: isDisconnectHovered ? '#FFE004' : 'white' }}
                      />
                      <span>Desconectar</span>
                    </button>
                  </div>
                )}
              </div>
            ) : (
              <Button 
                onClick={connectWallet}
                disabled={isConnecting}
                className="bg-[#FFE000] hover:bg-[#FFD700] text-black border-0 disabled:opacity-50"
              >
                <Wallet className="w-4 h-4 mr-2" />
                <span className="hidden sm:inline">
                  {isConnecting ? 'Conectando...' : 'Conectar Carteira'}
                </span>
                <span className="sm:hidden">
                  {isConnecting ? '...' : 'Conectar'}
                </span>
              </Button>
            )}

            {/* Mobile Menu Button */}
            <Button
              variant="ghost"
              size="sm"
              className="lg:hidden"
              onClick={() => setIsMenuOpen(!isMenuOpen)}
            >
              {isMenuOpen ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
            </Button>
          </div>
        </div>

        {/* Mobile Menu */}
        {isMenuOpen && (
          <div className="lg:hidden border-t border-border/40 py-4">
            <div className="flex flex-col space-y-4">
              {/* Mobile Search */}
              <SearchBox />
              
              {/* Mobile Navigation */}
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
                <Button
                  variant={activeTab === 'home' ? 'default' : 'ghost'}
                  className={`${activeTab === 'home' ? 'bg-[#FFE000] text-black' : ''}`}
                  onClick={() => {
                    onTabChange?.('home');
                    setIsMenuOpen(false);
                  }}
                >
                  Home
                </Button>
                <Button
                  variant={activeTab === 'nfts' ? 'default' : 'ghost'}
                  className={`${activeTab === 'nfts' ? 'bg-[#FFE000] text-black' : ''}`}
                  onClick={() => {
                    onTabChange?.('nfts');
                    setIsMenuOpen(false);
                  }}
                >
                  NFTs
                </Button>
                <Button
                  variant={activeTab === 'promocoes' ? 'default' : 'ghost'}
                  className={`${activeTab === 'promocoes' ? 'bg-[#FFE000] text-black' : ''}`}
                  onClick={() => {
                    onTabChange?.('promocoes');
                    setIsMenuOpen(false);
                  }}
                >
                  Promoções
                </Button>
                <Button
                  variant={activeTab === 'legacy' ? 'default' : 'ghost'}
                  className={`${activeTab === 'legacy' ? 'bg-[#FFE000] text-black' : ''}`}
                  onClick={() => {
                    onTabChange?.('legacy');
                    setIsMenuOpen(false);
                  }}
                >
                  Legacy
                </Button>
              </div>
            </div>
          </div>
        )}
      </div>
    </header>
  );
}