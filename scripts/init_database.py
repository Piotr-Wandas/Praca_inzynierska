from pathlib import Path
import psycopg
from financial_platform.config.settings import get_settings

url = get_settings().database_url.replace("postgresql+psycopg://", "postgresql://")
sql = Path("sql/create_database.sql").read_text(encoding="utf-8")
with psycopg.connect(url) as conn:
    with conn.cursor() as cur:
        cur.execute(sql)
print("Database schema initialized/updated.")
