import { getJson, HttpParams, postJson } from './client';

// Banner API types
export interface Banner {
  id: number;
  title: string;
  image_url: string;
  image_mobile?: string | null;
  order: number;
  created_at: string;
  updated_at: string;
}

// Collections API types (mirror gallery serializers)
export interface NftCollection {
  id: number;
  name: string;
  slug: string;
  description: string;
  address: string;
  profile_image: string;
  cover_image: string;
  creator: number | null;
  creator_name: string;
  author: string;
  items_count: number;
  owners_count: number;
  floor_price: string; // numeric string from backend
  floor_price_eth: string;
  total_volume: string;
  total_volume_eth: string;
  metadata_api_url: string;
  project_id: number | null;
  project_owner_address: string;
  website_url: string;
  twitter_url: string;
  instagram_url: string;
  discord_url: string;
  telegram_url: string;
  created_at: string;
  updated_at: string;
}

export interface Paginated<T> {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
}

export interface NFTItem {
  id: number;
  name: string; // pt-BR when available, otherwise English
  original_name?: string | null; // original English name
  name_pt_br?: string | null;
  product_code: string | null;
  image_url: string;
  rarity: string;
  item_type: string;
  item_sub_type: string;
  material: string;
  last_price_brl: string | null; // numeric string
  updated_at: string;
  collection?: number | null;
  // convenience fields from serializer
  collection_slug?: string | null;
  collection_name?: string | null;
  // seven-day metrics (numeric strings)
  seven_day_volume_brl?: string | null;
  seven_day_sales_count?: number | null;
  seven_day_avg_price_brl?: string | null;
  seven_day_last_sale_brl?: string | null;
  seven_day_price_change_pct?: string | null;
}

// GET /collections/ with optional search (?q=)
export function fetchCollections(params?: { q?: string }) {
  return getJson<NftCollection[]>(`/collections/`, params as HttpParams);
}

// GET /collections/<slug>/
export function fetchCollectionDetail(slug: string) {
  return getJson<NftCollection>(`/collections/${encodeURIComponent(slug)}/`);
}

// GET /nft/items/ with filters, search and ordering
export function fetchNFTItems(params?: HttpParams) {
  return getJson<Paginated<NFTItem>>(`/nft/items/`, params);
}

// GET /nft/items/?product_code=... (first result)
export async function fetchNFTByProductCode(product_code: string): Promise<NFTItem | null> {
  const res = await getJson<Paginated<NFTItem>>(`/nft/items/`, { product_code, page_size: 1 });
  return (res.results && res.results.length > 0) ? res.results[0] : null;
}

// POST /nft/ to upsert a single item by product_code
export function upsertNFTByProductCode(product_code: string) {
  return postJson<NFTItem>(`/nft/`, { product_code });
}

// POST /nft/items/view/ to record access for trending
export function recordNFTView(params: { product_code?: string; item_id?: number }) {
  return postJson<{ ok: boolean }>(`/nft/items/view/`, params);
}

// GET /nft/trending/?limit=4 to fetch most-accessed recent items
export function fetchTrendingByAccess(params?: { limit?: number; days?: number }) {
  return getJson<{ results: NFTItem[] }>(`/nft/trending/`, params as HttpParams);
}

// Pricing configuration API types
export interface PricingConfig {
  global_markup_percent: number;
  updated_at: string;
}

// GET /nft/pricing-config/ to fetch pricing configuration
export function fetchPricingConfig(productCode?: string) {
  const url = productCode 
    ? `/nft/pricing-config/?product_code=${encodeURIComponent(productCode)}`
    : `/nft/pricing-config/`;
  return getJson<PricingConfig>(url);
}

// Banner API types and functions
export interface Banner {
  id: number;
  title: string;
  image_url: string;
  image_mobile?: string | null;
  order: number;
  created_at: string;
  updated_at: string;
}

// GET /api/banners/collection/ to fetch collection banner
export function fetchCollectionBanner() {
  return getJson<Banner>(`/api/banners/collection/`);
}

// GET /api/banners/ to fetch all active banners
export function fetchBanners() {
  return getJson<Banner[]>(`/api/banners/`);
}
