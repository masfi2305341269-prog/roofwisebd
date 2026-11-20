"""Link public.users to Supabase auth.users via auth_user_id

Revision ID: b6f49c365d8f
Revises: a5764b316a82
Create Date: 2026-11-18
"""
from alembic import op
import sqlalchemy as sa

revision = 'b6f49c365d8f'
down_revision = 'a5764b316a82'
branch_labels = None
depends_on = None

def upgrade() -> None:
    # Add auth_user_id and email_verified columns to users table
    bind = op.get_bind()
    insp = sa.inspect(bind)
    cols = [c["name"] for c in insp.get_columns("users")]
    with op.batch_alter_table('users') as batch_op:
        if 'auth_user_id' not in cols:
            batch_op.add_column(sa.Column('auth_user_id', sa.String(36), nullable=True))
            batch_op.create_unique_constraint('uq_users_auth_user_id', ['auth_user_id'])
            batch_op.create_index('ix_users_auth_user_id', ['auth_user_id'])
            batch_op.alter_column('hashed_password', nullable=True)
        if 'email_verified' not in cols:
            batch_op.add_column(sa.Column('email_verified', sa.Boolean(), server_default=sa.true(), nullable=False))

def downgrade() -> None:
    with op.batch_alter_table('users') as batch_op:
        batch_op.drop_index('ix_users_auth_user_id')
        batch_op.drop_constraint('uq_users_auth_user_id', type_='unique')
        batch_op.drop_column('auth_user_id')
        batch_op.alter_column('hashed_password', nullable=False)
