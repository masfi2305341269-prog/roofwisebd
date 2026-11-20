"""create_initial_assessments_table

Revision ID: 19a84b124801
Revises: 
Create Date: 2026-11-16 19:00:00.000000

Baseline migration: Creates the initial assessments table (29 columns).
Allows fresh database installations to run the full migration chain.
"""
from typing import Sequence, Union
from alembic import op, context
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '19a84b124801'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create initial assessments table if not already present."""
    should_create = True
    if not context.is_offline_mode():
        conn = op.get_bind()
        inspector = sa.inspect(conn)
        if 'assessments' in inspector.get_table_names():
            should_create = False

    if should_create:
        op.create_table(
            'assessments',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('created_at', sa.DateTime(), nullable=True),
            sa.Column('division', sa.String(length=50), nullable=False),
            sa.Column('district', sa.String(length=50), nullable=False),
            sa.Column('area', sa.String(length=100), nullable=True),
            sa.Column('latitude', sa.Float(), nullable=True),
            sa.Column('longitude', sa.Float(), nullable=True),
            sa.Column('monthly_units_kwh', sa.Float(), nullable=False),
            sa.Column('billing_period_days', sa.Integer(), nullable=True),
            sa.Column('bill_amount_bdt', sa.Float(), nullable=True),
            sa.Column('sanctioned_load_kw', sa.Float(), nullable=True),
            sa.Column('consumer_category', sa.String(length=50), nullable=True),
            sa.Column('total_area_sqft', sa.Float(), nullable=False),
            sa.Column('usable_area_sqft', sa.Float(), nullable=False),
            sa.Column('roof_type', sa.String(length=50), nullable=True),
            sa.Column('shading_condition', sa.String(length=50), nullable=True),
            sa.Column('orientation', sa.String(length=50), nullable=True),
            sa.Column('tilt_degrees', sa.Float(), nullable=True),
            sa.Column('bill_file_path', sa.String(length=255), nullable=True),
            sa.Column('recommended_capacity_kwp', sa.Float(), nullable=False),
            sa.Column('recommended_inverter_ac_kw', sa.Float(), nullable=False),
            sa.Column('panel_count', sa.Integer(), nullable=False),
            sa.Column('daily_generation_kwh', sa.Float(), nullable=False),
            sa.Column('monthly_generation_kwh', sa.Float(), nullable=False),
            sa.Column('annual_generation_kwh', sa.Float(), nullable=False),
            sa.Column('monthly_savings_bdt', sa.Float(), nullable=False),
            sa.Column('estimated_payback_years', sa.Float(), nullable=False),
            sa.Column('sreda_compliant', sa.Boolean(), nullable=True),
            sa.Column('notes', sa.Text(), nullable=True),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index(op.f('ix_assessments_id'), 'assessments', ['id'], unique=False)


def downgrade() -> None:
    """Drop initial assessments table."""
    op.drop_index(op.f('ix_assessments_id'), table_name='assessments')
    op.drop_table('assessments')
