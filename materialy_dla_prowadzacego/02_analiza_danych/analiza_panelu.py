"""Statystyki opisowe panelu CSV. Nie wykonuje treningu."""
import argparse
import hashlib
import json
from pathlib import Path

import pandas as pd


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--data-kind', choices=['demo', 'real'], required=True)
    args = parser.parse_args()
    frame = pd.read_csv(args.input)
    required = {'ticker', 'period_end'}
    if not required.issubset(frame):
        raise ValueError(f'Brak kolumn: {required - set(frame)}')
    dates = pd.to_datetime(frame['period_end'], errors='raise')
    if dates.isna().any() or frame['ticker'].isna().any():
        raise ValueError('Brak klucza ticker lub period_end')
    args.output.mkdir(parents=True, exist_ok=False)
    pd.DataFrame({'kolumna': frame.columns, 'niepuste': frame.notna().sum().values,
                  'braki_proc': frame.isna().mean().values * 100}).to_csv(
                      args.output / 'kompletnosc.csv', index=False)
    numeric = frame.select_dtypes(include='number')
    if not numeric.empty:
        numeric.describe().T.to_csv(args.output / 'statystyki_liczbowe.csv')
    coverage = frame.assign(period_end=dates).groupby('ticker')['period_end'].agg(
        liczba='size', od='min', do='max')
    coverage.to_csv(args.output / 'pokrycie_spolek.csv')
    gaps = []
    for ticker, group in frame.assign(period_end=dates).groupby('ticker'):
        quarters = sorted(group.period_end.dt.to_period('Q').unique())
        for before, after in zip(quarters, quarters[1:]):
            missing = after.ordinal - before.ordinal - 1
            if missing:
                gaps.append({'ticker': ticker, 'od': str(before), 'do': str(after),
                             'brakujace_kwartaly': missing})
    pd.DataFrame(gaps, columns=['ticker', 'od', 'do', 'brakujace_kwartaly']).to_csv(
        args.output / 'luki_kwartalne.csv', index=False)
    metadata = {'data_kind': args.data_kind, 'rows': len(frame), 'companies': len(coverage),
                'duplicate_keys': int(frame.duplicated(['ticker', 'period_end']).sum()),
                'sha256': hashlib.sha256(args.input.read_bytes()).hexdigest(),
                'warning': 'Statystyki opisowe nie potwierdzają poprawności point-in-time ani prognoz.'}
    (args.output / 'podsumowanie.json').write_text(
        json.dumps(metadata, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps(metadata, ensure_ascii=False))


if __name__ == '__main__':
    main()
