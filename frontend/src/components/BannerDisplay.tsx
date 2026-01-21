import { useEffect, useState } from 'react';
import { fetchCollectionBanner, Banner } from '@/api/nft';

interface BannerDisplayProps {
  className?: string;
}

export function BannerDisplay({ className = '' }: BannerDisplayProps) {
  const [banner, setBanner] = useState<Banner | null>(null);
  const [loading, setLoading] = useState(false);

  // Carregar banner aleatório ao montar o componente (quando a página carrega)
  useEffect(() => {
    let mounted = true;
    setLoading(true);
    
    fetchCollectionBanner()
      .then((data) => {
        if (!mounted) return;
        setBanner(data);
      })
      .catch(() => {
        // Silenciosamente ignora erros - não mostra nada se não houver banners
        if (mounted) {
          setBanner(null);
        }
      })
      .finally(() => {
        if (mounted) {
          setLoading(false);
        }
      });
    
    return () => { mounted = false; };
  }, []);

  // Não exibe nada se não houver banner ou estiver carregando
  if (loading || !banner || !banner.image_url) {
    return null;
  }

  return (
    <div className={`text-center ${className}`}>
      <div className="relative w-full max-w-4xl mx-auto">
        <picture>
          <source
            media="(max-width: 768px)"
            srcSet={banner.image_mobile || banner.image_url}
          />
          <img 
            src={banner.image_url} 
            alt={banner.title}
            className="w-full rounded-lg shadow-lg"
            style={{ maxHeight: '300px', objectFit: 'contain' }}
          />
        </picture>
      </div>
    </div>
  );
}
