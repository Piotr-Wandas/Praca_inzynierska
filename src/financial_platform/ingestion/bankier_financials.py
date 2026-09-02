from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from io import StringIO
import re
import unicodedata

import httpx
import numpy as np
import pandas as pd


_MONTHS = {"mar": 3, "cze": 6, "wrz": 9, "gru": 12}
_MONTHS_DATE = {
    "sty": 1, "lut": 2, "mar": 3, "kwi": 4, "maj": 5, "cze": 6,
    "lip": 7, "sie": 8, "wrz": 9, "paz": 10, "paź": 10, "lis": 11, "gru": 12,
}


def _plain(value: object) -> str:
    text = str(value).replace("\xa0", " ").strip().lower()
    text = text.translate(str.maketrans({"ł": "l", "Ł": "l"}))
    text = unicodedata.normalize("NFKD", text)
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def _period_end(label: object) -> pd.Timestamp | None:
    # Pandas może zwrócić kolumnę jako tuple/MultiIndex. Łączymy wszystkie części.
    if isinstance(label, tuple):
        label = " ".join(str(x) for x in label if str(x) != "nan")
    text = _plain(label)
    match = re.search(r"\b(mar|cze|wrz|gru)\s+(\d{4})\b", text)
    if not match:
        return None
    month = _MONTHS[match.group(1)]
    year = int(match.group(2))
    return pd.Timestamp(year=year, month=month, day=1) + pd.offsets.MonthEnd(0)


def _publication_date(value: object) -> datetime | None:
    if value is None or (isinstance(value, float) and np.isnan(value)):
        return None
    # W komórkach mogą pojawić się dodatkowe adnotacje/linki. Szukamy daty wewnątrz tekstu.
    text = _plain(value)
    match = re.search(r"(\d{1,2})\s+([a-z]+)\s+(\d{4})", text)
    if match:
        day = int(match.group(1))
        month = _MONTHS_DATE.get(match.group(2)[:3])
        if month:
            return datetime(int(match.group(3)), month, day, tzinfo=timezone.utc)
    ts = pd.to_datetime(value, dayfirst=True, errors="coerce")
    if pd.isna(ts):
        return None
    return datetime(ts.year, ts.month, ts.day, tzinfo=timezone.utc)


def _number(value: object) -> float | None:
    if value is None or (isinstance(value, float) and np.isnan(value)):
        return None
    text = str(value).replace("\xa0", " ").strip()
    if text in {"", "-", "—", "--", "-- --", "nan", "None"}:
        return None
    negative = text.startswith("(") and text.endswith(")")
    text = text.strip("()")
    text = re.sub(r"[^0-9,\.\- ]", "", text).replace(" ", "")
    if not text or text in {"-", "--"}:
        return None
    if "," in text and "." in text:
        text = text.replace(".", "").replace(",", ".")
    elif "," in text:
        text = text.replace(",", ".")
    try:
        result = float(text)
        return -result if negative else result
    except ValueError:
        return None


@dataclass(frozen=True)
class MappingDecision:
    concept_code: str | None
    confidence: float
    method: str
    reason: str


# v5.3 DATA FIX
# Reguły są oparte na faktycznych etykietach występujących w tabelach Bankier/Notoria,
# m.in. „Zysk/strata netto udziałowców jednostki dominującej” oraz
# „Przychody z podstawowej działalności operacyjnej”. Kolejność ma znaczenie.
def classify_source_label(label: object, statement: str) -> MappingDecision:
    raw = _plain(label)
    if not raw or raw.startswith("data publikacji"):
        return MappingDecision(None, 0.0, "ignored", "metadata_or_empty")

    # Wykluczenia zabezpieczają przed przypisaniem wyniku działalności zaniechanej
    # lub udziałowców niekontrolujących do zysku netto grupy.
    if "niekontrol" in raw:
        return MappingDecision(None, 0.0, "excluded", "non_controlling_interest")
    if "dzialalnosci zaniechanej" in raw:
        return MappingDecision(None, 0.0, "excluded", "discontinued_operations")

    if statement == "rachunek-zyskow-i-strat":
        if (
            ("zysk/strata netto" in raw or "zysk strata netto" in raw or "zysk netto" in raw)
            and "jednostki dominujacej" in raw
            and ("udzialowc" in raw or "akcjonarius" in raw or "przypis" in raw)
        ):
            return MappingDecision("NET_INCOME_PARENT", 0.99, "semantic_rule", "parent_net_income")

        if raw in {"zysk/strata netto", "zysk strata netto", "zysk netto", "wynik netto", "strata netto"}:
            return MappingDecision("NET_INCOME", 0.99, "exact_normalized", "generic_net_income")
        if raw.startswith("zysk/strata netto") and "jednostki dominujacej" not in raw:
            return MappingDecision("NET_INCOME", 0.96, "semantic_rule", "generic_net_income_prefix")

        # Dla spółek handlowych/produkcyjnych Bankier często nazywa top-line właśnie tak.
        revenue_exact = {
            "przychody z podstawowej dzialalnosci operacyjnej",
            "przychody netto ze sprzedazy produktow towarow i materialow",
            "przychody netto ze sprzedazy",
            "przychody ze sprzedazy netto",
            "przychody ze sprzedazy",
            "przychody razem",
            "przychody",
        }
        if raw in revenue_exact:
            return MappingDecision("REVENUE", 0.98, "exact_normalized", "revenue_total")
        # Nie sumujemy komponentów „sprzedaż produktów” + „towarów i materiałów”; mapujemy tylko total.
        if raw.startswith("przychody z podstawowej dzialalnosci operacyjnej"):
            return MappingDecision("REVENUE", 0.96, "semantic_rule", "revenue_operating_total")

        operating_exact = {
            "zysk/strata z dzialalnosci operacyjnej",
            "zysk strata z dzialalnosci operacyjnej",
            "zysk z dzialalnosci operacyjnej",
            "wynik z dzialalnosci operacyjnej",
            "wynik operacyjny",
            "zysk operacyjny",
        }
        if raw in operating_exact:
            return MappingDecision("OPERATING_PROFIT", 0.98, "exact_normalized", "operating_profit")
        if raw == "ebitda" or raw.startswith("ebitda "):
            return MappingDecision("EBITDA", 0.99, "exact_normalized", "ebitda")

        interest_exact = {
            "wynik z tytulu odsetek", "wynik odsetkowy", "dochody odsetkowe netto", "wynik z odsetek",
        }
        if raw in interest_exact:
            return MappingDecision("NET_INTEREST_INCOME", 0.98, "exact_normalized", "net_interest_income")
        if "wynik" in raw and "odset" in raw:
            return MappingDecision("NET_INTEREST_INCOME", 0.93, "semantic_rule", "net_interest_income")

        fee_exact = {
            "wynik z tytulu oplat i prowizji", "wynik z tytulu prowizji", "wynik prowizyjny",
            "dochody z oplat i prowizji netto", "wynik z tytulu prowizji i oplat",
        }
        if raw in fee_exact:
            return MappingDecision("NET_FEE_INCOME", 0.98, "exact_normalized", "net_fee_income")
        if "wynik" in raw and ("prowiz" in raw or ("oplat" in raw and "prowiz" in raw)):
            return MappingDecision("NET_FEE_INCOME", 0.92, "semantic_rule", "net_fee_income")

    if statement == "bilans":
        if raw in {"aktywa razem", "suma aktywow", "aktywa ogolem"}:
            return MappingDecision("TOTAL_ASSETS", 0.99, "exact_normalized", "total_assets")
        if raw in {
            "kapital wlasny akcjonariuszy jednostki dominujacej",
            "kapital wlasny przypisany akcjonariuszom jednostki dominujacej",
            "kapitaly wlasne", "kapital wlasny",
        }:
            return MappingDecision("EQUITY", 0.98, "exact_normalized", "equity")
        if "kapital" in raw and "wlasn" in raw and "niekontrol" not in raw:
            return MappingDecision("EQUITY", 0.90, "semantic_rule", "equity")

    if statement == "przeplywy-pieniezne":
        if raw in {
            "przeplywy pieniezne netto z dzialalnosci operacyjnej",
            "przeplywy pieniezne z dzialalnosci operacyjnej",
            "przeplywy netto z dzialalnosci operacyjnej",
            "cash flow operacyjny",
        }:
            return MappingDecision("OPERATING_CASH_FLOW", 0.98, "exact_normalized", "operating_cash_flow")
        if "przeplyw" in raw and "dzialalnosci operacyjnej" in raw and "netto" in raw:
            return MappingDecision("OPERATING_CASH_FLOW", 0.91, "semantic_rule", "operating_cash_flow")

    return MappingDecision(None, 0.0, "unmatched", "no_safe_mapping")


class BankierFinancialClient:
    """Parser kwartalnych tabel Bankier/Notoria z audytem mapowania etykiet.

    v5.3 zapisuje także nierozpoznane etykiety, aby mapowanie nie było „czarną skrzynką”.
    Parser próbuje wariantu skonsolidowanego, strony domyślnej oraz jednostkowego.
    """

    base_url = "https://www.bankier.pl/gielda/notowania/akcje"
    statements = ("rachunek-zyskow-i-strat", "bilans", "przeplywy-pieniezne")

    def __init__(self, timeout: float = 30.0):
        self.timeout = timeout
        self.headers = {
            "User-Agent": "Mozilla/5.0 (compatible; FinancialPredictionThesis/1.0; research prototype)",
            "Accept-Language": "pl-PL,pl;q=0.9,en;q=0.7",
        }

    def _candidate_urls(self, slug: str, statement: str) -> list[str]:
        root = f"{self.base_url}/{slug}/wyniki-finansowe/{statement}"
        return [
            f"{root}/skonsolidowany/kwartalny",
            root,
            f"{root}/jednostkowy/kwartalny",
        ]

    def _tables(self, url: str) -> list[pd.DataFrame]:
        response = httpx.get(url, headers=self.headers, timeout=self.timeout, follow_redirects=True)
        response.raise_for_status()
        return pd.read_html(StringIO(response.text), decimal=",", thousands=" ")

    @staticmethod
    def _find_financial_table(tables: list[pd.DataFrame]) -> pd.DataFrame | None:
        best: pd.DataFrame | None = None
        score = -1
        for table in tables:
            if table.shape[1] < 3 or table.empty:
                continue
            periods = sum(_period_end(col) is not None for col in table.columns)
            first_col = table.iloc[:, 0].astype(str).map(_plain)
            has_publication = first_col.str.contains("data publikacji", regex=False).any()
            current = periods * 2 + int(has_publication) * 5 + min(len(table), 50) / 100
            if current > score and periods >= 2:
                best, score = table.copy(), current
        return best

    def _load_best_table(self, slug: str, statement: str) -> tuple[pd.DataFrame | None, str | None]:
        best = None
        best_url = None
        best_score = -1
        for url in self._candidate_urls(slug, statement):
            try:
                tables = self._tables(url)
            except Exception:
                continue
            table = self._find_financial_table(tables)
            if table is None:
                continue
            periods = sum(_period_end(col) is not None for col in table.columns)
            if periods > best_score:
                best, best_url, best_score = table, url, periods
        return best, best_url

    @staticmethod
    def _first_column_text(table: pd.DataFrame) -> pd.Series:
        return table.iloc[:, 0].astype(str)

    @staticmethod
    def _publication_row(table: pd.DataFrame) -> pd.Series | None:
        first = BankierFinancialClient._first_column_text(table).map(_plain)
        mask = first.str.contains("data publikacji", regex=False, na=False)
        if not mask.any():
            return None
        return table.loc[mask].iloc[0]

    @staticmethod
    def _unit_multiplier(table: pd.DataFrame) -> float:
        first_header = " ".join(str(x) for x in table.columns)
        first_label = str(table.columns[0])
        unit_text = _plain(first_header + " " + first_label)
        if "mln" in unit_text:
            return 1_000_000.0
        if "tys" in unit_text:
            return 1_000.0
        return 1.0

    def quarterly_facts_with_audit(self, slug: str, start_year: int = 2018) -> tuple[pd.DataFrame, pd.DataFrame]:
        facts: list[dict] = []
        audit: list[dict] = []

        for statement in self.statements:
            table, url = self._load_best_table(slug, statement)
            if table is None or url is None:
                audit.append({
                    "statement": statement, "source_label": "<TABLE_NOT_FOUND>", "normalized_label": "",
                    "mapped_concept": None, "confidence": 0.0, "match_method": "table_missing",
                    "reason": "no_accessible_quarterly_table", "values_observed": 0,
                    "first_period": None, "last_period": None, "source_url": url,
                })
                continue

            multiplier = self._unit_multiplier(table)
            publication_values = self._publication_row(table)
            period_columns: list[tuple[object, pd.Timestamp]] = []
            for col in table.columns[1:]:
                period = _period_end(col)
                if period is not None and period.year >= start_year:
                    period_columns.append((col, period))

            # Audytujemy wszystkie nazwy w tabeli, nie tylko rozpoznane koncepty.
            for _, series in table.iterrows():
                source_row = str(series.iloc[0])
                decision = classify_source_label(source_row, statement)
                values = []
                periods_with_values = []
                for col, period in period_columns:
                    value = _number(series[col])
                    if value is not None:
                        values.append(value)
                        periods_with_values.append(period)
                audit.append({
                    "statement": statement,
                    "source_label": source_row,
                    "normalized_label": _plain(source_row),
                    "mapped_concept": decision.concept_code,
                    "confidence": decision.confidence,
                    "match_method": decision.method,
                    "reason": decision.reason,
                    "values_observed": len(values),
                    "first_period": periods_with_values[0].date() if periods_with_values else None,
                    "last_period": periods_with_values[-1].date() if periods_with_values else None,
                    "source_url": url,
                })
                if decision.concept_code is None:
                    continue

                for col, period in period_columns:
                    value = _number(series[col])
                    if value is None:
                        continue
                    publication = None
                    if publication_values is not None:
                        try:
                            publication = _publication_date(publication_values[col])
                        except Exception:
                            publication = None
                    if publication is None:
                        publication = datetime(period.year, period.month, period.day, tzinfo=timezone.utc) + timedelta(days=120)
                        availability_note = "availability_proxy_120d"
                    else:
                        availability_note = "publication_date_from_table"
                    facts.append({
                        "concept_code": decision.concept_code,
                        "value": float(value) * multiplier,
                        "unit": "PLN",
                        "period_start": None,
                        "period_end": period.date(),
                        "publication_date": publication,
                        "available_at": publication,
                        "source_label": (
                            f"Bankier/{statement}/{source_row}; mapping={decision.method}; "
                            f"confidence={decision.confidence:.2f}; {availability_note}; {url}"
                        ),
                        "source_concept": source_row,
                        "mapping_confidence": decision.confidence,
                        "mapping_method": decision.method,
                    })

        facts_df = pd.DataFrame(facts)
        audit_df = pd.DataFrame(audit)
        if facts_df.empty:
            return facts_df, audit_df

        # Jeżeli kilka wierszy zostało bezpiecznie zmapowanych do tego samego konceptu,
        # wybieramy mapowanie o najwyższej pewności; przy remisie zachowujemy ostatnie.
        facts_df = facts_df.sort_values(
            ["period_end", "concept_code", "mapping_confidence", "source_concept"],
            ascending=[True, True, True, True],
        ).drop_duplicates(subset=["concept_code", "period_end"], keep="last")
        return facts_df.reset_index(drop=True), audit_df.reset_index(drop=True)

    def quarterly_facts(self, slug: str, start_year: int = 2018) -> pd.DataFrame:
        facts, _ = self.quarterly_facts_with_audit(slug, start_year=start_year)
        return facts
