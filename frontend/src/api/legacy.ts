import { getJson, HttpParams } from './client';
import { Paginated } from './nft';

export interface LegacyItem {
  id: number;
  name: string;
  slug: string;
  image_url: string;
  description?: string | null;
  last_price: number;
  average_price: number;
  available_offers: number;
  can_buy_multiple?: boolean;
  price_history?: any;
  created_at: string;
  updated_at: string;
}

// GET /legacy/ with filters, search and ordering
export function fetchLegacyItems(params?: HttpParams) {
  return getJson<Paginated<LegacyItem>>(`/legacy/`, params);
}

// GET /legacy/<slug>/
export function fetchLegacyItem(slug: string) {
  return getJson<LegacyItem>(`/legacy/${encodeURIComponent(slug)}/`);
}

