"""create device table

Revision ID: e952df129f60
Revises: 
Create Date: 2019-06-10 09:10:50.775198

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'e952df129f60'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'devices',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('status', sa.String(20), nullable=False),
        sa.Column('description', sa.String(200)),
        sa.Column('user', sa.Integer),
    )


def downgrade():
    op.drop_table('devices')
