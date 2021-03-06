"""empty message

Revision ID: 4f4e3e365bc0
Revises: 42f324e8531d
Create Date: 2016-12-02 11:37:24.689000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = '4f4e3e365bc0'
down_revision = '42f324e8531d'
branch_labels = None
depends_on = None


def upgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.add_column('user', sa.Column('images', sa.String(length=256), nullable=True))
    op.drop_column('user', 'image')
    ### end Alembic commands ###


def downgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.add_column('user', sa.Column('image', mysql.VARCHAR(length=64), nullable=True))
    op.drop_column('user', 'images')
    ### end Alembic commands ###
