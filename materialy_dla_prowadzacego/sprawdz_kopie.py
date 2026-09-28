"""Uruchom: python materialy_dla_prowadzacego/sprawdz_kopie.py."""
from pathlib import Path
import hashlib
import json

folder = Path(__file__).resolve().parent
manifest = json.loads((folder / "manifest_kopii.json").read_text(encoding="utf-8"))
bad = []
for entry in manifest:
    for path in [folder.parent / entry["source"], folder / entry["copy"]]:
        if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest() != entry["sha256"]:
            bad.append(str(path))
print(json.dumps({"pairs": len(manifest), "valid": not bad, "different_or_missing": bad}, ensure_ascii=False))
raise SystemExit(1 if bad else 0)
