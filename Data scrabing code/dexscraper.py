import csv
import os
import re
import threading
import time
from datetime import datetime
from typing import Dict, List, Optional, Set

import requests
from bs4 import BeautifulSoup


CSV_HEADERS = [
    "Timestamp",
    "Token Address",
    "Name",
    "X Account",
    "Telegram",
    "Total Liquidity",
    "Liquidity Locked",
    "FDV",
    "Market Cap",
    "Price USD",
    "5m Change %",
    "1h Change %",
    "6h Change %",
    "24h Change %",
    "Pair Age (hours)",
    "Pooled SOL",
]

RUG_HEADERS = [
    "Rug Token Name",
    "Rug Token Symbol",
    "Rug Risk Score",
    "Rug Risk Assessment",
    "Rug Supply",
    "Rug Mint Authority",
    "Rug Freeze Authority",
    "Rug LP Locked %",
    "Rug Top 10 Holders %",
]

ALL_HEADERS = CSV_HEADERS + RUG_HEADERS

COINGECKO_HEADERS = [
    "CG Name",
    "CG Symbol",
    "CG Price USD",
    "CG Market Cap",
    "CG Market Cap Rank",
    "CG FDV",
    "CG Total Volume 24h",
    "CG High 24h",
    "CG Low 24h",
    "CG Price Change % 24h",
    "CG Market Cap Change 24h",
    "CG Market Cap Change % 24h",
    "CG Circulating Supply",
    "CG Total Supply",
    "CG Max Supply",
    "CG ATH",
    "CG ATH Change %",
    "CG ATH Date",
    "CG ATL",
    "CG ATL Change %",
    "CG ATL Date",
    "CG Homepage",
]

TELEGRAM_HEADERS = [
    "TG Channel",
    "TG Channel Title",
    "TG Subscribers",
    "TG Messages Analyzed",
    "TG Positive",
    "TG Negative",
    "TG Neutral",
    "TG Positive %",
    "TG Negative %",
    "TG Neutral %",
    "TG New Messages",
]

ALL_HEADERS = ALL_HEADERS + COINGECKO_HEADERS + TELEGRAM_HEADERS


class DexScreenerClient:
    """Lightweight client around the DexScreener public API."""

    BASE_URL = "https://api.dexscreener.com/latest/dex/tokens/{token_address}"

    def __init__(self) -> None:
        self.session = requests.Session()
        self.session.headers.update(
            {
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36"
                )
            }
        )

    def fetch_pair(self, token_address: str) -> Optional[Dict]:
        url = self.BASE_URL.format(token_address=token_address.strip())
        try:
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            payload = response.json()
        except requests.RequestException as exc:  # network or HTTP errors
            print(f"[warn] {token_address}: request failed: {exc}")
            return None
        except ValueError:
            print(f"[warn] {token_address}: invalid JSON from API")
            return None

        pairs = payload.get("pairs") or []
        if not pairs:
            print(f"[warn] {token_address}: no pairs returned")
            return None
        return pairs[0]


class RugCheckClient:
    """Client for RugCheck token reports."""

    BASE_URL = "https://api.rugcheck.xyz/v1/tokens/{token_address}/report"

    def __init__(self) -> None:
        self.session = requests.Session()
        self.session.headers.update(
            {
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36"
                )
            }
        )

    def fetch_report(self, token_address: str) -> Optional[Dict]:
        url = self.BASE_URL.format(token_address=token_address.strip())
        try:
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as exc:
            print(f"[warn] {token_address}: rugcheck request failed: {exc}")
        except ValueError:
            print(f"[warn] {token_address}: rugcheck invalid JSON")
        return None


class CoinGeckoClient:
    """Client for CoinGecko contract data (Solana network)."""

    BASE_URL = "https://api.coingecko.com/api/v3/coins/solana/contract/{contract}"

    def __init__(self) -> None:
        self.session = requests.Session()
        self.session.headers.update(
            {
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36"
                ),
                "Accept": "application/json",
            }
        )

    def fetch(self, contract_address: str) -> Optional[Dict]:
        url = self.BASE_URL.format(contract=contract_address.strip())
        try:
            response = self.session.get(url, timeout=20)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as exc:
            print(f"[warn] {contract_address}: coingecko request failed: {exc}")
        except ValueError:
            print(f"[warn] {contract_address}: coingecko invalid JSON")
        return None


# Sentiment keyword lists (simple substring matching)
POSITIVE_WORDS = [
    "bullish",
    "moon",
    "pump",
    "buy",
    "buying",
    "hold",
    "hodl",
    "long",
    "gem",
    "rocket",
    "🚀",
    "🌙",
    "💎",
    "🔥",
    "lambo",
    "profit",
    "gains",
    "up",
    "green",
    "win",
    "winner",
    "strong",
    "support",
    "love",
    "great",
    "amazing",
    "best",
    "good",
    "nice",
    "awesome",
    "excellent",
    "perfect",
    "bull",
    "breakout",
    "mooning",
    "pumping",
    "bullrun",
    "ath",
    "undervalued",
    "potential",
    "accumulate",
    "bullmarket",
    "to the moon",
    "lets go",
    "lfg",
    "based",
]


NEGATIVE_WORDS = [
    "bearish",
    "dump",
    "sell",
    "selling",
    "short",
    "crash",
    "scam",
    "rug",
    "rugpull",
    "down",
    "red",
    "loss",
    "lose",
    "losing",
    "bear",
    "dead",
    "shit",
    "trash",
    "bad",
    "worst",
    "terrible",
    "avoid",
    "warning",
    "danger",
    "overvalued",
    "bubble",
    "ponzi",
    "fake",
    "exit",
    "rekt",
    "bearmarket",
    "falling",
    "collapse",
    "scam",
]


class TelegramSentiment:
    """Scrapes public Telegram channel preview pages and infers simple sentiment."""

    def __init__(self) -> None:
        self.session = requests.Session()
        self.session.headers.update(
            {
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36"
                )
            }
        )
        self.seen_messages: Set[str] = set()
        self.first_run = True

    def _parse_number(self, text: str) -> int:
        if not text:
            return 0
        text = text.strip().upper().replace(",", "")
        match = re.search(r"([\d.]+)\s*([KMB])?", text)
        if not match:
            return 0
        try:
            number = float(match.group(1))
            suffix = match.group(2) or ""
            multipliers = {"K": 1_000, "M": 1_000_000, "B": 1_000_000_000}
            return int(number * multipliers.get(suffix, 1))
        except Exception:
            return 0

    def _normalize_username(self, telegram_field: str) -> Optional[str]:
        if not telegram_field or telegram_field == "NA":
            return None
        username = telegram_field.strip()
        if username.startswith("http") and "t.me/" in username:
            username = username.split("t.me/")[-1]
        if username.startswith("@"):  # strip @
            username = username[1:]
        if "/" in username:
            username = username.split("/")[0]
        username = username.strip()
        return username or None

    def _scrape_channel(self, username: str, fetch_more: bool) -> Optional[Dict]:
        base_url = f"https://t.me/s/{username}"
        pages = 5 if fetch_more else 1
        channel_title = "NA"
        subscribers = 0
        messages: List[str] = []

        for page in range(pages):
            url = base_url if page == 0 else f"{base_url}?before={page * 20}"
            try:
                resp = self.session.get(url, timeout=13)
            except requests.RequestException as exc:
                print(f"[warn] telegram request failed: {exc}")
                break

            if resp.status_code != 200:
                print(f"[warn] telegram HTTP {resp.status_code} for {username}")
                break

            soup = BeautifulSoup(resp.content, "html.parser")

            if page == 0:
                title_elem = soup.find("div", class_="tgme_channel_info_header_title")
                if title_elem:
                    channel_title = title_elem.get_text(strip=True)

                counter_elem = soup.find("div", class_="tgme_channel_info_counter")
                if counter_elem:
                    subscribers = self._parse_number(counter_elem.get_text(strip=True))

            for msg_div in soup.find_all("div", class_="tgme_widget_message_text"):
                message_text = msg_div.get_text(strip=True)
                if not message_text:
                    continue
                msg_id = message_text[:120]
                if msg_id in self.seen_messages:
                    continue
                self.seen_messages.add(msg_id)
                messages.append(message_text)

            if not fetch_more:
                break
            if page < pages - 1:
                time.sleep(1)

        return {
            "username": username,
            "channel_title": channel_title,
            "subscribers": subscribers,
            "messages": messages,
        }

    def _analyze(self, messages: List[str]) -> Dict[str, str]:
        if not messages:
            return {
                "messages_analyzed": 0,
                "positive": 0,
                "negative": 0,
                "neutral": 0,
                "positive_pct": "0%",
                "negative_pct": "0%",
                "neutral_pct": "0%",
                "new_messages": 0,
            }

        sentiments = []
        for msg in messages:
            msg_lower = msg.lower()
            pos_count = sum(1 for w in POSITIVE_WORDS if w in msg_lower)
            neg_count = sum(1 for w in NEGATIVE_WORDS if w in msg_lower)
            if pos_count > neg_count:
                sentiments.append("positive")
            elif neg_count > pos_count:
                sentiments.append("negative")
            else:
                sentiments.append("neutral")

        total = len(sentiments)
        positive = sentiments.count("positive")
        negative = sentiments.count("negative")
        neutral = sentiments.count("neutral")

        def pct(part: int) -> str:
            return f"{(part / total * 100):.1f}%" if total else "0%"

        return {
            "messages_analyzed": total,
            "positive": positive,
            "negative": negative,
            "neutral": neutral,
            "positive_pct": pct(positive),
            "negative_pct": pct(negative),
            "neutral_pct": pct(neutral),
            "new_messages": total,
        }

    def fetch_and_analyze(self, telegram_field: str) -> Dict[str, str]:
        username = self._normalize_username(telegram_field)
        if not username:
            return {
                "channel": "NA",
                "channel_title": "NA",
                "subscribers": 0,
                "messages_analyzed": 0,
                "positive": 0,
                "negative": 0,
                "neutral": 0,
                "positive_pct": "0%",
                "negative_pct": "0%",
                "neutral_pct": "0%",
                "new_messages": 0,
            }

        channel_data = self._scrape_channel(username, fetch_more=self.first_run)
        self.first_run = False
        if not channel_data:
            return {
                "channel": username,
                "channel_title": "NA",
                "subscribers": 0,
                "messages_analyzed": 0,
                "positive": 0,
                "negative": 0,
                "neutral": 0,
                "positive_pct": "0%",
                "negative_pct": "0%",
                "neutral_pct": "0%",
                "new_messages": 0,
            }

        sentiment = self._analyze(channel_data["messages"])
        return {
            "channel": username,
            "channel_title": channel_data["channel_title"],
            "subscribers": channel_data["subscribers"],
            **sentiment,
        }


class RedditSentiment:
    """No-op placeholder; Reddit sentiment removed."""

    def fetch_and_analyze(self, token_name: str, token_symbol: str = "") -> Dict[str, str]:
        return {
            "subs": "",
            "posts_analyzed": 0,
            "positive": 0,
            "negative": 0,
            "neutral": 0,
            "positive_pct": "0%",
            "negative_pct": "0%",
            "neutral_pct": "0%",
            "new_posts": 0,
        }


def _safe_get(data: Dict, default="NA", *keys):
    current = data
    for key in keys:
        if not isinstance(current, dict):
            return default
        current = current.get(key, default)
    return default if current is None else current


def format_money(value: Optional[float]) -> str:
    if value is None or value == 0:
        return "NA"
    try:
        return f"${float(value):,.2f}"
    except (TypeError, ValueError):
        return "NA"


def format_change(value: Optional[float]) -> str:
    if value is None:
        return "NA"
    try:
        return f"{float(value):.2f}%"
    except (TypeError, ValueError):
        return "NA"


def extract_fields(pair_data: Dict) -> Optional[Dict[str, str]]:
    if not pair_data:
        return None

    socials = _safe_get(pair_data, [], "info", "socials")
    x_account = "NA"
    telegram = "NA"
    if isinstance(socials, list):
        for social in socials:
            if not isinstance(social, dict):
                continue
            social_type = (social.get("type") or "").lower()
            url = social.get("url") or ""
            if social_type == "twitter":
                if "twitter.com/" in url:
                    x_account = "@" + url.rsplit("/", 1)[-1]
                elif "x.com/" in url:
                    x_account = "@" + url.rsplit("/", 1)[-1]
            elif social_type == "telegram":
                if "t.me/" in url:
                    telegram = "@" + url.rsplit("/", 1)[-1]
                else:
                    telegram = url

    liquidity_usd = _safe_get(pair_data, 0, "liquidity", "usd")
    liquidity_locked = "NA"
    boosts = pair_data.get("boosts") or {}
    if isinstance(boosts, dict) and boosts.get("active", 0) > 0:
        liquidity_locked = "Yes"

    fdv = _safe_get(pair_data, 0, "fdv")
    market_cap = _safe_get(pair_data, 0, "marketCap")

    price_usd = _safe_get(pair_data, "NA", "priceUsd")
    try:
        price_usd = f"${float(price_usd):.10f}" if price_usd != "NA" else "NA"
    except (TypeError, ValueError):
        price_usd = "NA"

    price_change = _safe_get(pair_data, {}, "priceChange")
    pair_created_at = _safe_get(pair_data, 0, "pairCreatedAt")
    pair_age_hours = "NA"
    if pair_created_at:
        try:
            created_dt = datetime.fromtimestamp(pair_created_at / 1000)
            pair_age_hours = f"{(datetime.now() - created_dt).total_seconds() / 3600:.1f}"
        except (TypeError, ValueError):
            pair_age_hours = "NA"

    pooled_sol = "NA"
    quote_symbol = _safe_get(pair_data, "", "quoteToken", "symbol")
    if quote_symbol == "SOL":
        quote_liquidity = _safe_get(pair_data, 0, "liquidity", "quote")
        try:
            pooled_sol = f"{float(quote_liquidity):.2f} SOL" if quote_liquidity else "NA"
        except (TypeError, ValueError):
            pooled_sol = "NA"

    return {
        "name": _safe_get(pair_data, "Unknown", "baseToken", "name"),
        "x_account": x_account,
        "telegram": telegram,
        "total_liquidity": format_money(liquidity_usd),
        "liquidity_locked": liquidity_locked,
        "fdv": format_money(fdv),
        "market_cap": format_money(market_cap),
        "price_usd": price_usd,
        "m5_change": format_change(_safe_get(price_change, None, "m5")),
        "h1_change": format_change(_safe_get(price_change, None, "h1")),
        "h6_change": format_change(_safe_get(price_change, None, "h6")),
        "h24_change": format_change(_safe_get(price_change, None, "h24")),
        "pair_age": pair_age_hours,
        "pooled_sol": pooled_sol,
    }


def extract_rug_fields(report: Optional[Dict]) -> Dict[str, str]:
    if not report:
        return {
            "token_name": "NA",
            "token_symbol": "NA",
            "risk_score": "NA",
            "risk_assessment": "NA",
            "supply": "NA",
            "mint_authority": "NA",
            "freeze_authority": "NA",
            "lp_locked_pct": "NA",
            "top_10_pct": "NA",
        }

    def safe_get(obj: Dict, default="NA", *keys):
        cur = obj
        for key in keys:
            if not isinstance(cur, dict):
                return default
            cur = cur.get(key, default)
        return default if cur is None else cur

    token_name = safe_get(report, "Unknown", "tokenMeta", "name")
    token_symbol = safe_get(report, "Unknown", "tokenMeta", "symbol")

    raw_scores = [
        safe_get(report, 0, "score"),
        safe_get(report, 0, "aggregate", "score"),
        safe_get(report, 0, "fileMeta", "score"),
    ]
    numeric_scores = [s for s in raw_scores if isinstance(s, (int, float))]
    risk_score = min(numeric_scores) if numeric_scores else 0
    if risk_score > 100:
        risk_score = min(int(risk_score / 50), 100)

    if risk_score <= 20:
        risk_assessment = "Good"
    elif risk_score <= 50:
        risk_assessment = "Neutral"
    elif risk_score <= 80:
        risk_assessment = "Warning"
    else:
        risk_assessment = "Bad"

    supply_raw = safe_get(report, 0, "token", "supply")
    decimals = safe_get(report, 9, "token", "decimals")
    supply = "NA"
    try:
        adjusted = float(supply_raw) / (10 ** int(decimals)) if supply_raw else 0
        if adjusted >= 1_000_000_000:
            supply = f"{adjusted/1_000_000_000:.1f}B"
        elif adjusted >= 1_000_000:
            supply = f"{adjusted/1_000_000:.1f}M"
        elif adjusted > 0:
            supply = f"{adjusted:,.0f}"
    except (TypeError, ValueError):
        supply = "NA"

    mint_authority = safe_get(report, None, "token", "mintAuthority")
    mint_authority = "Revoked" if not mint_authority or mint_authority == "null" else "Active"

    freeze_authority = safe_get(report, None, "token", "freezeAuthority")
    freeze_authority = "Revoked" if not freeze_authority or freeze_authority == "null" else "Active"

    markets = safe_get(report, [], "markets")
    total_lp_locked = 0.0
    lp_count = 0
    if isinstance(markets, list):
        for market in markets:
            pct = safe_get(market, 0, "lp", "lpLockedPct")
            try:
                pct_val = float(pct)
                total_lp_locked += pct_val
                lp_count += 1
            except (TypeError, ValueError):
                continue
    lp_locked_pct = f"{total_lp_locked / lp_count:.2f}%" if lp_count else "0%"

    top_holders = safe_get(report, [], "topHolders")
    top_10_pct_val = 0.0
    if isinstance(top_holders, list):
        for holder in top_holders[:10]:
            pct = safe_get(holder, 0, "pct")
            try:
                top_10_pct_val += float(pct)
            except (TypeError, ValueError):
                continue
    top_10_pct = f"{top_10_pct_val:.2f}%" if top_10_pct_val else "NA"

    return {
        "token_name": token_name,
        "token_symbol": token_symbol,
        "risk_score": str(risk_score) if risk_score != "NA" else "NA",
        "risk_assessment": risk_assessment,
        "supply": supply,
        "mint_authority": mint_authority,
        "freeze_authority": freeze_authority,
        "lp_locked_pct": lp_locked_pct,
        "top_10_pct": top_10_pct,
    }


def extract_coingecko_fields(data: Optional[Dict]) -> Dict[str, str]:
    if not data:
        return {
            "name": "NA",
            "symbol": "NA",
            "price_usd": "NA",
            "market_cap": "NA",
            "market_cap_rank": "NA",
            "fdv": "NA",
            "total_volume": "NA",
            "high_24h": "NA",
            "low_24h": "NA",
            "price_change_pct_24h": "NA",
            "mc_change_24h": "NA",
            "mc_change_pct_24h": "NA",
            "circulating_supply": "NA",
            "total_supply": "NA",
            "max_supply": "NA",
            "ath": "NA",
            "ath_change_pct": "NA",
            "ath_date": "NA",
            "atl": "NA",
            "atl_change_pct": "NA",
            "atl_date": "NA",
            "homepage": "NA",
        }

    def safe_get(obj, default="NA", *keys):
        cur = obj
        for key in keys:
            if not isinstance(cur, dict):
                return default
            cur = cur.get(key, default)
        return default if cur is None else cur

    def fmt_pct(val):
        if val in ("NA", None):
            return "NA"
        try:
            return f"{float(val):.2f}%"
        except (TypeError, ValueError):
            return "NA"

    def fmt_price(val):
        if val in ("NA", None):
            return "NA"
        try:
            return f"${float(val):.10f}"
        except (TypeError, ValueError):
            return "NA"

    def fmt_money(val):
        if val in ("NA", None):
            return "NA"
        try:
            num = float(val)
            if num >= 1_000_000_000:
                return f"${num/1_000_000_000:.2f}B"
            if num >= 1_000_000:
                return f"${num/1_000_000:.2f}M"
            if num >= 1_000:
                return f"${num/1_000:.2f}K"
            return f"${num:.2f}"
        except (TypeError, ValueError):
            return "NA"

    def fmt_number(val):
        if val in ("NA", None):
            return "NA"
        try:
            num = float(val)
            if num >= 1_000_000_000:
                return f"{num/1_000_000_000:.2f}B"
            if num >= 1_000_000:
                return f"{num/1_000_000:.2f}M"
            return f"{num:,.0f}"
        except (TypeError, ValueError):
            return "NA"

    def fmt_date(val):
        if val in ("NA", None):
            return "NA"
        try:
            return datetime.fromisoformat(val.replace("Z", "+00:00")).strftime("%Y-%m-%d")
        except Exception:
            return "NA"

    market_data = safe_get(data, {}, "market_data")

    return {
        "name": safe_get(data, "NA", "name"),
        "symbol": (safe_get(data, "NA", "symbol") or "").upper(),
        "price_usd": fmt_price(safe_get(market_data, "NA", "current_price", "usd")),
        "market_cap": fmt_money(safe_get(market_data, "NA", "market_cap", "usd")),
        "market_cap_rank": safe_get(data, "NA", "market_cap_rank"),
        "fdv": fmt_money(safe_get(market_data, "NA", "fully_diluted_valuation", "usd")),
        "total_volume": fmt_money(safe_get(market_data, "NA", "total_volume", "usd")),
        "high_24h": fmt_price(safe_get(market_data, "NA", "high_24h", "usd")),
        "low_24h": fmt_price(safe_get(market_data, "NA", "low_24h", "usd")),
        "price_change_pct_24h": fmt_pct(safe_get(market_data, "NA", "price_change_percentage_24h")),
        "mc_change_24h": fmt_money(safe_get(market_data, "NA", "market_cap_change_24h")),
        "mc_change_pct_24h": fmt_pct(safe_get(market_data, "NA", "market_cap_change_percentage_24h")),
        "circulating_supply": fmt_number(safe_get(market_data, "NA", "circulating_supply")),
        "total_supply": fmt_number(safe_get(market_data, "NA", "total_supply")),
        "max_supply": fmt_number(safe_get(market_data, "NA", "max_supply")),
        "ath": fmt_price(safe_get(market_data, "NA", "ath", "usd")),
        "ath_change_pct": fmt_pct(safe_get(market_data, "NA", "ath_change_percentage", "usd")),
        "ath_date": fmt_date(safe_get(market_data, "NA", "ath_date", "usd")),
        "atl": fmt_price(safe_get(market_data, "NA", "atl", "usd")),
        "atl_change_pct": fmt_pct(safe_get(market_data, "NA", "atl_change_percentage", "usd")),
        "atl_date": fmt_date(safe_get(market_data, "NA", "atl_date", "usd")),
        "homepage": (
            safe_get(data, [], "links", "homepage")[0]
            if isinstance(safe_get(data, [], "links", "homepage"), list)
            and safe_get(data, [], "links", "homepage")
            else "NA"
        ),
    }


def ensure_csv(token_address: str) -> str:
    filename = f"{token_address}.csv"
    if not os.path.exists(filename):
        with open(filename, "w", newline="", encoding="utf-8") as handle:
            writer = csv.writer(handle)
            writer.writerow(ALL_HEADERS)
        print(f"[init] created {filename}")
    return filename


def append_row(
    filename: str,
    token_address: str,
    dex_fields: Dict[str, str],
    rug_fields: Dict[str, str],
    cg_fields: Dict[str, str],
    tg_fields: Dict[str, str],
) -> None:
    with open(filename, "a", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(
            [
                datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                token_address,
                dex_fields["name"],
                dex_fields["x_account"],
                dex_fields["telegram"],
                dex_fields["total_liquidity"],
                dex_fields["liquidity_locked"],
                dex_fields["fdv"],
                dex_fields["market_cap"],
                dex_fields["price_usd"],
                dex_fields["m5_change"],
                dex_fields["h1_change"],
                dex_fields["h6_change"],
                dex_fields["h24_change"],
                dex_fields["pair_age"],
                dex_fields["pooled_sol"],
                rug_fields["token_name"],
                rug_fields["token_symbol"],
                rug_fields["risk_score"],
                rug_fields["risk_assessment"],
                rug_fields["supply"],
                rug_fields["mint_authority"],
                rug_fields["freeze_authority"],
                rug_fields["lp_locked_pct"],
                rug_fields["top_10_pct"],
                cg_fields["name"],
                cg_fields["symbol"],
                cg_fields["price_usd"],
                cg_fields["market_cap"],
                cg_fields["market_cap_rank"],
                cg_fields["fdv"],
                cg_fields["total_volume"],
                cg_fields["high_24h"],
                cg_fields["low_24h"],
                cg_fields["price_change_pct_24h"],
                cg_fields["mc_change_24h"],
                cg_fields["mc_change_pct_24h"],
                cg_fields["circulating_supply"],
                cg_fields["total_supply"],
                cg_fields["max_supply"],
                cg_fields["ath"],
                cg_fields["ath_change_pct"],
                cg_fields["ath_date"],
                cg_fields["atl"],
                cg_fields["atl_change_pct"],
                cg_fields["atl_date"],
                cg_fields["homepage"],
                tg_fields["channel"],
                tg_fields["channel_title"],
                tg_fields["subscribers"],
                tg_fields["messages_analyzed"],
                tg_fields["positive"],
                tg_fields["negative"],
                tg_fields["neutral"],
                tg_fields["positive_pct"],
                tg_fields["negative_pct"],
                tg_fields["neutral_pct"],
                tg_fields["new_messages"],
            ]
        )


class TokenWorker(threading.Thread):
    def __init__(
        self,
        token_address: str,
        client: DexScreenerClient,
        rug_client: RugCheckClient,
        cg_client: CoinGeckoClient,
        tg_helper: TelegramSentiment,
        iterations: int,
        interval_seconds: int,
        stop_event: threading.Event,
    ) -> None:
        super().__init__(daemon=True)
        self.token_address = token_address
        self.client = client
        self.rug_client = rug_client
        self.cg_client = cg_client
        self.tg_helper = tg_helper
        self.iterations = iterations
        self.interval_seconds = interval_seconds
        self.stop_event = stop_event
        self.filename = ensure_csv(token_address)

    def run(self) -> None:
        for i in range(1, self.iterations + 1):
            if self.stop_event.is_set():
                break
            pair = self.client.fetch_pair(self.token_address)
            dex_fields = extract_fields(pair) if pair else None
            rug_report = self.rug_client.fetch_report(self.token_address)
            rug_fields = extract_rug_fields(rug_report)
            cg_report = self.cg_client.fetch(self.token_address)
            cg_fields = extract_coingecko_fields(cg_report)
            tg_fields = self.tg_helper.fetch_and_analyze(dex_fields.get("telegram") if dex_fields else "NA")

            if dex_fields:
                append_row(
                    self.filename,
                    self.token_address,
                    dex_fields,
                    rug_fields,
                    cg_fields,
                    tg_fields,
                )
                print(
                    f"[{self.token_address}] saved iteration {i}/" f"{self.iterations}: {dex_fields['price_usd']}"
                )
            else:
                print(f"[{self.token_address}] iteration {i}: no dex data")

            if i < self.iterations:
                # Sleep in small slices so we can react to a stop signal.
                slept = 0
                while slept < self.interval_seconds and not self.stop_event.is_set():
                    time.sleep(1)
                    slept += 1


def prompt_token_addresses() -> List[str]:
    while True:
        try:
            count = int(input("How many token addresses? (1-10): ").strip())
        except ValueError:
            print("Enter a number between 1 and 10.")
            continue
        if 1 <= count <= 10:
            break
        print("Number must be between 1 and 10.")

    addresses: List[str] = []
    for idx in range(count):
        while True:
            address = input(f"Enter token address #{idx + 1}: ").strip()
            if address:
                addresses.append(address)
                break
            print("Address cannot be empty.")
    return addresses


def main() -> None:
    token_addresses = prompt_token_addresses()
    client = DexScreenerClient()
    rug_client = RugCheckClient()
    cg_client = CoinGeckoClient()

    iterations = 6000
    interval_seconds = 13
    stop_event = threading.Event()

    workers = [
        TokenWorker(
            addr,
            client,
            rug_client,
            cg_client,
            TelegramSentiment(),
            iterations,
            interval_seconds,
            stop_event,
        )
        for addr in token_addresses
    ]

    for worker in workers:
        worker.start()

    try:
        for worker in workers:
            worker.join()
    except KeyboardInterrupt:
        print("[info] stopping...")
        stop_event.set()
        for worker in workers:
            worker.join()

    print("[done] all workers finished")


if __name__ == "__main__":
    main()
