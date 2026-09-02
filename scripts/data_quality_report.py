from __future__ import annotations

import json

from financial_platform.services.data_quality import get_data_quality_report


if __name__ == "__main__":
    print(json.dumps(get_data_quality_report(), ensure_ascii=False, indent=2, default=str))
