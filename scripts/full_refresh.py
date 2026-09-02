from __future__ import annotations
import argparse
import json

from financial_platform.services.internet_ingestion import run_full_ingestion
from financial_platform.services.train_from_db import train_models_from_db


def main():
    parser = argparse.ArgumentParser(description="Internet -> PostgreSQL -> features -> models -> dashboard data")
    parser.add_argument("--start-year", type=int, default=2018)
    parser.add_argument("--tickers", nargs="*", default=None)
    parser.add_argument("--target", choices=["net_income", "revenue", "net_interest_income"], default="net_income")
    parser.add_argument("--min-common-eval-rows", type=int, default=20)
    args = parser.parse_args()
    print("=== 1/2 POBIERANIE I ZAPIS DANYCH ===")
    print(json.dumps(run_full_ingestion(args.start_year, args.tickers), ensure_ascii=False, indent=2, default=str))
    print("=== 2/2 BUDOWA DATASETU I TRENING ===")
    print(json.dumps(train_models_from_db(target=args.target, min_common_eval_rows=args.min_common_eval_rows), ensure_ascii=False, indent=2, default=str))

if __name__ == "__main__":
    main()
