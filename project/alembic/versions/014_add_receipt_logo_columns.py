"""Add logo_data and logo_content_type columns to receipt_config."""
from alembic import op
import sqlalchemy as sa

revision = '014'
down_revision = '013'
branch_labels = None
depends_on = None

def upgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    cols = {c["name"] for c in inspector.get_columns("receipt_config")}

    if "logo_data" not in cols:
        op.add_column('receipt_config', sa.Column('logo_data', sa.LargeBinary(), nullable=True))
    if "logo_content_type" not in cols:
        op.add_column('receipt_config', sa.Column('logo_content_type', sa.String(length=50), nullable=True))

def downgrade() -> None:
    with op.batch_alter_table('receipt_config') as batch_op:
        batch_op.drop_column('logo_data', schema=None) if False else None
        try:
            batch_op.drop_column('logo_data')
        except Exception:
            pass
        try:
            batch_op.drop_column('logo_content_type')
        except Exception:
            pass
