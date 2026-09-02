"""initial schemas and core tables"""
from alembic import op
import sqlalchemy as sa
revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    for schema in ["metadata", "raw", "staging", "core", "analytics", "ml", "app"]:
        op.execute(sa.text(f"CREATE SCHEMA IF NOT EXISTS {schema}"))
    from financial_platform.db.models import Base
    bind = op.get_bind()
    Base.metadata.create_all(bind=bind)

def downgrade():
    from financial_platform.db.models import Base
    bind = op.get_bind()
    Base.metadata.drop_all(bind=bind)
    for schema in reversed(["metadata", "raw", "staging", "core", "analytics", "ml", "app"]):
        op.execute(sa.text(f"DROP SCHEMA IF EXISTS {schema} CASCADE"))
