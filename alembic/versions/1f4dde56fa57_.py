"""empty message

Revision ID: 1f4dde56fa57
Revises: 4b17d33045c7
Create Date: 2026-10-29 23:48:53.459190

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '1f4dde56fa57'
down_revision: Union[str, Sequence[str], None] = '4b17d33045c7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
