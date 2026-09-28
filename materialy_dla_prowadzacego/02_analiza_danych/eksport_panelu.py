"""Eksport obecnego panelu z istniejącej bazy; nie naprawia metodologii."""
import argparse
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'src'))
from financial_platform.services.model_dataset import build_dataset_from_db


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError(args.output)
    frame = build_dataset_from_db()
    if frame.empty:
        raise ValueError('Baza nie zawiera panelu')
    args.output.mkdir(parents=True)
    target = args.output / 'panel.csv'
    frame.to_csv(target, index=False)
    metadata = {'rows': len(frame), 'sha256': hashlib.sha256(target.read_bytes()).hexdigest(),
                'builder': 'src/financial_platform/services/model_dataset.py',
                'point_in_time_verified': False}
    (args.output / 'metadata.json').write_text(json.dumps(metadata, indent=2), encoding='utf-8')


if __name__ == '__main__':
    main()
