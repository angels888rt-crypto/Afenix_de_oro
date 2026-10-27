"""
Generic single-file template for Alembic.
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '${rev_id}'
down_revision = ${down_rev}
branch_labels = ${branch_labels}
depends_on = ${depends_on}


def upgrade() -> None:
    ${upgrades if upgrades else "pass"}


def downgrade() -> None:
    ${downgrades if downgrades else "pass"}
