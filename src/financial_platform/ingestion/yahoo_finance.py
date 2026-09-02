from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

import pandas as pd
import yfinance as yf


@dataclass(frozen=True)
class FinancialConceptSpec:
    code: str
    candidates: tuple[str, ...]


CONCEPTS = (
    FinancialConceptSpec("REVENUE", ("Total Revenue", "Operating Revenue")),
    FinancialConceptSpec("NET_INCOME_PARENT", ("Net Income Common Stockholders", "Net Income")),
    FinancialConceptSpec("OPERATING_PROFIT", ("Operating Income",)),
    FinancialConceptSpec("EBITDA", ("EBITDA", "Normalized EBITDA")),
    FinancialConceptSpec("TOTAL_ASSETS", ("Total Assets",)),
    FinancialConceptSpec("EQUITY", ("Stockholders Equity", "Total Equity Gross Minority Interest")),
    FinancialConceptSpec("OPERATING_CASH_FLOW", ("Operating Cash Flow", "Total Cash From Operating Activities")),
)


class YahooFinanceClient:
    """Pragmatic public-data adapter used by the prototype.

    Yahoo Finance is not the final authoritative source for the thesis. The loader keeps
    source metadata so values can later be verified/replaced with issuer/ESPI/ESEF data.
    """

    def history(self, symbol: str, start: str, end: str) -> pd.DataFrame:
        frame = yf.Ticker(symbol).history(start=start, end=end, auto_adjust=False, actions=False)
        if frame.empty:
            return frame
        frame = frame.reset_index()
        frame.columns = [str(c) for c in frame.columns]
        return frame.rename(columns={
            "Date": "trade_date", "Open": "open", "High": "high", "Low": "low",
            "Close": "close", "Adj Close": "adjusted_close", "Volume": "volume",
        })

    def quarterly_facts(self, symbol: str) -> pd.DataFrame:
        ticker = yf.Ticker(symbol)
        statements = {
            "income": ticker.quarterly_income_stmt,
            "balance": ticker.quarterly_balance_sheet,
            "cashflow": ticker.quarterly_cashflow,
        }
        frames: list[pd.DataFrame] = []
        for statement_name, statement in statements.items():
            if statement is None or statement.empty:
                continue
            for spec in CONCEPTS:
                source_label = next((c for c in spec.candidates if c in statement.index), None)
                if source_label is None:
                    continue
                series = statement.loc[source_label]
                for period_end, value in series.items():
                    if pd.isna(value):
                        continue
                    period_end = pd.Timestamp(period_end).date()
                    # Yahoo statements do not consistently expose the exact public filing timestamp.
                    # A conservative +120d proxy is used only for the prototype and explicitly marked.
                    proxy = datetime.combine(period_end, datetime.min.time(), tzinfo=timezone.utc) + timedelta(days=120)
                    frames.append(pd.DataFrame([{
                        "concept_code": spec.code,
                        "value": float(value),
                        "unit": "PLN",
                        "period_start": None,
                        "period_end": period_end,
                        "publication_date": proxy,
                        "available_at": proxy,
                        "source_label": f"Yahoo Finance/{statement_name}/{source_label}; availability_proxy_120d",
                    }]))
        if not frames:
            return pd.DataFrame()
        return pd.concat(frames, ignore_index=True).drop_duplicates(
            subset=["concept_code", "period_end"], keep="first"
        )
