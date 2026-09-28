"""Kontrola zapisanych OOF; bez ponownego treningu i bez deserializacji joblib."""
import argparse
import hashlib
import json
from pathlib import Path
import sys

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'src'))
from financial_platform.evaluation.metrics import regression_metrics


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    records, checks = [], []
    for name in ['net_income', 'revenue', 'net_interest_income']:
        folder = ROOT / 'review/artifacts/real_data_analysis' / name
        source = folder / 'oof_predictions_common_sample.csv'
        frame = pd.read_csv(source)
        saved = pd.read_csv(folder / 'model_comparison.csv').set_index('model')
        key_cols = ['ticker', 'target_period_end', 'cutoff_at']
        groups = list(frame.groupby('model_name'))
        reference = set(map(tuple, groups[0][1][key_cols].to_numpy()))
        consistent = True
        for model, group in groups:
            if group.duplicated(key_cols).any():
                raise ValueError(f'{name}/{model}: powielone klucze')
            if set(map(tuple, group[key_cols].to_numpy())) != reference:
                raise ValueError(f'{name}/{model}: różne próbki porównawcze')
            metrics = regression_metrics(group.actual_value.to_numpy(), group.predicted_value.to_numpy())
            matches = all(np.isclose(value, saved.loc[model, key], rtol=1e-9, atol=1e-9,
                                     equal_nan=True) for key, value in metrics.items())
            consistent = consistent and matches
            records.append({'target': name, 'model': model, 'n_obs': len(group),
                            'metrics_match': bool(matches), **metrics})
        unique = frame.drop_duplicates(key_cols)
        late = pd.to_datetime(unique.cutoff_at, utc=True) > pd.to_datetime(unique.target_period_end, utc=True)
        checks.append({'target': name, 'n_obs_per_model': len(reference),
                       'companies': sorted(unique.ticker.unique().tolist()),
                       'folds': int(unique.fold.nunique()),
                       'target_from': unique.target_period_end.min(),
                       'target_to': unique.target_period_end.max(),
                       'cutoff_after_target_end': int(late.sum()),
                       'metrics_match': bool(consistent), 'same_keys': True,
                       'sha256': hashlib.sha256(source.read_bytes()).hexdigest()})
    args.output.mkdir(parents=True, exist_ok=False)
    pd.DataFrame(records).to_csv(args.output / 'metryki_przeliczone.csv', index=False)
    (args.output / 'weryfikacja.json').write_text(json.dumps(checks, indent=2, ensure_ascii=False), encoding='utf-8')
    print(json.dumps(checks, ensure_ascii=False))
    if not all(x['metrics_match'] for x in checks):
        raise SystemExit(1)


if __name__ == '__main__':
    main()
