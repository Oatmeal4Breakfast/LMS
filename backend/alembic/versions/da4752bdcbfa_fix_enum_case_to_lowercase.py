"""fix enum case to lowercase

Revision ID: da4752bdcbfa
Revises: c6b261ed4b78
Create Date: 2026-04-06 13:53:00.063031

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "da4752bdcbfa"
down_revision: Union[str, Sequence[str], None] = "c6b261ed4b78"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.execute("ALTER TYPE department RENAME TO department_old")
    op.execute("CREATE TYPE department AS ENUM ('pos', 'it', 'av')")
    op.execute(
        "ALTER TABLE user_account ALTER COLUMN department TYPE department USING department::text::department"
    )
    op.execute(
        "ALTER TABLE training_path ALTER COLUMN department TYPE department USING department::text::department"
    )
    op.execute("DROP TYPE department_old")

    op.execute("ALTER TYPE user_type RENAME TO user_type_old")
    op.execute("CREATE TYPE user_type AS ENUM ('admin', 'staff', 'trainer')")
    op.execute(
        "ALTER TABLE user_account ALTER COLUMN user_type TYPE user_type USING user_type::text::user_type"
    )
    op.execute("DROP TYPE user_type_old")


def downgrade() -> None:
    """Downgrade schema."""
    op.execute("ALTER TYPE department RENAME TO department_old")
    op.execute("CREATE TYPE department AS ENUM ('POS', 'IT', 'AV')")
    op.execute(
        "ALTER TABLE user_account ALTER COLUMN department TYPE department USING department::text::department"
    )
    op.execute(
        "ALTER TABLE training_path ALTER COLUMN department TYPE department USING department::text::department"
    )
    op.execute("DROP TYPE department_old")

    op.execute("ALTER TYPE user_type RENAME TO user_type_old")
    op.execute("CREATE TYPE user_type AS ENUM ('ADMIN', 'STAFF', 'TRAINER')")
    op.execute(
        "ALTER TABLE user_account ALTER COLUMN user_type TYPE user_type USING user_type::text::user_type"
    )
    op.execute("DROP TYPE user_type_old")
