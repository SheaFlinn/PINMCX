"""Add awarded_points and awarded_xp to Prediction model

Revision ID: {revision_id}
Revises: {previous_revision}
Create Date: {create_date}

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '{revision_id}'
down_revision = '{previous_revision}'
branch_labels = None
depends_on = None

def upgrade():
    # Add awarded_points and awarded_xp columns to prediction table
    op.add_column('prediction', sa.Column('awarded_points', sa.Float(), nullable=True))
    op.add_column('prediction', sa.Column('awarded_xp', sa.Integer(), nullable=True))

def downgrade():
    # Remove awarded_points and awarded_xp columns from prediction table
    op.drop_column('prediction', 'awarded_points')
    op.drop_column('prediction', 'awarded_xp')
