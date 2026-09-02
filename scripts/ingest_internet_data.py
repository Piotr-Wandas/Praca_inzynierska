from __future__ import annotations
import argparse
import json
from financial_platform.services.internet_ingestion import run_full_ingestion


def main():
    parser = argparse.ArgumentParser(description="Download real internet data and save it to PostgreSQL")
    parser.add_argument("--start-year", type=int, default=2018)
    parser.add_argument("--tickers", nargs="*", default=None, help="Pilot tickers, e.g. PKO PEO ORL CDR")
    args = parser.parse_args()
    print(json.dumps(run_full_ingestion(args.start_year, args.tickers), indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
