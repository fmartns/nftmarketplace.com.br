import { useEffect, useState } from 'react';
import { ImageWithFallback } from './figma/ImageWithFallback';
import { fetchUserProfile, type User } from '@/api/accounts';
import { Skeleton } from './ui/skeleton';

export function UserProfilePage() {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let mounted = true;
    setLoading(true);
    setError(null);

    (async () => {
      try {
        // Wait a bit to ensure token is saved after login
        await new Promise(resolve => setTimeout(resolve, 200));
        
        const token = localStorage.getItem('access_token') || localStorage.getItem('token');
        if (!token) {
          if (!mounted) return;
          setError('Usuário não autenticado');
          setLoading(false);
          return;
        }

        const data = await fetchUserProfile();
        if (!mounted) return;
        setUser(data);
        setError(null);
      } catch (e: any) {
        if (!mounted) return;
        console.error('Erro ao buscar perfil:', e);
        // Check if it's an authentication error
        if (e?.message?.includes('401') || e?.message?.includes('403')) {
          setError('Usuário não autenticado. Por favor, faça login novamente.');
          // Clear invalid token
          localStorage.removeItem('access_token');
          localStorage.removeItem('refresh_token');
          localStorage.removeItem('token');
        } else {
          setError(e?.message || 'Falha ao carregar perfil');
        }
      } finally {
        if (mounted) setLoading(false);
      }
    })();

    return () => {
      mounted = false;
    };
  }, []);

  const formatAddress = (address: string) => {
    if (!address) return '';
    return `${address.slice(0, 6)}...${address.slice(-4)}`;
  };

  const getUserDisplayName = () => {
    if (!user) return '';
    if (user.first_name && user.last_name) {
      return `${user.first_name} ${user.last_name}`;
    }
    return user.username;
  };

  if (loading) {
    return (
      <div className="relative w-full">
        <div className="relative h-64 lg:h-80 overflow-hidden">
          <ImageWithFallback
            src="https://collectibles.habbo.com/hero-bg-xl.png"
            alt="Profile cover"
            className="w-full h-full object-cover opacity-50"
          />
          <div className="absolute inset-0 bg-gradient-to-t from-black/60 via-black/20 to-transparent" />
          <div className="absolute inset-0 bg-muted/30" />
        </div>
        <div className="container mx-auto px-4 lg:px-8">
          <div className="relative mt-8 lg:mt-12">
            <div className="flex flex-col items-center gap-6">
              <Skeleton className="w-32 h-32 lg:w-40 lg:h-40 rounded-2xl" />
              <Skeleton className="h-8 w-48" />
              <Skeleton className="h-6 w-32" />
            </div>
          </div>
        </div>
      </div>
    );
  }

  if (error || !user) {
    return (
      <div className="container mx-auto px-4 lg:px-8 py-16">
        <div className="text-center">
          <h2 className="text-2xl font-bold mb-4">Erro ao carregar perfil</h2>
          <p className="text-muted-foreground">{error || 'Usuário não encontrado'}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="relative w-full">
      {/* Cover Image */}
      <div className="relative h-64 lg:h-80 overflow-hidden">
        <ImageWithFallback
          src="https://collectibles.habbo.com/hero-bg-xl.png"
          alt="Profile cover"
          className="w-full h-full object-cover"
        />
        <div className="absolute inset-0 bg-gradient-to-t from-black/60 via-black/20 to-transparent" />
      </div>

      {/* Profile Info */}
      <div className="container mx-auto px-4 lg:px-8 pb-16 lg:pb-24">
        <div className="relative mt-8 lg:mt-12">
          <div className="flex flex-col items-center gap-6">
            {/* Profile Picture - Centered */}
            <div className="relative">
              <div className="w-32 h-32 lg:w-40 lg:h-40 rounded-2xl overflow-hidden border-4 border-background bg-card">
                <ImageWithFallback
                  src={user.nick_habbo ? `https://www.habbo.com.br/habbo-imaging/avatarimage?&user=${encodeURIComponent(user.nick_habbo)}&action=std&direction=4&head_direction=4&img_format=png&gesture=std&headonly=1&size=b` : ''}
                  alt={getUserDisplayName()}
                  className="w-full h-full object-cover"
                />
              </div>
            </div>

            {/* User Details - Centered */}
            <div className="text-center space-y-2">
              <h1 className="text-3xl lg:text-4xl font-bold">{getUserDisplayName()}</h1>
              {user.wallet_address && (
                <p className="text-lg text-muted-foreground font-mono pb-4">
                  {formatAddress(user.wallet_address)}
                </p>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

