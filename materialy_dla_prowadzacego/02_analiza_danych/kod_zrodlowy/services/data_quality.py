from __future__ import annotations

import math

import pandas as pd
from sqlalchemy import text

from financial_platform.db.session import get_engine
from financial_platform.services.model_dataset import build_dataset_from_db
from financial_platform.modeling.feature_selection import CATEGORICAL_CANDIDATES, NUMERIC_CANDIDATES
from financial_platform.modeling.common_evaluation import TARGET_SPECS, common_eval_mask
from financial_platform.modeling.feature_registry import scoped_feature_coverage


def _quality_status(coverage: float) -> str:
    if coverage >= 0.80:
        return "good"
    if coverage >= 0.50:
        return "warning"
    return "poor"


def feature_coverage(frame: pd.DataFrame, columns: list[str]) -> list[dict]:
    rows = scoped_feature_coverage(frame, columns)
    for row in rows:
        row["status"] = _quality_status(float(row["coverage"]))
    return sorted(rows, key=lambda x: (x["scope"], x["coverage"], x["feature"]))


def _safe_date(value):
    if value is None or pd.isna(value):
        return None
    return pd.Timestamp(value).date().isoformat()


def _target_profile(panel: pd.DataFrame, key: str) -> dict:
    spec = TARGET_SPECS[key]
    frame = panel
    if spec.applicability == "financial":
        frame = panel[panel["is_financial"].astype(bool)]
    elif spec.applicability == "non_financial":
        frame = panel[~panel["is_financial"].astype(bool)]

    rows = int(len(frame))
    known = int(frame[spec.target_column].notna().sum()) if spec.target_column in frame else 0
    mask = common_eval_mask(frame, key)
    common = int(mask.sum())
    return {
        "key": key,
        "label": spec.label_pl,
        "target_code": spec.target_code,
        "rows": rows,
        "companies": int(frame["ticker"].nunique()) if rows else 0,
        "known_targets": known,
        "target_coverage": round(known / rows, 4) if rows else 0.0,
        "common_eval_rows": common,
        "common_eval_companies": int(frame.loc[mask, "ticker"].nunique()) if common else 0,
        "common_eval_periods": int(frame.loc[mask, "target_period_end"].nunique()) if common else 0,
        "applicability": spec.applicability,
        "status": "good" if common >= 40 else ("warning" if common >= 20 else "poor"),
    }


def get_data_quality_report() -> dict:
    panel = build_dataset_from_db()
    if panel.empty:
        return {
            "dataset": {
                "rows": 0, "companies": 0, "periods": 0, "known_targets": 0,
                "target_coverage": 0.0, "common_eval_rows": 0,
                "lag4_ready_companies": 0, "training_ready": False,
            },
            "targets": [], "target_provenance": {}, "features": [], "feature_scope_summary": [], "companies": [],
            "sources": [], "concepts": [], "mapping_audit": {},
            "recommendations": ["Uruchom pobieranie danych internetowych przed treningiem."],
        }

    total = len(panel)
    target_profiles = [_target_profile(panel, key) for key in TARGET_SPECS]
    net_profile = next(x for x in target_profiles if x["key"] == "net_income")
    known_targets = net_profile["known_targets"]
    common_eval_rows = net_profile["common_eval_rows"]
    common_eval_companies = net_profile["common_eval_companies"]
    common_eval_periods = net_profile["common_eval_periods"]

    company_quarters = panel.groupby("ticker")["period_end"].nunique().sort_values(ascending=False)
    lag4_ready = int((company_quarters >= 5).sum())
    periods = int(panel["period_end"].nunique())

    candidate_columns = [c for c in NUMERIC_CANDIDATES + CATEGORICAL_CANDIDATES if c in panel.columns]
    features = feature_coverage(panel, candidate_columns)
    poor_features = [f["feature"] for f in features if f["coverage"] < 0.5]
    feature_scope_summary = []
    for scope in ("all", "financial", "non_financial"):
        scoped = [f for f in features if f["scope"] == scope]
        if not scoped:
            continue
        feature_scope_summary.append({
            "scope": scope,
            "features": len(scoped),
            "eligible_rows": max((f["eligible_rows"] for f in scoped), default=0),
            "eligible_companies": max((f["eligible_companies"] for f in scoped), default=0),
            "avg_coverage": round(sum(f["coverage"] for f in scoped) / len(scoped), 4),
            "good_features": sum(1 for f in scoped if f["coverage"] >= 0.8),
            "warning_features": sum(1 for f in scoped if 0.5 <= f["coverage"] < 0.8),
            "poor_features": sum(1 for f in scoped if f["coverage"] < 0.5),
        })

    target_source = panel["target_source_concept"].value_counts(dropna=True).to_dict() if "target_source_concept" in panel else {}
    target_provenance = {
        "parent_targets": int(target_source.get("NET_INCOME_PARENT", 0)),
        "generic_fallback_targets": int(target_source.get("NET_INCOME", 0)),
        "unknown_targets": int(total - known_targets),
    }
    if known_targets:
        target_provenance["parent_share"] = round(target_provenance["parent_targets"] / known_targets, 4)
        target_provenance["fallback_share"] = round(target_provenance["generic_fallback_targets"] / known_targets, 4)
    else:
        target_provenance["parent_share"] = 0.0
        target_provenance["fallback_share"] = 0.0

    company_rows = []
    for ticker, group in panel.groupby("ticker"):
        group = group.sort_values("period_end")
        mask = common_eval_mask(group, "net_income")
        company_rows.append({
            "ticker": ticker,
            "rows": int(len(group)),
            "periods": int(group["period_end"].nunique()),
            "from": _safe_date(group["period_end"].min()),
            "to": _safe_date(group["period_end"].max()),
            "known_targets": int(group["target_net_income"].notna().sum()),
            "revenue_targets": int(group.get("target_revenue", pd.Series(dtype=float)).notna().sum()),
            "interest_targets": int(group.get("target_net_interest_income", pd.Series(dtype=float)).notna().sum()),
            "common_eval_rows": int(mask.sum()),
            "lag4_observed": int(group.get("net_income_lag4", pd.Series(dtype=float)).notna().sum()),
            "lag4_ready": bool(group["period_end"].nunique() >= 5),
            "is_financial": bool(group["is_financial"].iloc[0]) if "is_financial" in group else False,
        })
    company_rows.sort(key=lambda x: (-x["periods"], x["ticker"]))

    with get_engine().connect() as conn:
        source_rows = conn.execute(text("""
            SELECT
                CASE
                    WHEN ff.source_label LIKE 'Bankier/%' THEN 'Bankier/Notoria'
                    WHEN ff.source_label LIKE 'Yahoo Finance/%' THEN 'Yahoo Finance'
                    ELSE 'Other'
                END AS source,
                count(*) AS rows, count(DISTINCT ff.company_id) AS companies,
                min(ff.period_end) AS first_period, max(ff.period_end) AS last_period,
                sum(CASE WHEN ff.source_label LIKE '%publication_date_from_table%' THEN 1 ELSE 0 END) AS exact_date_rows,
                sum(CASE WHEN ff.source_label LIKE '%availability_proxy_120d%' THEN 1 ELSE 0 END) AS proxy_date_rows
            FROM core.financial_fact ff
            WHERE ff.is_current=TRUE
            GROUP BY 1 ORDER BY rows DESC
        """)).mappings().all()
        sources = [dict(r) for r in source_rows]

        concept_rows = conn.execute(text("""
            SELECT fc.code, count(*) AS rows, count(DISTINCT ff.company_id) AS companies,
                   min(ff.period_end) AS first_period, max(ff.period_end) AS last_period
            FROM core.financial_fact ff
            JOIN core.financial_concept fc ON fc.id=ff.financial_concept_id
            WHERE ff.is_current=TRUE
            GROUP BY fc.code ORDER BY rows DESC, fc.code
        """)).mappings().all()
        concepts = [dict(r) for r in concept_rows]

        audit_exists = conn.execute(text("SELECT to_regclass('staging.financial_mapping_audit')")).scalar()
        mapping_audit = {
            "latest_run_id": None, "labels_total": 0, "mapped_labels": 0, "unmatched_labels": 0,
            "mapped_with_values": 0, "unmatched_with_values": 0, "mapping_rate_with_values": 0.0,
            "top_unmatched": [], "by_concept": [],
        }
        if audit_exists:
            latest_run = conn.execute(text("""
                SELECT id FROM metadata.ingestion_run
                WHERE source_name='Bankier fundamentals v5.3'
                ORDER BY started_at DESC LIMIT 1
            """)).scalar()
            if latest_run:
                stats = conn.execute(text("""
                    SELECT count(*) AS labels_total,
                           count(*) FILTER (WHERE mapped_concept_code IS NOT NULL) AS mapped_labels,
                           count(*) FILTER (WHERE mapped_concept_code IS NULL) AS unmatched_labels,
                           count(*) FILTER (WHERE mapped_concept_code IS NOT NULL AND values_observed > 0) AS mapped_with_values,
                           count(*) FILTER (WHERE mapped_concept_code IS NULL AND values_observed > 0) AS unmatched_with_values
                    FROM staging.financial_mapping_audit WHERE ingestion_run_id=:run_id
                """), {"run_id": latest_run}).mappings().one()
                unmatched = conn.execute(text("""
                    SELECT c.ticker, a.statement_name, a.source_label, a.values_observed,
                           a.first_period, a.last_period, a.reason
                    FROM staging.financial_mapping_audit a
                    JOIN core.company c ON c.id=a.company_id
                    WHERE a.ingestion_run_id=:run_id AND a.mapped_concept_code IS NULL
                      AND a.values_observed > 0 AND a.match_method NOT IN ('excluded','ignored')
                    ORDER BY a.values_observed DESC, c.ticker, a.source_label
                    LIMIT 30
                """), {"run_id": latest_run}).mappings().all()
                by_concept = conn.execute(text("""
                    SELECT mapped_concept_code AS concept, count(*) AS labels,
                           sum(values_observed) AS observations,
                           round(avg(confidence)::numeric, 4) AS avg_confidence
                    FROM staging.financial_mapping_audit
                    WHERE ingestion_run_id=:run_id AND mapped_concept_code IS NOT NULL
                    GROUP BY mapped_concept_code ORDER BY observations DESC
                """), {"run_id": latest_run}).mappings().all()
                denom = int(stats["mapped_with_values"] or 0) + int(stats["unmatched_with_values"] or 0)
                mapping_audit = {
                    "latest_run_id": int(latest_run),
                    **{k: int(stats[k] or 0) for k in stats.keys()},
                    "mapping_rate_with_values": round(int(stats["mapped_with_values"] or 0) / denom, 4) if denom else 0.0,
                    "top_unmatched": [dict(r) for r in unmatched],
                    "by_concept": [dict(r) for r in by_concept],
                }

    # W v5.3 status „gotowy” jest celowo bardziej rygorystyczny niż wcześniej.
    training_ready = bool(
        net_profile["target_coverage"] >= 0.50
        and common_eval_rows >= 40
        and common_eval_periods >= 8
        and common_eval_companies >= 4
    )

    recommendations: list[str] = []
    if net_profile["target_coverage"] < 0.50:
        recommendations.append(
            f"Pokrycie targetu zysku netto wynosi {net_profile['target_coverage']:.1%}; "
            "sprawdź sekcję audytu mapowania i nierozpoznane etykiety z wartościami."
        )
    if common_eval_rows < 40:
        recommendations.append(
            f"Wspólna próbka OOF zysku netto ma {common_eval_rows} obserwacji. "
            "Do interpretacji rankingu v5.3 wymaga co najmniej 40."
        )
    revenue_profile = next(x for x in target_profiles if x["key"] == "revenue")
    if revenue_profile["common_eval_rows"] >= 20:
        recommendations.append(
            f"Target REVENUE ma {revenue_profile['common_eval_rows']} wspólnych obserwacji OOF i może służyć jako target kontrolny."
        )
    if mapping_audit.get("unmatched_with_values", 0):
        recommendations.append(
            f"Audyt wykrył {mapping_audit['unmatched_with_values']} nierozpoznanych etykiet zawierających dane. "
            "Przejrzyj je przed finalnym eksperymentem."
        )
    if lag4_ready < max(1, int(math.ceil(panel["ticker"].nunique() * 0.8))):
        recommendations.append("Co najmniej 80% spółek powinno mieć minimum 5 kwartałów historii.")
    if poor_features:
        recommendations.append(
            "Cechy o pokryciu poniżej 50% w swojej właściwej populacji są pomijane w foldach bez danych: "
            + ", ".join(poor_features[:8]) + ("..." if len(poor_features) > 8 else "")
        )
    if any(int(s.get("proxy_date_rows") or 0) > 0 for s in sources):
        recommendations.append(
            "Wiersze z proxy +120 dni są prototypowe; finalne available_at zweryfikuj w raportach emitenta/ESPI/ESEF."
        )
    if not recommendations:
        recommendations.append("Dataset spełnia rygorystyczne kryteria v5.5 dla porównania modeli.")

    return {
        "dataset": {
            "rows": total,
            "companies": int(panel["ticker"].nunique()),
            "periods": periods,
            "known_targets": known_targets,
            "target_coverage": net_profile["target_coverage"],
            "common_eval_rows": common_eval_rows,
            "common_eval_companies": common_eval_companies,
            "common_eval_periods": common_eval_periods,
            "lag4_ready_companies": lag4_ready,
            "lag4_ready_share": round(lag4_ready / panel["ticker"].nunique(), 4) if panel["ticker"].nunique() else 0.0,
            "training_ready": training_ready,
            "readiness_rule": "target_coverage>=50%, common_OOF>=40, periods>=8, companies>=4",
        },
        "targets": target_profiles,
        "target_provenance": target_provenance,
        "features": features,
        "feature_scope_summary": feature_scope_summary,
        "companies": company_rows,
        "sources": sources,
        "concepts": concepts,
        "mapping_audit": mapping_audit,
        "recommendations": recommendations,
    }
