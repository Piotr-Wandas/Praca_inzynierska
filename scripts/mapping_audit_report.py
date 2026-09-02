from __future__ import annotations

import json

from financial_platform.services.data_quality import get_data_quality_report


if __name__ == "__main__":
    report = get_data_quality_report()
    print(json.dumps({
        "mapping_audit": report.get("mapping_audit", {}),
        "targets": report.get("targets", []),
        "recommendations": report.get("recommendations", []),
    }, ensure_ascii=False, indent=2, default=str))
