import { useEffect } from 'react';

interface SEOData {
  title?: string;
  description?: string;
  image?: string;
  url?: string;
  type?: string;
}

export function useSEO(data: SEOData) {
  useEffect(() => {
    const { title, description, image, url, type = 'website' } = data;
    
    // URL atual (usar a fornecida ou a atual da página)
    const currentUrl = url || (typeof window !== 'undefined' ? window.location.href : '');
    const baseUrl = typeof window !== 'undefined' ? window.location.origin : '';
    
    // Atualizar title
    if (title) {
      document.title = title;
    }
    
    // Função auxiliar para atualizar ou criar meta tag
    const updateMetaTag = (property: string, content: string, isProperty = false) => {
      const selector = isProperty ? `meta[property="${property}"]` : `meta[name="${property}"]`;
      let meta = document.querySelector(selector) as HTMLMetaElement;
      
      if (!meta) {
        meta = document.createElement('meta');
        if (isProperty) {
          meta.setAttribute('property', property);
        } else {
          meta.setAttribute('name', property);
        }
        document.head.appendChild(meta);
      }
      meta.setAttribute('content', content);
    };
    
    // Meta description
    if (description) {
      updateMetaTag('description', description);
    }
    
    // Open Graph tags
    if (title) {
      updateMetaTag('og:title', title, true);
    }
    if (description) {
      updateMetaTag('og:description', description, true);
    }
    if (image) {
      // Garantir URL absoluta para imagens
      const imageUrl = image.startsWith('http') ? image : `${baseUrl}${image}`;
      updateMetaTag('og:image', imageUrl, true);
    }
    if (currentUrl) {
      updateMetaTag('og:url', currentUrl, true);
    }
    updateMetaTag('og:type', type, true);
    
    // Twitter Card tags
    if (title) {
      updateMetaTag('twitter:title', title);
    }
    if (description) {
      updateMetaTag('twitter:description', description);
    }
    if (image) {
      // Garantir URL absoluta para imagens
      const imageUrl = image.startsWith('http') ? image : `${baseUrl}${image}`;
      updateMetaTag('twitter:image', imageUrl);
    }
    updateMetaTag('twitter:card', 'summary_large_image');
    
    // Cleanup: restaurar valores padrão quando o componente desmontar
    return () => {
      document.title = 'NFT Marketplace - Compre e Venda NFTs Habbo';
      const defaultFavicon = '/favicon.png';
      const faviconSelectors = [
        "link[rel='icon']",
        "link[rel='shortcut icon']"
      ];
      
      faviconSelectors.forEach(selector => {
        let link = document.querySelector(selector) as HTMLLinkElement;
        if (link) {
          link.href = defaultFavicon;
        }
      });
    };
  }, [data]);
}
