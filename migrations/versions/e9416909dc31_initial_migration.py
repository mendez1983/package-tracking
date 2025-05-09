"""Initial migration

Revision ID: e9416909dc31
Revises: 
Create Date: 2025-04-09 15:40:13.249354

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'e9416909dc31'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('customers',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(length=100), nullable=False),
    sa.Column('email', sa.String(length=100), nullable=False),
    sa.Column('phone', sa.String(length=20), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('email')
    )
    op.create_table('users',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('username', sa.String(length=50), nullable=False),
    sa.Column('email', sa.String(length=100), nullable=False),
    sa.Column('password_hash', sa.String(length=128), nullable=False),
    sa.Column('is_admin', sa.Boolean(), nullable=True),
    sa.Column('is_active', sa.Boolean(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('email'),
    sa.UniqueConstraint('username')
    )
    op.create_table('packages',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('tracking_number', sa.String(length=20), nullable=False),
    sa.Column('customer_id', sa.Integer(), nullable=False),
    sa.Column('branch', sa.String(length=50), nullable=False),
    sa.Column('sender_name', sa.String(length=100), nullable=False),
    sa.Column('sender_email', sa.String(length=100), nullable=False),
    sa.Column('sender_phone', sa.String(length=20), nullable=False),
    sa.Column('recipient_name', sa.String(length=100), nullable=False),
    sa.Column('recipient_address', sa.Text(), nullable=False),
    sa.Column('recipient_phone', sa.String(length=20), nullable=False),
    sa.Column('destination_country_code', sa.String(length=3), nullable=False),
    sa.Column('destination_country_name', sa.String(length=50), nullable=False),
    sa.Column('estimated_weight', sa.Float(), nullable=False),
    sa.Column('actual_weight', sa.Float(), nullable=True),
    sa.Column('estimated_cost', sa.Float(), nullable=False),
    sa.Column('final_cost', sa.Float(), nullable=True),
    sa.Column('package_type', sa.Enum('DOCUMENT', 'BOX_SMALL', 'BOX_MEDIUM', 'BOX_LARGE', 'FRAGILE', 'SPECIAL', name='packagetypeenum'), nullable=False),
    sa.Column('status', sa.Enum('REGISTERED', 'PROCESSING', 'TRANSIT', 'CUSTOMS', 'DELIVERY', 'DELIVERED', 'RETURNED', 'LOST', name='statusenum'), nullable=False),
    sa.Column('registration_date', sa.DateTime(), nullable=False),
    sa.Column('delivery_date', sa.DateTime(), nullable=True),
    sa.Column('current_location', sa.String(length=100), nullable=True),
    sa.Column('notification_sent', sa.Boolean(), nullable=True),
    sa.ForeignKeyConstraint(['customer_id'], ['customers.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('tracking_number')
    )
    op.create_table('notifications',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('package_id', sa.Integer(), nullable=False),
    sa.Column('method', sa.Enum('EMAIL', 'SMS', 'CALL', name='notificationmethodenum'), nullable=False),
    sa.Column('recipient', sa.String(length=100), nullable=False),
    sa.Column('message', sa.Text(), nullable=False),
    sa.Column('sent_at', sa.DateTime(), nullable=True),
    sa.Column('success', sa.Boolean(), nullable=True),
    sa.Column('error_message', sa.Text(), nullable=True),
    sa.ForeignKeyConstraint(['package_id'], ['packages.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('tracking_events',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('package_id', sa.Integer(), nullable=False),
    sa.Column('date', sa.DateTime(), nullable=False),
    sa.Column('location', sa.String(length=100), nullable=False),
    sa.Column('status', sa.Enum('REGISTERED', 'PROCESSING', 'TRANSIT', 'CUSTOMS', 'DELIVERY', 'DELIVERED', 'RETURNED', 'LOST', name='statusenum'), nullable=False),
    sa.Column('description', sa.String(length=200), nullable=False),
    sa.Column('notes', sa.Text(), nullable=True),
    sa.Column('created_by_id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['created_by_id'], ['users.id'], ),
    sa.ForeignKeyConstraint(['package_id'], ['packages.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('tracking_events')
    op.drop_table('notifications')
    op.drop_table('packages')
    op.drop_table('users')
    op.drop_table('customers')
    # ### end Alembic commands ###
