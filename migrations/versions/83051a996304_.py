"""empty message

Revision ID: 83051a996304
Revises: 87bbc8883c43
Create Date: 2016-11-25 18:21:20.201000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '83051a996304'
down_revision = '87bbc8883c43'
branch_labels = None
depends_on = None


def upgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.add_column('user', sa.Column('social_id', sa.String(length=64), nullable=True))
    op.drop_index('ix_user_username', table_name='user')
    op.create_index(op.f('ix_user_username'), 'user', ['username'], unique=False)
    op.create_unique_constraint(None, 'user', ['social_id'])
    ### end Alembic commands ###


def downgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint(None, 'user', type_='unique')
    op.drop_index(op.f('ix_user_username'), table_name='user')
    op.create_index('ix_user_username', 'user', ['username'], unique=True)
    op.drop_column('user', 'social_id')
    ### end Alembic commands ###
