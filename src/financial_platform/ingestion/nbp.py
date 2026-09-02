from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
import httpx
import pandas as pd


class NBPClient:
    base_url = "https://api.nbp.pl/api"

    def fetch_fx(self, currency: str, start: date, end: date) -> pd.DataFrame:
        rows: list[dict] = []
        cursor = start
        # NBP limits one range request to 93 days.
        while cursor <= end:
            chunk_end = min(cursor + timedelta(days=92), end)
            url = f"{self.base_url}/exchangerates/rates/a/{currency.lower()}/{cursor}/{chunk_end}/"
            response = httpx.get(url, params={"format": "json"}, timeout=30.0)
            response.raise_for_status()
            for item in response.json().get("rates", []):
                obs_date = date.fromisoformat(item["effectiveDate"])
                available_at = datetime.combine(obs_date, datetime.min.time(), tzinfo=timezone.utc)
                rows.append({
                    "series_code": f"FX_{currency.upper()}_PLN",
                    "name": f"{currency.upper()}/PLN - kurs średni NBP",
                    "unit": "PLN",
                    "frequency": "daily",
                    "source_code": "NBP",
                    "observation_date": obs_date,
                    "value": float(item["mid"]),
                    "publication_date": available_at,
                    "available_at": available_at,
                })
            cursor = chunk_end + timedelta(days=1)
        return pd.DataFrame(rows)
