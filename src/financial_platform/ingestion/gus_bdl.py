from __future__ import annotations

from datetime import datetime, timezone
import httpx
import pandas as pd


class GUSBDLClient:
    """Generic GUS BDL adapter.

    Variable IDs are intentionally configuration-driven because BDL contains thousands
    of series and the exact variable chosen for the thesis must be documented.
    """
    base_url = "https://bdl.stat.gov.pl/api/v1"

    def __init__(self, client_id: str | None = None):
        self.headers = {"X-ClientId": client_id} if client_id else {}

    def fetch_poland_variable(self, variable_id: int, years: list[int], series_code: str, name: str, unit: str = "") -> pd.DataFrame:
        params: list[tuple[str, str | int]] = [("format", "json"), ("unit-level", 0), ("page-size", 100)]
        params.extend(("year", year) for year in years)
        url = f"{self.base_url}/data/by-variable/{variable_id}"
        response = httpx.get(url, params=params, headers=self.headers, timeout=30.0)
        response.raise_for_status()
        payload = response.json()
        rows: list[dict] = []
        for result in payload.get("results", []):
            for value in result.get("values", []):
                year = int(value["year"])
                # BDL annual observations: available_at is marked as ingestion-time proxy.
                available = datetime.now(timezone.utc)
                rows.append({
                    "series_code": series_code,
                    "name": name,
                    "unit": unit,
                    "frequency": "annual",
                    "source_code": "GUS_BDL",
                    "observation_date": f"{year}-12-31",
                    "value": value.get("val"),
                    "publication_date": None,
                    "available_at": available,
                })
        return pd.DataFrame(rows)
