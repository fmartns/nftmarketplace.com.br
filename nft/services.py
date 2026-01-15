from __future__ import annotations

import json
import logging
from decimal import Decimal, ROUND_HALF_UP
from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime, timedelta, timezone

import requests
from .models import PricingConfig, NFTItem
import time
from random import random


logger = logging.getLogger(__name__)


IMMUTABLE_BASE_URL = "https://api.x.immutable.com/v3/orders"

DEFAULT_MARKUP_MULTIPLIER = Decimal("1.30")

# Simple in-process cache for rates to avoid frequent 429s and reduce latency
_RATES_CACHE: Optional[Tuple[Decimal, Decimal, float]] = (
    None  # (eth_usd, usd_brl, expires_at_epoch)
)
_RATES_TTL_SECONDS = 600.0  # 10 minutes - reduz chamadas à API e evita rate limiting


def _get_markup_multiplier_for(product_code: Optional[str]) -> Decimal:
    """Return the price multiplier based on per-item or global markup.
    If an item has markup_percent (e.g., 30.00), uses (1 + 30/100).
    Else uses PricingConfig.global_markup_percent; fallback to DEFAULT_MARKUP_MULTIPLIER if none.
    """
    try:
        if product_code:
            item = (
                NFTItem.objects.filter(product_code=product_code)
                .only("markup_percent")
                .first()
            )
            if item and item.markup_percent is not None:
                return Decimal("1") + (Decimal(item.markup_percent) / Decimal("100"))
        cfg = (
            PricingConfig.objects.order_by("-updated_at")
            .only("global_markup_percent")
            .first()
        )
        if cfg and cfg.global_markup_percent is not None:
            return Decimal("1") + (Decimal(cfg.global_markup_percent) / Decimal("100"))
    except Exception:
        pass
    return DEFAULT_MARKUP_MULTIPLIER


class ImmutableAPIError(Exception):
    """Raised when Immutable API returns a non-success status code."""


def _get_json_with_retries(
    url: str,
    *,
    params: Optional[Dict[str, Any]] = None,
    headers: Optional[Dict[str, str]] = None,
    timeout: int = 30,
    retries: int = 4,
    backoff_factor: float = 0.5,
    status_forcelist: Tuple[int, ...] = (429, 500, 502, 503, 504),
) -> Optional[Any]:
    """Perform GET with basic retries and exponential backoff.
    Returns parsed JSON on success, or None on repeated failure.
    """
    attempt = 0
    # Perform up to `retries` attempts total
    while attempt < retries:
        try:
            base_headers = {
                "Accept": "application/json",
                "User-Agent": "nft-portal/1.0",
            }
            merged_headers = {**base_headers, **(headers or {})}
            resp = requests.get(
                url, params=params, headers=merged_headers, timeout=timeout
            )
            if resp.status_code == 200:
                try:
                    return resp.json()
                except Exception as je:  # malformed JSON
                    logger.warning("JSON decode failed from %s: %s", url, je)
                    return None
            if resp.status_code in status_forcelist:
                # Backoff and retry
                sleep_s = backoff_factor * (2**attempt) + (random() * 0.1)
                logger.warning(
                    "HTTP %s from %s; retrying in %.2fs (attempt %d/%d)",
                    resp.status_code,
                    url,
                    sleep_s,
                    attempt + 1,
                    retries,
                )
                time.sleep(sleep_s)
                attempt += 1
                continue
            # HTTP 400 (Bad Request) - pode ser parâmetros inválidos, não retry
            if resp.status_code == 400:
                logger.warning(
                    "HTTP 400 from %s; not retrying (bad request - check parameters)",
                    url,
                )
                # Log response body for debugging
                try:
                    error_body = resp.text[:500]  # First 500 chars
                    logger.debug("HTTP 400 response body: %s", error_body)
                except Exception:
                    pass
                return None
            # Non-retriable status
            logger.warning("HTTP %s from %s; not retrying", resp.status_code, url)
            return None
        except Exception as e:
            # Network error; retry with backoff
            sleep_s = backoff_factor * (2**attempt) + (random() * 0.1)
            logger.warning(
                "GET failed %s: %s; retrying in %.2fs (attempt %d/%d)",
                url,
                e,
                sleep_s,
                attempt + 1,
                retries,
            )
            time.sleep(sleep_s)
            attempt += 1
    return None


def get_current_rates() -> Tuple[Decimal, Decimal]:
    """
    Fetch current conversion rates.

    Returns tuple (eth_usd, usd_brl) as Decimals.
    On failure, returns fallback values.
    """
    # Serve from cache if valid
    global _RATES_CACHE
    now = time.time()
    if _RATES_CACHE is not None:
        eth_usd_cached, usd_brl_cached, exp = _RATES_CACHE
        if now < exp:
            return eth_usd_cached, usd_brl_cached
    eth_usd: Optional[Decimal] = None
    usd_brl: Optional[Decimal] = None

    try:
        data = _get_json_with_retries(
            "https://api.coingecko.com/api/v3/simple/price",
            params={"ids": "ethereum", "vs_currencies": "usd"},
            timeout=10,
            retries=3,
            backoff_factor=0.6,
        )
        if isinstance(data, dict):
            val = (data.get("ethereum") or {}).get("usd")
            if val is not None:
                eth_usd = Decimal(str(val))
    except Exception as e:  # noqa: BLE001 - network exceptions are varied
        logger.warning("CoinGecko fetch failed: %s", e)

    # AwesomeAPI USD -> BRL
    try:
        data = _get_json_with_retries(
            "https://economia.awesomeapi.com.br/json/last/USD-BRL",
            timeout=10,
            retries=5,
            backoff_factor=0.6,
        )
        if isinstance(data, dict):
            bid = (data.get("USDBRL") or {}).get("bid")
            if bid is not None:
                usd_brl = Decimal(str(bid))
    except Exception as e:  # noqa: BLE001
        logger.warning("AwesomeAPI fetch failed: %s", e)

    # Fallbacks if any are missing
    if eth_usd is None:
        eth_usd = Decimal("4713.59")
    if usd_brl is None:
        usd_brl = Decimal("5.42")
    # Update cache
    _RATES_CACHE = (eth_usd, usd_brl, now + _RATES_TTL_SECONDS)
    return eth_usd, usd_brl


def _wei_to_eth(wei: int) -> Decimal:
    """Convert Wei to ETH using Decimal with high precision."""
    return (Decimal(wei) / Decimal("1e18")).quantize(Decimal("0.000000000000000001"))


def _extract_buy_info(order: Dict[str, Any]) -> Tuple[str, int, int, Optional[str]]:
    """Return (buy_type, quantity_int, decimals, token_address) from order.buy.
    buy_type is expected to be 'ETH' or 'ERC20'.
    quantity_int is the integer representation of the on-chain amount (no decimals applied).
    decimals indicates the number of decimals for the buy token (18 for ETH; often 6 for USDC-like tokens).
    token_address when present for ERC20 tokens.
    """
    buy = order.get("buy", {})
    buy_type = (buy.get("type") or buy.get("data", {}).get("type") or "").upper()
    data = buy.get("data", {})
    # Prefer taker price (quantity_with_fees) to mirror frontend logic
    raw = data.get("quantity_with_fees") or data.get("quantity")
    quantity_int = int(str(raw)) if raw is not None else 0
    decimals = int(data.get("decimals") or (18 if buy_type == "ETH" else 6))
    token_address = data.get("token_address")
    return buy_type, quantity_int, decimals, token_address


def _convert_order_to_prices(
    order: Dict[str, Any],
    eth_usd: Decimal,
    usd_brl: Decimal,
    *,
    product_code: Optional[str] = None,
) -> Optional[Tuple[Decimal, Decimal, Decimal]]:
    """Return last_price_eth, last_price_usd, last_price_brl (all with markup applied) for the given order.
    Supports:
      - ETH-denominated orders (18 decimals, convert via eth_usd)
      - ERC20 stablecoins with 6 decimals (treated as USD directly)
    Returns None when token type is unsupported.
    """
    try:
        buy_type, qty_int, decimals, _ = _extract_buy_info(order)
        if qty_int <= 0:
            return None

        if buy_type == "ETH":
            eth_raw = _wei_to_eth(qty_int)  # full precision (1e-18)
            # Use float math to mimic JS toFixed pipeline before rounding
            usd_pre = float(eth_raw) * float(eth_usd)
            brl_pre = usd_pre * float(usd_brl)
            price_usd = Decimal(str(usd_pre)).quantize(
                Decimal("0.01"), rounding=ROUND_HALF_UP
            )
            price_brl_pre = Decimal(str(brl_pre)).quantize(
                Decimal("0.01"), rounding=ROUND_HALF_UP
            )
            # Frontend parity: if ETH amount is meaningful but BRL looks implausibly small (e.g., cents),
            # recompute BRL using fallback rates so we never show R$ 0,xx for ~0.07 ETH.
            try:
                if eth_raw > Decimal("0.01") and price_brl_pre < Decimal("10"):
                    fallback_eth_usd = Decimal("4713.59")
                    fallback_usd_brl = Decimal("5.42")
                    brl_fb = (
                        float(eth_raw)
                        * float(fallback_eth_usd)
                        * float(fallback_usd_brl)
                    )
                    price_brl_pre = Decimal(str(brl_fb)).quantize(
                        Decimal("0.01"), rounding=ROUND_HALF_UP
                    )
            except Exception:
                pass
        elif buy_type == "ERC20" and decimals == 6:
            # Treat 6-decimal ERC20 as USD stablecoin (e.g., USDC/USDT)
            amount_usd = Decimal(qty_int) / (Decimal(10) ** Decimal(decimals))
            # Use float math to mimic JS toFixed before rounding
            usd_pre = float(amount_usd)
            brl_pre = usd_pre * float(usd_brl)
            price_usd = Decimal(str(usd_pre)).quantize(
                Decimal("0.01"), rounding=ROUND_HALF_UP
            )
            # Derive synthetic ETH for consistency
            price_eth = (price_usd / eth_usd).quantize(
                Decimal("0.000000000000000001"), rounding=ROUND_HALF_UP
            )
            price_brl_pre = Decimal(str(brl_pre)).quantize(
                Decimal("0.01"), rounding=ROUND_HALF_UP
            )
        else:
            # Unsupported token type/decimals for now
            return None

        # Apply markup using admin-configured multiplier (round after applying)
        mult = _get_markup_multiplier_for(product_code)
        # ETH: apply markup to raw ETH then quantize to 8 decimals for output
        if buy_type == "ETH":
            price_eth_out = (eth_raw * mult).quantize(
                Decimal("0.00000001"), rounding=ROUND_HALF_UP
            )
        else:
            price_eth_out = (price_eth * mult).quantize(
                Decimal("0.00000001"), rounding=ROUND_HALF_UP
            )
        price_usd_out = (price_usd * mult).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )
        price_brl_out = (price_brl_pre * mult).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )

        return price_eth_out, price_usd_out, price_brl_out
    except Exception:
        return None


def pick_best_bid_order(
    orders: List[Dict[str, Any]],
    eth_usd: Decimal,
    usd_brl: Decimal,
    *,
    product_code: Optional[str] = None,
) -> Tuple[Optional[Dict[str, Any]], Optional[Tuple[Decimal, Decimal, Decimal]]]:
    """Select the order with the lowest BRL price, prioritizing ETH-denominated orders.
    Returns (best_order, (price_eth, price_usd, price_brl)) with markup applied, or (None, None).

    Rationale: Frontend listing cards generally reflect ETH listings; including non-ETH tokens
    (e.g., ERC20 with unusual decimals) has led to implausibly low backend prices. To keep the
    product page price consistent with visible offers, we restrict selection to ETH orders.
    """
    best_order: Optional[Dict[str, Any]] = None
    best_prices: Optional[Tuple[Decimal, Decimal, Decimal]] = None
    best_brl: Optional[Decimal] = None

    for order in orders:
        try:
            buy_type, _, _, _ = _extract_buy_info(order)
        except Exception:
            buy_type = ""
        if buy_type != "ETH":
            # Skip non-ETH orders to avoid inconsistencies with listing display
            continue
        prices = _convert_order_to_prices(
            order, eth_usd, usd_brl, product_code=product_code
        )
        if prices is None:
            continue
        _, _, brl = prices
        if best_brl is None or brl < best_brl:
            best_order = order
            best_prices = prices
            best_brl = brl

    # If no ETH orders found, fall back to previous behavior across supported currencies
    if best_order is None:
        for order in orders:
            prices = _convert_order_to_prices(
                order, eth_usd, usd_brl, product_code=product_code
            )
            if prices is None:
                continue
            _, _, brl = prices
            if best_brl is None or brl < best_brl:
                best_order = order
                best_prices = prices
                best_brl = brl

    if best_order is not None and best_prices is not None:
        try:
            buy_type, _, _, _ = _extract_buy_info(best_order)
        except Exception:
            buy_type = ""
        logger.info(
            "pick_best_bid_order: selected buy_type=%s brl=%s",
            buy_type,
            (best_prices[2] if best_prices else None),
        )
    else:
        logger.info("pick_best_bid_order: no suitable order found")
    return best_order, best_prices


def _get_prop(root: Dict[str, Any], key: str, default: Any = "") -> Any:
    props = root.get("sell", {}).get("data", {}).get("properties", {})
    return props.get(key, default)


def map_order_to_item_fields(
    order: Optional[Dict[str, Any]],
    product_code: str,
    eth_usd: Decimal,
    usd_brl: Decimal,
    override_prices: Optional[Tuple[Decimal, Decimal, Decimal]] = None,
) -> Dict[str, Any]:
    """
    Map Immutable order JSON to our NFTItem fields dict.
    If order is None, returns a default structure with zeroed prices.
    """
    name = _get_prop(order or {}, "name", default=product_code)
    image_url = _get_prop(order or {}, "image_url", default="")
    blueprint = _get_prop(order or {}, "blueprint", default="")
    text_type = _get_prop(order or {}, "type", default="unknown")
    rarity = _get_prop(order or {}, "rarity", default="")
    item_type = _get_prop(order or {}, "itemType", default="")
    item_sub_type = _get_prop(order or {}, "itemSubType", default="")
    product_type = _get_prop(order or {}, "productType", default="")
    material = _get_prop(order or {}, "material", default="")
    is_crafted_item = bool(_get_prop(order or {}, "isCraftedItem", default=False))
    is_craft_material = bool(_get_prop(order or {}, "isCraftMaterial", default=False))

    number_val = _get_prop(order or {}, "number", default=None)
    try:
        number = int(number_val) if number_val is not None else None
    except Exception:
        number = None

    if override_prices is not None:
        price_eth, price_usd, price_brl = override_prices
    else:
        price_eth = Decimal("0")
        if order:
            # Try to convert based on buy leg; fallback to ETH path
            conv = _convert_order_to_prices(
                order, eth_usd, usd_brl, product_code=product_code
            )
            if conv is not None:
                price_eth, price_usd, price_brl = conv
            else:
                # Legacy path based on _price_wei when available
                if "_price_wei" in order:
                    price_eth = _wei_to_eth(int(order["_price_wei"]))
                    price_usd = (price_eth * eth_usd).quantize(
                        Decimal("0.01"), rounding=ROUND_HALF_UP
                    )
                    price_brl = (price_usd * usd_brl).quantize(
                        Decimal("0.01"), rounding=ROUND_HALF_UP
                    )
                    # Apply markup (legacy path)
                    mult = _get_markup_multiplier_for(product_code)
                    price_eth = (price_eth * mult).quantize(
                        Decimal("0.000000000000000001")
                    )
                    price_usd = (price_usd * mult).quantize(
                        Decimal("0.01"), rounding=ROUND_HALF_UP
                    )
                    price_brl = (price_brl * mult).quantize(
                        Decimal("0.01"), rounding=ROUND_HALF_UP
                    )
                else:
                    price_usd = Decimal("0")
                    price_brl = Decimal("0")

    mapped = {
        "name": name or product_code,
        "type": text_type or "unknown",
        "blueprint": blueprint or "",
        "image_url": image_url or "",
        "source": "immutable_bids",
        "is_crafted_item": is_crafted_item,
        "is_craft_material": is_craft_material,
        "rarity": rarity or "",
        "item_type": item_type or "",
        "item_sub_type": item_sub_type or "",
        "number": number,
        "product_code": product_code,
        "product_type": product_type or "",
        "material": material or "",
        "last_price_eth": price_eth,
        "last_price_usd": price_usd,
        "last_price_brl": price_brl,
    }

    return mapped


def _paginate_immutable(
    params: Dict[str, Any], headers: Dict[str, str], max_pages: int = 50
) -> List[Dict[str, Any]]:
    """Fetch all pages from Immutable orders endpoint using cursor."""
    all_results: List[Dict[str, Any]] = []
    cursor: Optional[str] = None
    for _ in range(max_pages):
        page_params = params.copy()
        if cursor:
            page_params["cursor"] = cursor
        data = _get_json_with_retries(
            IMMUTABLE_BASE_URL,
            params=page_params,
            headers=headers,
            timeout=30,
            retries=4,
        )
        if not isinstance(data, dict):
            break
        items = data.get("result") or []
        all_results.extend(items)
        # Handle cursors that can be either strings or nested objects
        next_cursor = data.get("next_cursor")

        def _nc(obj: Any) -> Optional[str]:
            if isinstance(obj, dict):
                return obj.get("next_cursor")
            return None

        cursor = (
            next_cursor
            or _nc(data.get("cursor"))
            or _nc(data.get("page_cursor"))
            or _nc(data.get("page"))
        )
        if not cursor:
            break
    return all_results


def fetch_7d_sales_stats(product_code: str) -> Dict[str, Any]:
    """
    Compute 7-day sales stats (volume, count, avg, last sale, change %) for a product_code
    using filled orders from Immutable.
    """
    now = datetime.now(timezone.utc)
    seven_days_ago = now - timedelta(days=7)
    headers = {"Accept": "application/json", "Content-Type": "application/json"}
    params = {
        "status": "filled",
        # Do not restrict buy token type; we will normalize to BRL
        "sell_metadata": json.dumps({"productCode": [product_code]}),
        "order_by": "buy_quantity",
        "direction": "asc",
        "page_size": 200,
        # Not all deployments may support this filter; we add but still filter client-side
        "updated_min_timestamp": int(seven_days_ago.timestamp()),
    }

    try:
        results = _paginate_immutable(params, headers)
    except Exception:
        results = []

    # Rates for conversion
    eth_usd, usd_brl = get_current_rates()

    sales: List[Tuple[datetime, Decimal]] = []  # (timestamp, price_brl_with_markup)
    for o in results:
        try:
            # Try to derive a timestamp from fields
            ts = None
            for key in (
                "updated_timestamp",
                "timestamp",
                "created_timestamp",
                "filled_timestamp",
            ):
                val = o.get(key)
                if val is None:
                    continue
                if isinstance(val, (int, float)):
                    ts_candidate = datetime.fromtimestamp(float(val), tz=timezone.utc)
                else:
                    # string: numeric seconds or ISO
                    s = str(val)
                    if s.isdigit():
                        ts_candidate = datetime.fromtimestamp(float(s), tz=timezone.utc)
                    else:
                        try:
                            ts_candidate = datetime.fromisoformat(
                                s.replace("Z", "+00:00")
                            )
                        except Exception:
                            continue
                ts = ts_candidate
                break
            if not ts or ts < seven_days_ago:
                continue

            conv = _convert_order_to_prices(
                o, eth_usd, usd_brl, product_code=product_code
            )
            if conv is None:
                continue
            _, _, price_brl = conv
            sales.append((ts, price_brl))
        except Exception:
            continue

    sales.sort(key=lambda x: x[0])

    count = len(sales)
    volume_brl = sum((p for _, p in sales), Decimal("0")) if count else Decimal("0")
    avg_brl = (
        (volume_brl / count).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        if count
        else Decimal("0")
    )
    last_brl = sales[-1][1] if count else Decimal("0")
    change_pct = Decimal("0")
    if count >= 2 and sales[0][1] > 0:
        change_pct = ((last_brl - sales[0][1]) / sales[0][1] * Decimal("100")).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )

    return {
        "seven_day_volume_brl": volume_brl,
        "seven_day_sales_count": count,
        "seven_day_avg_price_brl": avg_brl,
        "seven_day_last_sale_brl": last_brl,
        "seven_day_price_change_pct": change_pct,
        "seven_day_updated_at": now,
    }


def fetch_item_from_immutable(
    product_code: str,
) -> Tuple[Dict[str, Any], Optional[str]]:
    """
    Orchestrates fetching orders for the given product_code from Immutable,
    picking the best order, converting prices, and mapping to NFTItem fields.
    """
    if not product_code or not str(product_code).strip():
        raise ValueError("product_code inválido")

    params = {
        "status": "active",
        # Don't fix buy token type; we'll normalize below
        "sell_metadata": json.dumps({"productCode": [product_code]}),
        "order_by": "buy_quantity",
        "direction": "asc",
        "page_size": 200,
    }
    headers = {"Accept": "application/json", "Content-Type": "application/json"}

    # Try with ordering; if fails, retry without ordering constraints
    try_variants = [
        params,
        {k: v for k, v in params.items() if k not in ("order_by", "direction")},
    ]
    results: List[Dict[str, Any]] = []
    last_err: Optional[Exception] = None
    for pp in try_variants:
        try:
            results = _paginate_immutable(pp, headers)
            if results:
                break
            # Even if empty list, confirm the call works by doing a single page fetch
            data = _get_json_with_retries(
                IMMUTABLE_BASE_URL, params=pp, headers=headers, timeout=30, retries=4
            )
            if isinstance(data, dict):
                results = data.get("result") or []
                break
        except Exception as e:
            last_err = e
            continue
    if results is None and last_err is not None:
        logger.error("Immutable pagination error for %s: %s", product_code, last_err)
        raise ImmutableAPIError("Erro ao consultar a Immutable") from last_err

    eth_usd, usd_brl = get_current_rates()
    best, prices = pick_best_bid_order(
        results, eth_usd, usd_brl, product_code=product_code
    )
    mapped = map_order_to_item_fields(
        best, product_code, eth_usd, usd_brl, override_prices=prices
    )

    # Extract possible collection contract address from the best order
    collection_address: Optional[str] = None
    try:
        if best:
            sell_data = best.get("sell", {}).get("data", {})
            addr = (
                sell_data.get("token_address")
                or sell_data.get("contract_address")
                or sell_data.get("token_address_hex")
            )
            if not addr:
                addr = _get_prop(best, "collectionAddress", default="")
            if isinstance(addr, str) and addr:
                collection_address = addr
    except Exception:
        collection_address = None

    logger.info(
        "fetch_item: product_code=%s status=200 orders=%s eth=%s usd=%s brl=%s",
        product_code,
        len(results),
        mapped.get("last_price_eth"),
        mapped.get("last_price_usd"),
        mapped.get("last_price_brl"),
    )

    return mapped, collection_address


def fetch_min_listing_prices(
    product_code: str,
) -> Optional[Tuple[Decimal, Decimal, Decimal]]:
    """Fetch all active orders and return the minimum (eth, usd, brl) with markup applied,
    mirroring frontend listing conversions.

    This uses the same pagination, conversion, and pick_best_bid_order logic as
    fetch_item_from_immutable, ensuring parity with the product page's displayed price.
    """
    if not product_code or not str(product_code).strip():
        return None

    params = {
        "status": "active",
        "sell_metadata": json.dumps({"productCode": [product_code]}),
        "order_by": "buy_quantity",
        "direction": "asc",
        "page_size": 200,
    }
    headers = {"Accept": "application/json", "Content-Type": "application/json"}

    try_variants = [
        params,
        {k: v for k, v in params.items() if k not in ("order_by", "direction")},
    ]
    results: List[Dict[str, Any]] = []
    for pp in try_variants:
        try:
            results = _paginate_immutable(pp, headers)
            if results:
                break
            data = _get_json_with_retries(
                IMMUTABLE_BASE_URL, params=pp, headers=headers, timeout=30, retries=4
            )
            if isinstance(data, dict):
                results = data.get("result") or []
                break
        except Exception:
            continue

    eth_usd, usd_brl = get_current_rates()
    # Compute minimum across all supported orders by BRL (with markup), mirroring frontend listing map
    best_prices: Optional[Tuple[Decimal, Decimal, Decimal]] = None
    best_brl: Optional[Decimal] = None
    for o in results:
        conv = _convert_order_to_prices(o, eth_usd, usd_brl, product_code=product_code)
        if conv is None:
            continue
        _, _, brl = conv
        if best_brl is None or brl < best_brl:
            best_brl = brl
            best_prices = conv
    return best_prices
