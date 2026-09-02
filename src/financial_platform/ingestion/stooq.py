from __future__ import annotations
from datetime import date
from io import StringIO
import httpx
import pandas as pd

from financial_platform.config.settings import get_settings


class StooqClient:
    """Supplementary Stooq adapter.

    Automated CSV downloads require an API key in 2026. Set STOOQ_API_KEY in .env.
    """
    base_url = "https://stooq.pl/q/d/l/"

    def fetch_daily(self, ticker: str, start: date, end: date) -> pd.DataFrame:
        key = get_settings().stooq_api_key
        if not key:
            raise RuntimeError("STOOQ_API_KEY is not configured. Use Yahoo ingestion or add the Stooq key to .env.")
        params = {
            "s": ticker.lower(), "d1": start.strftime("%Y%m%d"),
            "d2": end.strftime("%Y%m%d"), "i": "d", "apikey": key,
        }
        r = httpx.get(self.base_url, params=params, timeout=30.0)
        r.raise_for_status()
        if "Get your apikey" in r.text or "Exceeded the daily hits limit" in r.text:
            raise RuntimeError(f"Stooq rejected the request: {r.text[:160]}")
        df = pd.read_csv(StringIO(r.text))
        rename = {
            "Data":"trade_date", "Otwarcie":"open", "Najwyzszy":"high",
            "Najnizszy":"low", "Zamkniecie":"close", "Wolumen":"volume",
            "Date":"trade_date", "Open":"open", "High":"high", "Low":"low",
            "Close":"close", "Volume":"volume",
        }
        df = df.rename(columns=rename)
        if "trade_date" not in df:
            raise ValueError("Unexpected Stooq CSV schema")
        return df[[c for c in ["trade_date","open","high","low","close","volume"] if c in df.columns]].copy()
