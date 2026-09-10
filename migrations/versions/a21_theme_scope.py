"""Organization scoped reusable design references."""

from alembic import op
import sqlalchemy as sa

revision = "a21_theme_scope"
down_revision = "39b4465bf603"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("templates", sa.Column("org_id", sa.String(36), nullable=True))
    op.create_index("ix_templates_org_id", "templates", ["org_id"])


def downgrade():
    op.drop_index("ix_templates_org_id", "templates")
    op.drop_column("templates", "org_id")
