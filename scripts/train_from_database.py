from __future__ import annotations

import argparse
import json

from financial_platform.services.train_from_db import train_models_from_db


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--target",
        choices=["net_income", "revenue", "net_interest_income"],
        default="net_income",
    )
    parser.add_argument("--min-common-eval-rows", type=int, default=20)
    args = parser.parse_args()
    print(json.dumps(
        train_models_from_db(target=args.target, min_common_eval_rows=args.min_common_eval_rows),
        indent=2, ensure_ascii=False, default=str,
    ))
