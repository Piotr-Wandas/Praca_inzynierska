from datetime import timezone

import pandas as pd

from financial_platform.ingestion.bankier_financials import BankierFinancialClient


def test_bankier_parser_extracts_long_quarterly_history(monkeypatch):
    income = pd.DataFrame({
        "Nazwa (dane w tys. zł)": [
            "Data publikacji/aktualizacji raportu", "Przychody ze sprzedaży",
            "Zysk z działalności operacyjnej", "Zysk netto akcjonariuszy jednostki dominującej",
        ],
        "Mar 2019": ["15 Maj 2019", "100", "20", "12"],
        "Cze 2019": ["13 Sie 2019", "110", "22", "13"],
        "Wrz 2019": ["07 Lis 2019", "120", "24", "14"],
        "Gru 2019": ["12 Lut 2020", "130", "26", "15"],
        "Mar 2020": ["28 Maj 2020", "140", "28", "16"],
    })
    balance = pd.DataFrame({
        "Nazwa (dane w tys. zł)": ["Data publikacji/aktualizacji raportu", "Aktywa razem", "Kapitał własny"],
        "Mar 2019": ["15 Maj 2019", "1000", "500"],
        "Cze 2019": ["13 Sie 2019", "1100", "510"],
        "Wrz 2019": ["07 Lis 2019", "1200", "520"],
        "Gru 2019": ["12 Lut 2020", "1300", "530"],
        "Mar 2020": ["28 Maj 2020", "1400", "540"],
    })
    cashflow = pd.DataFrame({
        "Nazwa (dane w tys. zł)": ["Data publikacji/aktualizacji raportu", "Przepływy pieniężne netto z działalności operacyjnej"],
        "Mar 2019": ["15 Maj 2019", "30"],
        "Cze 2019": ["13 Sie 2019", "31"],
        "Wrz 2019": ["07 Lis 2019", "32"],
        "Gru 2019": ["12 Lut 2020", "33"],
        "Mar 2020": ["28 Maj 2020", "34"],
    })

    client = BankierFinancialClient()
    def fake_tables(url):
        if "bilans" in url:
            return [balance]
        if "przeplywy-pieniezne" in url:
            return [cashflow]
        return [income]
    monkeypatch.setattr(client, "_tables", fake_tables)

    result = client.quarterly_facts("TEST", start_year=2019)
    assert result["period_end"].nunique() == 5
    assert {"REVENUE", "NET_INCOME_PARENT", "OPERATING_PROFIT", "TOTAL_ASSETS", "EQUITY", "OPERATING_CASH_FLOW"}.issubset(set(result["concept_code"]))
    revenue = result[(result["concept_code"] == "REVENUE") & (result["period_end"] == pd.Timestamp("2019-03-31").date())].iloc[0]
    assert revenue["value"] == 100_000.0
    assert revenue["publication_date"].tzinfo == timezone.utc
    assert "publication_date_from_table" in revenue["source_label"]


def test_bankier_parser_maps_generic_net_income_to_fallback(monkeypatch):
    income = pd.DataFrame({
        "Nazwa (dane w tys. zł)": ["Przychody ze sprzedaży", "Zysk netto"],
        "Mar 2022": ["100", "12"],
        "Cze 2022": ["110", "13"],
    })
    client = BankierFinancialClient()
    monkeypatch.setattr(client, "_tables", lambda url: [income])
    result = client.quarterly_facts("TEST", start_year=2022)
    assert "NET_INCOME" in set(result["concept_code"])
    generic = result[result["concept_code"] == "NET_INCOME"]
    assert len(generic) == 2


def test_v53_maps_actual_bankier_notoria_labels():
    from financial_platform.ingestion.bankier_financials import classify_source_label

    assert classify_source_label(
        "Zysk/strata netto udziałowców jednostki dominującej", "rachunek-zyskow-i-strat"
    ).concept_code == "NET_INCOME_PARENT"
    assert classify_source_label(
        "Zysk/strata netto", "rachunek-zyskow-i-strat"
    ).concept_code == "NET_INCOME"
    assert classify_source_label(
        "Przychody z podstawowej działalności operacyjnej", "rachunek-zyskow-i-strat"
    ).concept_code == "REVENUE"
    assert classify_source_label(
        "Zysk/strata udziałowców niekontrolujących", "rachunek-zyskow-i-strat"
    ).concept_code is None


def test_v53_parser_returns_audit_for_unmatched_rows(monkeypatch):
    income = pd.DataFrame({
        "Nazwa (dane w tys. zł)": [
            "Data publikacji/aktualizacji raportu",
            "Przychody z podstawowej działalności operacyjnej",
            "Zysk/strata netto udziałowców jednostki dominującej",
            "Pozycja specyficzna dla emitenta",
        ],
        "Mar 2024": ["15 Maj 2024", "100", "12", "5"],
        "Cze 2024": ["20 Sie 2024", "110", "13", "6"],
    })
    client = BankierFinancialClient()
    monkeypatch.setattr(client, "_tables", lambda url: [income])
    facts, audit = client.quarterly_facts_with_audit("TEST", start_year=2024)
    assert "NET_INCOME_PARENT" in set(facts["concept_code"])
    unmatched = audit[audit["source_label"] == "Pozycja specyficzna dla emitenta"].iloc[0]
    assert unmatched["mapped_concept"] is None
    assert unmatched["values_observed"] == 2
