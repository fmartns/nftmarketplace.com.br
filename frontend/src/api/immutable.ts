// Frontend helper to fetch Immutable orders for a productCode and convert prices to ETH/USD/BRL
// Mirrors backend logic in nft/services.py

import { getJson } from './client';
import { fetchPricingConfig, PricingConfig } from './nft';

export interface ImmutableOrder {
  buy?: { type?: string; data?: { type?: string; quantity?: string; quantity_with_fees?: string; decimals?: number; token_address?: string } };
  sell?: { data?: { properties?: Record<string, any>; token_address?: string; token_id?: string } };
  [k: string]: any;
}

export interface Rates {
  eth_usd: number;
  usd_brl: number;
}

export interface ImmutableItemView {
  name: string;
  image_url: string;
  product_code: string;
  rarity?: string;
  item_type?: string;
  item_sub_type?: string;
  material?: string;
  number?: number | null;
  last_price_eth: number;
  last_price_usd: number;
  last_price_brl: number;
  attributes?: Array<{ trait: string; value: string }>; // generic attributes extracted from properties
}

const IMMUTABLE_BASE_URL = 'https://api.x.immutable.com/v3/orders';

function weiToEth(wei: string | number): number {
  const s = typeof wei === 'number' ? Math.trunc(wei).toString() : String(wei).trim();
  if (!/^-?\d+$/.test(s)) return 0;
  const negative = s.startsWith('-');
  const raw = negative ? s.slice(1) : s;
  // remove leading zeros
  const digits = raw.replace(/^0+/, '') || '0';
  const len = digits.length;
  let intPart = '0';
  let fracPart = '0'.repeat(18);
  if (len > 18) {
    intPart = digits.slice(0, len - 18);
    fracPart = digits.slice(len - 18);
  } else {
    intPart = '0';
    fracPart = digits.padStart(18, '0');
  }
  // Trim trailing zeros in fractional for parseFloat stability
  const trimmedFrac = fracPart.replace(/0+$/, '');
  const out = trimmedFrac.length > 0 ? `${negative ? '-' : ''}${intPart}.${trimmedFrac}` : `${negative ? '-' : ''}${intPart}`;
  const num = parseFloat(out);
  return isFinite(num) ? num : 0;
}

function ercAmount(raw: string | number, decimals = 18): number {
  const n = typeof raw === 'string' ? Number(raw) : raw;
  if (!isFinite(n) || decimals <= 0) return 0;
  return n / Math.pow(10, decimals);
}

function pickBestBidOrder(orders: ImmutableOrder[]): { order: ImmutableOrder | null; priceWei: number } {
  // Use BigInt for precise comparison of wei amounts to avoid float precision issues
  let best: ImmutableOrder | null = null;
  let bestWeiBI: bigint | null = null;
  for (const o of orders || []) {
    const q = o?.buy?.data?.quantity_with_fees || o?.buy?.data?.quantity;
    if (!q) continue;
    try {
      const bi = BigInt(String(q));
      if (bestWeiBI === null || bi < bestWeiBI) {
        best = o;
        bestWeiBI = bi;
      }
    } catch {
      // ignore malformed quantity
    }
  }
  if (bestWeiBI === null) return { order: null, priceWei: 0 };
  // Convert to number safely by going through string-based ETH conversion
  return { order: best, priceWei: Number(bestWeiBI.toString()) };
}

export async function getRates(): Promise<Rates> {
  // Fetch CoinGecko and AwesomeAPI in parallel with fallbacks
  const [cg, br] = await Promise.allSettled([
    fetch('https://api.coingecko.com/api/v3/simple/price?ids=ethereum&vs_currencies=usd', {
      headers: { Accept: 'application/json' },
      referrerPolicy: 'strict-origin-when-cross-origin',
    }).then(r => r.ok ? r.json() : Promise.reject(r.status)),
    fetch('https://economia.awesomeapi.com.br/json/last/USD-BRL', {
      headers: { Accept: 'application/json' },
      referrerPolicy: 'strict-origin-when-cross-origin',
    }).then(r => r.ok ? r.json() : Promise.reject(r.status)),
  ]);

  const eth_usd = (cg.status === 'fulfilled' ? Number(cg.value?.ethereum?.usd) : NaN) || 4713.59;
  const usd_brl = (br.status === 'fulfilled' ? Number(br.value?.USDBRL?.bid) : NaN) || 5.42;
  return { eth_usd, usd_brl };
}

// Cache for pricing config to avoid frequent API calls
let pricingConfigCache: { config: PricingConfig | null; timestamp: number } = {
  config: null,
  timestamp: 0
};

const PRICING_CONFIG_CACHE_TTL = 1 * 1000; // 1 second for testing

// Function to clear pricing config cache (useful for testing)
export function clearPricingConfigCache(): void {
  pricingConfigCache = {
    config: null,
    timestamp: 0
  };
  console.log('Pricing config cache cleared');
}

// Debug function to test pricing config API directly
export async function debugPricingConfig(): Promise<void> {
  console.log('=== DEBUG PRICING CONFIG ===');
  try {
    const config = await fetchPricingConfig();
    console.log('Direct API call result:', config);
    console.log('Markup percent:', config.global_markup_percent);
    console.log('Multiplier:', 1 + (config.global_markup_percent / 100));
  } catch (error) {
    console.error('API call failed:', error);
  }
  
  console.log('Current cache:', pricingConfigCache);
  console.log('Cache TTL:', PRICING_CONFIG_CACHE_TTL);
  console.log('========================');
}

// Make debug function available globally for console testing
if (typeof window !== 'undefined') {
  (window as any).debugPricingConfig = debugPricingConfig;
  (window as any).clearPricingConfigCache = clearPricingConfigCache;
}

export async function getPricingConfig(productCode?: string): Promise<PricingConfig> {
  const now = Date.now();
  
  // Return cached config if still valid (cache key includes productCode)
  const cacheKey = productCode || 'global';
  if (pricingConfigCache.config && (now - pricingConfigCache.timestamp) < PRICING_CONFIG_CACHE_TTL) {
    console.log('Using cached pricing config:', pricingConfigCache.config);
    return pricingConfigCache.config;
  }
  
  try {
    console.log('Fetching fresh pricing config from API...', productCode ? `for ${productCode}` : 'global');
    const config = await fetchPricingConfig(productCode);
    console.log('Fresh pricing config received:', config);
    pricingConfigCache = {
      config,
      timestamp: now
    };
    return config;
  } catch (error) {
    console.error('Failed to fetch pricing config, using fallback:', error);
    // Fallback to default markup if API fails
    const fallbackConfig: PricingConfig = {
      global_markup_percent: 30.00,
      updated_at: new Date().toISOString()
    };
    return fallbackConfig;
  }
}

function mapOrderToItem(order: ImmutableOrder | null, productCode: string, rates: Rates, markupMultiplier: number = 1.3): ImmutableItemView {
  const props = (order?.sell?.data?.properties as Record<string, any>) || {};
  const name = props.name || productCode;
  const image_url = props.image_url || '';
  const rarity = props.rarity || '';
  const item_type = props.itemType || '';
  const item_sub_type = props.itemSubType || '';
  const material = props.material || '';
  const number = props.number != null ? Number(props.number) : null;
  const attributes: Array<{ trait: string; value: string }> = Object.entries(props)
    .filter(([k]) => !['name', 'image_url', 'rarity', 'itemType', 'itemSubType', 'material', 'number'].includes(k))
    .map(([trait, value]) => ({ trait, value: String(value) }));

  const buyType = String(order?.buy?.type || order?.buy?.data?.type || '').toUpperCase();
  const rawQty = order?.buy?.data?.quantity_with_fees || order?.buy?.data?.quantity || '0';
  const decimals = Number(order?.buy?.data?.decimals ?? (buyType === 'ETH' ? 18 : 6));
  let priceEth = 0;
  let priceUsd = 0;
  let priceBrl = 0;
  const FALLBACK_RATES: Rates = { eth_usd: 4713.59, usd_brl: 5.42 };
  let ethRaw = 0; // pre-markup ETH for sanity checks
  if (buyType === 'ETH') {
    const eth = weiToEth(rawQty);
    priceEth = eth;
    ethRaw = eth;
    // Single-step conversion ETH -> BRL to avoid any intermediate rounding loss
    priceBrl = +(eth * rates.eth_usd * rates.usd_brl).toFixed(2);
    priceUsd = +(eth * rates.eth_usd).toFixed(2);
  } else if (buyType === 'ERC20' && decimals === 6) {
    // Treat 6-decimal ERC20 as USD stablecoin
    const usd = ercAmount(rawQty, 6);
    priceUsd = +usd.toFixed(2);
    priceEth = +(usd / rates.eth_usd).toFixed(8);
    priceBrl = +(usd * rates.usd_brl).toFixed(2);
  } else {
    // Unsupported token; leave zeros
  }
  // Apply configured markup across all prices
  priceEth = +(priceEth * markupMultiplier).toFixed(8);
  priceUsd = +(priceUsd * markupMultiplier).toFixed(2);
  priceBrl = +(priceBrl * markupMultiplier).toFixed(2);

  // Sanity fallback: if ETH amount is meaningful but BRL looks implausibly small (e.g., cents),
  // recompute BRL using fallback rates so we never show R$ 0,xx for ~0.07 ETH.
  if (buyType === 'ETH' && ethRaw > 0.01 && priceBrl < 10) {
    const brlNoMarkup = ethRaw * FALLBACK_RATES.eth_usd * FALLBACK_RATES.usd_brl;
    priceBrl = +(brlNoMarkup * markupMultiplier).toFixed(2);
  }

  return {
    name,
    image_url,
    product_code: productCode,
    rarity,
    item_type,
    item_sub_type,
    material,
    number,
    last_price_eth: +priceEth.toFixed(8),
    last_price_usd: priceUsd,
    last_price_brl: priceBrl,
    attributes,
  };
}

export async function fetchImmutableItem(productCode: string): Promise<ImmutableItemView> {
  // Fetch all pages and pick the best order across the full set
  const orders = await fetchAllOrders(productCode);
  const { order } = pickBestBidOrder(orders);
  const [rates, pricingConfig] = await Promise.all([
    getRates(),
    getPricingConfig(productCode)
  ]);
  
  // Get markup multiplier (e.g., 1.15 for 15% markup)
  const markupMultiplier = 1 + (pricingConfig.global_markup_percent / 100);
  console.log('fetchImmutableItem - Pricing config:', pricingConfig);
  console.log('fetchImmutableItem - Markup multiplier:', markupMultiplier, '(markup:', pricingConfig.global_markup_percent + '%)');
  
  const mapped = mapOrderToItem(order, productCode, rates, markupMultiplier);
  return mapped;
}

export interface ImmutableListingView {
  id: string;
  price_eth: number;
  price_usd: number;
  price_brl: number;
  quantity: number;
  expiration: string | null; // ISO or humanized
  seller: string | null; // wallet
  token_address?: string | null;
  token_id?: string | null;
}

export async function fetchImmutableListings(productCode: string): Promise<ImmutableListingView[]> {
  // Fetch all pages using cursor to avoid divergences in totals
  const orders = await fetchAllOrders(productCode);
  const [rates, pricingConfig] = await Promise.all([
    getRates(),
    getPricingConfig(productCode)
  ]);
  
  // Get markup multiplier (e.g., 1.10 for 10% markup)
  const markupMultiplier = 1 + (pricingConfig.global_markup_percent / 100);
  console.log('Pricing config:', pricingConfig);
  console.log('Markup multiplier:', markupMultiplier, '(markup:', pricingConfig.global_markup_percent + '%)');
  
  // Rates fetched and applied silently
  const listings: ImmutableListingView[] = orders.map((o: any) => {
    const buyType = String(o?.buy?.type || o?.buy?.data?.type || '').toUpperCase();
    // Prefer quantity_with_fees when available (taker price)
    const q = o?.buy?.data?.quantity_with_fees || o?.buy?.data?.quantity || '0';
  const decimals = Number(o?.buy?.data?.decimals ?? (buyType === 'ETH' ? 18 : 6));
    let eth = 0, usd = 0, brl = 0;
    let ethRaw = 0; // pre-markup ETH for sanity checks
    
    if (buyType === 'ETH') {
      ethRaw = weiToEth(q);
      // Calcular preços e arredondar (igual ao backend: quantize antes de aplicar markup)
      const usdPre = +(ethRaw * rates.eth_usd).toFixed(2);
      const brlPre = +(usdPre * rates.usd_brl).toFixed(2);
      // Sanity fallback: se ETH é significativo mas BRL parece muito baixo
      let brlPreFinal = brlPre;
      if (ethRaw > 0.01 && brlPre < 10) {
        const brlFb = ethRaw * 4713.59 * 5.42;
        brlPreFinal = +brlFb.toFixed(2);
      }
      // Aplicar markup DEPOIS de arredondar (igual ao backend)
      eth = +(ethRaw * markupMultiplier).toFixed(8);
      usd = +(usdPre * markupMultiplier).toFixed(2);
      brl = +(brlPreFinal * markupMultiplier).toFixed(2);
    } else if (buyType === 'ERC20' && decimals === 6) {
      // Calcular preços e arredondar (igual ao backend: quantize antes de aplicar markup)
      const usdPre = +ercAmount(q, 6).toFixed(2);
      const brlPre = +(usdPre * rates.usd_brl).toFixed(2);
      // Aplicar markup DEPOIS de arredondar (igual ao backend)
      usd = +(usdPre * markupMultiplier).toFixed(2);
      eth = +(usd / rates.eth_usd).toFixed(8);
      brl = +(brlPre * markupMultiplier).toFixed(2);
    }
    const quantity = 1; // generally 1 per unique NFT
    const seller = o?.user || o?.seller || null;
    const rawExp = o?.expiration_timestamp ?? o?.expiry ?? o?.expiration ?? null;
    let expiration: string | null = null;
    if (rawExp !== null && rawExp !== undefined) {
      let d: Date | null = null;
      if (typeof rawExp === 'number') {
        // Assume seconds; if it looks like ms (>= 10^12), use directly
        const ms = rawExp >= 1e12 ? rawExp : rawExp * 1000;
        d = new Date(ms);
      } else if (typeof rawExp === 'string') {
        if (/^\d+(\.\d+)?$/.test(rawExp)) {
          const num = parseFloat(rawExp);
          const ms = num >= 1e12 ? num : num * 1000;
          d = new Date(ms);
        } else {
          // Try ISO/RFC date string
          const t = Date.parse(rawExp);
          if (!isNaN(t)) d = new Date(t);
        }
      }
      if (d && !isNaN(d.getTime())) {
        expiration = d.toISOString();
      }
    }
    return {
      id: String(o?.order_id ?? o?.id ?? Math.random()),
      price_eth: +eth.toFixed(8),
      price_usd: usd,
      price_brl: brl,
      quantity,
      expiration,
      seller,
      token_address: o?.sell?.data?.token_address ?? null,
      token_id: o?.sell?.data?.token_id ?? null,
    };
  });
  return listings;
}

// Helper to paginate through all orders using cursor
export async function fetchAllOrders(
  productCode: string,
  pageSize: number = 200,
  maxPages: number = 50
): Promise<ImmutableOrder[]> {
  const baseParams = new URLSearchParams({
    status: 'active',
    // don't restrict buy token type; normalize client-side
    sell_metadata: JSON.stringify({ productCode: [productCode] }),
    order_by: 'buy_quantity',
    direction: 'asc',
    page_size: String(pageSize),
  });

  let cursor: string | null = null;
  const all: ImmutableOrder[] = [];
  for (let i = 0; i < maxPages; i++) {
    const params = new URLSearchParams(baseParams);
    if (cursor) params.set('cursor', cursor);
    const url = `${IMMUTABLE_BASE_URL}?${params.toString()}`;
  // Fetch silently
    const resp = await fetch(url, {
      headers: { Accept: 'application/json', 'Content-Type': 'application/json' },
      referrerPolicy: 'strict-origin-when-cross-origin',
    });
    if (!resp.ok) throw new Error(`Immutable HTTP ${resp.status}`);
    const data = await resp.json();
    const orders: ImmutableOrder[] = data?.result || [];
    all.push(...orders);

    // Try to read next cursor from different possible shapes
    const next: string | undefined =
      data?.next_cursor ||
      data?.cursor?.next ||
      data?.cursor?.next_cursor ||
      data?.page_cursor?.next_cursor ||
      data?.page?.next_cursor;

    if (next && typeof next === 'string' && next.length > 0) {
      cursor = next;
    } else {
      break;
    }
  }
  // Fallback: if nothing came back, try restricting to ETH to handle API quirks
  if (all.length === 0) {
    let cursor: string | null = null;
    for (let i = 0; i < maxPages; i++) {
  const params = new URLSearchParams(baseParams);
  params.set('buy_token_type', 'ETH');
      if (cursor) params.set('cursor', cursor);
      const url = `${IMMUTABLE_BASE_URL}?${params.toString()}`;
  // Fallback fetch silently
      const resp = await fetch(url, {
        headers: { Accept: 'application/json', 'Content-Type': 'application/json' },
        referrerPolicy: 'strict-origin-when-cross-origin',
      });
      if (!resp.ok) break;
      const data = await resp.json();
      const orders: ImmutableOrder[] = data?.result || [];
      all.push(...orders);
      const next: string | undefined =
        data?.next_cursor ||
        data?.cursor?.next ||
        data?.cursor?.next_cursor ||
        data?.page_cursor?.next_cursor ||
        data?.page?.next_cursor;
      if (next && typeof next === 'string' && next.length > 0) {
        cursor = next;
      } else {
        break;
      }
    }
  }
  return all;
}

// Fetch a single asset from Immutable v1 to obtain canonical metadata/attributes
export interface ImmutableAsset {
  token_address: string;
  token_id: string;
  name?: string | null;
  image_url?: string | null;
  metadata?: Record<string, any> | null;
}

export async function fetchImmutableAsset(token_address: string, token_id: string): Promise<ImmutableAsset | null> {
  if (!token_address || !token_id) return null;
  const url = `https://api.immutable.com/v1/assets/${encodeURIComponent(token_address)}/${encodeURIComponent(token_id)}`;
  const resp = await fetch(url, { headers: { Accept: 'application/json' } });
  if (!resp.ok) return null;
  const data = await resp.json();
  return {
    token_address: data?.token_address ?? token_address,
    token_id: data?.token_id ?? token_id,
    name: data?.name ?? data?.metadata?.name ?? null,
    image_url: data?.image_url ?? data?.metadata?.image_url ?? null,
    metadata: data?.metadata ?? null,
  };
}

export function metadataToAttributes(meta?: Record<string, any> | null): Array<{ trait: string; value: string }> {
  if (!meta) return [];
  const omit = new Set(['name', 'image_url', 'productCode', 'productType']);
  return Object.entries(meta)
    .filter(([k, v]) => !omit.has(k) && v !== undefined && v !== null && v !== '')
    .map(([trait, value]) => ({ trait, value: String(value) }));
}
