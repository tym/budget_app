"""Add start_date column to bills table

Revision ID: e72c83c35dc8
Revises: 9a41673a7d9a
Create Date: 2025-01-05 10:50:22.096085

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'e72c83c35dc8'
down_revision = '9a41673a7d9a'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('budget_table')
    
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('budget_table',
    sa.Column('entry_id', sa.TEXT(), autoincrement=False, nullable=False),
    sa.Column('entry_type', sa.VARCHAR(length=10), autoincrement=False, nullable=False),
    sa.Column('description', sa.TEXT(), autoincrement=False, nullable=False),
    sa.Column('expected_date', sa.DATE(), autoincrement=False, nullable=False),
    sa.Column('actual_date', sa.DATE(), autoincrement=False, nullable=True),
    sa.Column('expected_amount', sa.NUMERIC(), autoincrement=False, nullable=False),
    sa.Column('actual_amount', sa.NUMERIC(), autoincrement=False, nullable=True),
    sa.Column('cleared', sa.BOOLEAN(), server_default=sa.text('false'), autoincrement=False, nullable=True),
    sa.Column('not_expected', sa.BOOLEAN(), server_default=sa.text('false'), autoincrement=False, nullable=True),
    sa.PrimaryKeyConstraint('entry_id', name='budget_table_pkey')
    )
    # ### end Alembic commands ###
