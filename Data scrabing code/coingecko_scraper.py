import csv
import os
import time
from datetime import datetime
from typing import Dict, List, Optional

import requests


COINGECKO_HEADERS = [
    "timestamp",
    "coingecko_fetched_at",
    "contract_address",
    "cg_name",
    "cg_symbol",
    "cg_price_usd",
    "cg_market_cap",
    "cg_market_cap_rank",
    "cg_fdv",
    "cg_total_volume_24h",
    "cg_high_24h",
    "cg_low_24h",
    "cg_price_change_pct_24h",
    "cg_market_cap_change_24h",
    "cg_market_cap_change_pct_24h",
    "cg_circulating_supply",
    "cg_total_supply",
    "cg_max_supply",
    "cg_ath",
    "cg_ath_change_pct",
    "cg_ath_date",
    "cg_atl",
    "cg_atl_change_pct",
    "cg_atl_date",
    "cg_homepage",
]


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


def _safe_get(data: Dict, default="NA", *keys):
    current = data
    for key in keys:
        if not isinstance(current, dict):
            return default
        current = current.get(key, default)
    return default if current is None else current


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

    market_data = _safe_get(data, {}, "market_data")

    return {
        "name": _safe_get(data, "NA", "name"),
        "symbol": (_safe_get(data, "NA", "symbol") or "").upper(),
        "price_usd": fmt_price(_safe_get(market_data, "NA", "current_price", "usd")),
        "market_cap": fmt_money(_safe_get(market_data, "NA", "market_cap", "usd")),
        "market_cap_rank": _safe_get(data, "NA", "market_cap_rank"),
        "fdv": fmt_money(_safe_get(market_data, "NA", "fully_diluted_valuation", "usd")),
        "total_volume": fmt_money(_safe_get(market_data, "NA", "total_volume", "usd")),
        "high_24h": fmt_price(_safe_get(market_data, "NA", "high_24h", "usd")),
        "low_24h": fmt_price(_safe_get(market_data, "NA", "low_24h", "usd")),
        "price_change_pct_24h": fmt_pct(_safe_get(market_data, "NA", "price_change_percentage_24h")),
        "mc_change_24h": fmt_money(_safe_get(market_data, "NA", "market_cap_change_24h")),
        "mc_change_pct_24h": fmt_pct(_safe_get(market_data, "NA", "market_cap_change_percentage_24h")),
        "circulating_supply": fmt_number(_safe_get(market_data, "NA", "circulating_supply")),
        "total_supply": fmt_number(_safe_get(market_data, "NA", "total_supply")),
        "max_supply": fmt_number(_safe_get(market_data, "NA", "max_supply")),
        "ath": fmt_price(_safe_get(market_data, "NA", "ath", "usd")),
        "ath_change_pct": fmt_pct(_safe_get(market_data, "NA", "ath_change_percentage", "usd")),
        "ath_date": fmt_date(_safe_get(market_data, "NA", "ath_date", "usd")),
        "atl": fmt_price(_safe_get(market_data, "NA", "atl", "usd")),
        "atl_change_pct": fmt_pct(_safe_get(market_data, "NA", "atl_change_percentage", "usd")),
        "atl_date": fmt_date(_safe_get(market_data, "NA", "atl_date", "usd")),
        "homepage": (
            _safe_get(data, [], "links", "homepage")[0]
            if isinstance(_safe_get(data, [], "links", "homepage"), list)
            and _safe_get(data, [], "links", "homepage")
            else "NA"
        ),
    }


def ensure_dataset(contract_address: str) -> str:
    filename = f"coingecko_{contract_address}.csv"
    if not os.path.exists(filename):
        with open(filename, "w", newline="", encoding="utf-8") as handle:
            writer = csv.writer(handle)
            writer.writerow(COINGECKO_HEADERS)
        print(f"[init] created {filename}")
    return filename


def append_row(filename: str, contract_address: str, cg_fields: Dict[str, str]) -> None:
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(filename, "a", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(
            [
                timestamp,
                timestamp,
                contract_address,
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
            ]
        )


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
    cg_client = CoinGeckoClient()
    files_map: Dict[str, str] = {addr: ensure_dataset(addr) for addr in token_addresses}

    try:
        while True:
            for idx, addr in enumerate(token_addresses, start=1):
                print(f"[fetch] ({idx}/{len(token_addresses)}) {addr} -> coingecko")
                try:
                    report = cg_client.fetch(addr)
                    if not report:
                        print(f"[warn] {addr}: no coingecko data")
                    else:
                        cg_fields = extract_coingecko_fields(report)
                        append_row(files_map[addr], addr, cg_fields)
                        print(f"[saved] {addr}: {cg_fields['price_usd']}")
                except Exception as exc:
                    print(f"[error] {addr}: {exc}")

                for _ in range(17):
                    time.sleep(1)
    except KeyboardInterrupt:
        print("[info] stopping coingecko scraper")


if __name__ == "__main__":
    main()

