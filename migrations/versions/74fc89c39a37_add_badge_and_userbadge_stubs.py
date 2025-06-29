"""ADD: Badge and UserBadge stubs

Revision ID: 74fc89c39a37
Revises: 53eb04838887
Create Date: 2025-06-28 20:15:22.441677

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '74fc89c39a37'
down_revision = '53eb04838887'
branch_labels = None
depends_on = None

def upgrade():
    # Create badge table if it doesn't exist
    op.create_table('badge',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('type', sa.String(length=50), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('description', sa.String(length=200)),
        sa.Column('icon', sa.String(length=100)),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Update user_badges table
    with op.batch_alter_table('user_badges', schema=None) as batch_op:
        batch_op.add_column(sa.Column('created_at', sa.DATETIME(), nullable=True))
        batch_op.create_foreign_key('fk_user_badges_badge', 'badge', ['badge_id'], ['id'])

def downgrade():
    with op.batch_alter_table('user_badges', schema=None) as batch_op:
        batch_op.drop_constraint('fk_user_badges_badge', type_='foreignkey')
        batch_op.drop_column('created_at')
    
    op.drop_table('badge')
