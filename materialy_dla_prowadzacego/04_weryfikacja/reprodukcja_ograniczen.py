"""Sztuczne kontrprzykłady do przeglądu; nie są wynikami badań finansowych."""
from pathlib import Path
import json
import sys
from unittest.mock import patch

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'src'))
from financial_platform.services import model_dataset as md
from financial_platform.services.train_from_db import _splits
from financial_platform.modeling.common_evaluation import get_target_spec
from financial_platform.datasets.point_in_time import asof_latest


def main():
    dates = pd.date_range('2018-03-31', periods=12, freq='QE')
    facts = pd.DataFrame({'company_id': 1, 'ticker': 'TEST', 'sector': 'Test',
                          'is_financial': False, 'period_end': dates,
                          'cutoff_at': dates.tz_localize('UTC') + pd.Timedelta(days=45),
                          'NET_INCOME_PARENT': range(100, 112)})
    def build(frame):
        with patch.object(md, '_financial_panel', return_value=frame.copy()), \
             patch.object(md, '_market_features', return_value=pd.DataFrame()), \
             patch.object(md, '_macro_series', return_value=pd.DataFrame()):
            return md.build_dataset_from_db()
    panel = build(facts)
    row = panel.iloc[5]
    output = {'baseline': {'target': float(row.target_net_income),
                           'kod_lag1': float(row.net_income_lag1),
                           'ostatni_wynik_t': float(row.NET_INCOME_CANONICAL),
                           'kod_lag4': float(row.net_income_lag4),
                           'sezonowy_dla_t_plus_1': float(panel.iloc[2].NET_INCOME_CANONICAL)}}
    gap = build(facts.drop(index=6))
    row = gap[gap.period_end == dates[5]].iloc[0]
    output['luka'] = {'period_end': str(row.period_end.date()),
                      'target_period_end': str(row.target_period_end.date())}
    two = pd.concat([panel, panel.assign(ticker='TEST2', company_id=2)], ignore_index=True)
    two['target_available_at'] = pd.Timestamp('2030-01-01', tz='UTC')
    first = next(_splits(two, get_target_spec('net_income')))
    train, valid = first[2], first[3]
    output['etykiety'] = {'pozniejsze_w_treningu': int((train.target_available_at > valid.cutoff_at.min()).sum())}
    obs = pd.DataFrame({'ticker': ['A', 'A', 'B', 'B'],
                        'available_at': ['2020-01-01', '2020-03-01', '2020-01-01', '2020-03-01'],
                        'value': [1, 2, 3, 4]})
    cut = pd.DataFrame({'ticker': ['A', 'A', 'B', 'B'],
                        'cutoff_at': ['2020-02-01', '2020-04-01', '2020-02-01', '2020-04-01']})
    try:
        asof_latest(obs, cut, 'ticker')
        output['asof_latest'] = 'Brak wyjątku w tej wersji pandas'
    except ValueError as exc:
        output['asof_latest'] = str(exc)
    print(json.dumps(output, indent=2, ensure_ascii=False))


if __name__ == '__main__':
    main()
