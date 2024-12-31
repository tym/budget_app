"""Recreate models

Revision ID: 5aeb5a5feda0
Revises: 
Create Date: 2024-12-30 15:54:30.151132

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '5aeb5a5feda0'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('bill_category',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(length=100), nullable=False),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('name')
    )
    op.create_table('expense_category',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(length=100), nullable=False),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('name')
    )
    op.create_table('expenses',
    sa.Column('expense_id', sa.String(length=20), nullable=False),
    sa.Column('description', sa.String(length=80), nullable=False),
    sa.Column('amount', sa.Float(), nullable=False),
    sa.Column('date', sa.Date(), nullable=False),
    sa.Column('category', sa.String(length=50), nullable=True),
    sa.Column('cleared', sa.Boolean(), nullable=True),
    sa.Column('linked_id', sa.String(length=20), nullable=True),
    sa.PrimaryKeyConstraint('expense_id')
    )
    op.create_table('income_category',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(length=100), nullable=False),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('name')
    )
    op.create_table('bills',
    sa.Column('bill_id', sa.String(length=20), nullable=False),
    sa.Column('name', sa.String(length=255), nullable=False),
    sa.Column('amount', sa.Float(), nullable=False),
    sa.Column('due_day', sa.Integer(), nullable=False),
    sa.Column('category_id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['category_id'], ['bill_category.id'], ),
    sa.PrimaryKeyConstraint('bill_id')
    )
    op.create_table('incomes',
    sa.Column('income_id', sa.String(length=20), nullable=False),
    sa.Column('name', sa.String(length=80), nullable=False),
    sa.Column('amount', sa.Float(), nullable=False),
    sa.Column('frequency', sa.String(length=20), nullable=False),
    sa.Column('start_date', sa.Date(), nullable=False),
    sa.Column('day_of_week', sa.String(length=10), nullable=True),
    sa.Column('category_id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['category_id'], ['income_category.id'], ),
    sa.PrimaryKeyConstraint('income_id')
    )
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
    op.drop_table('incomes')
    op.drop_table('bills')
    op.drop_table('income_category')
    op.drop_table('expenses')
    op.drop_table('expense_category')
    op.drop_table('bill_category')
    # ### end Alembic commands ###