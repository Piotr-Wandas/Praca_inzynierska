from pathlib import Path
import re

path = Path("/app/pyproject.toml")
if not path.exists():
    raise SystemExit("Nie znaleziono /app/pyproject.toml")

text = path.read_text(encoding="utf-8")

# E501: Ruff formatter celowo nie łamie wszystkich długich stringów/SQL.
# B008: FastAPI używa Query()/Depends() w wartościach domyślnych parametrów.
needed = ["E501", "B008"]

section_match = re.search(r"(?ms)^\[tool\.ruff\.lint\]\s*\n(.*?)(?=^\[|\Z)", text)

if not section_match:
    addition = '\n[tool.ruff.lint]\nextend-ignore = ["E501", "B008"]\n'
    text = text.rstrip() + "\n" + addition
else:
    section = section_match.group(0)
    m = re.search(r'(?m)^extend-ignore\s*=\s*\[(.*?)\]\s*$', section)
    if m:
        values = re.findall(r'["\']([^"\']+)["\']', m.group(1))
        for code in needed:
            if code not in values:
                values.append(code)
        replacement = "extend-ignore = [" + ", ".join(f'"{x}"' for x in values) + "]"
        section = section[:m.start()] + replacement + section[m.end():]
    else:
        section = section.rstrip() + '\nextend-ignore = ["E501", "B008"]\n'
    text = text[:section_match.start()] + section + text[section_match.end():]

path.write_text(text, encoding="utf-8")
print("[OK] pyproject.toml: skonfigurowano E501/B008.")
