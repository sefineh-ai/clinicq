"""Initial database schema with indexes and constraints

Revision ID: 001_initial
Revises: 
Create Date: 2026-11-21 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '001_initial'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Users table
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('hashed_password', sa.String(length=255), nullable=False),
        sa.Column('full_name', sa.String(length=255), nullable=False),
        sa.Column('role', sa.Enum('admin', 'receptionist', 'doctor', name='userrole'), nullable=False),
        sa.Column('is_active', sa.Boolean(), server_default=sa.text('true'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)
    op.create_index(op.f('ix_users_id'), 'users', ['id'], unique=False)
    op.create_index(op.f('ix_users_role'), 'users', ['role'], unique=False)

    # Doctors table
    op.create_table(
        'doctors',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('specialty', sa.String(length=100), nullable=False),
        sa.Column('room_number', sa.String(length=50), nullable=False),
        sa.Column('bio', sa.Text(), nullable=True),
        sa.Column('is_active', sa.Boolean(), server_default=sa.text('true'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id'),
    )
    op.create_index(op.f('ix_doctors_id'), 'doctors', ['id'], unique=False)

    # Schedules table
    op.create_table(
        'doctor_schedules',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('doctor_id', sa.Integer(), nullable=False),
        sa.Column('day_of_week', sa.Integer(), nullable=False),
        sa.Column('start_time', sa.Time(), nullable=False),
        sa.Column('end_time', sa.Time(), nullable=False),
        sa.Column('slot_duration_minutes', sa.Integer(), server_default='20', nullable=False),
        sa.Column('is_active', sa.Boolean(), server_default=sa.text('true'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['doctor_id'], ['doctors.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('doctor_id', 'day_of_week', name='uq_doctor_schedule_day'),
    )
    op.create_index(op.f('ix_doctor_schedules_doctor_id'), 'doctor_schedules', ['doctor_id'], unique=False)
    op.create_index(op.f('ix_doctor_schedules_id'), 'doctor_schedules', ['id'], unique=False)

    # Appointments table
    op.create_table(
        'appointments',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('doctor_id', sa.Integer(), nullable=False),
        sa.Column('patient_name', sa.String(length=255), nullable=False),
        sa.Column('patient_phone', sa.String(length=50), nullable=False),
        sa.Column('reason', sa.String(length=500), nullable=False),
        sa.Column('appointment_date', sa.Date(), nullable=False),
        sa.Column('start_time', sa.Time(), nullable=False),
        sa.Column('end_time', sa.Time(), nullable=False),
        sa.Column('status', sa.Enum('booked', 'checked_in', 'called', 'in_consultation', 'completed', 'cancelled', 'no_show', name='appointmentstatus'), server_default='booked', nullable=False),
        sa.Column('booked_by_user_id', sa.Integer(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['booked_by_user_id'], ['users.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['doctor_id'], ['doctors.id'], ondelete='RESTRICT'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_appointments_appointment_date'), 'appointments', ['appointment_date'], unique=False)
    op.create_index(op.f('ix_appointments_doctor_id'), 'appointments', ['doctor_id'], unique=False)
    op.create_index(op.f('ix_appointments_id'), 'appointments', ['id'], unique=False)
    op.create_index(op.f('ix_appointments_patient_phone'), 'appointments', ['patient_phone'], unique=False)
    op.create_index(op.f('ix_appointments_status'), 'appointments', ['status'], unique=False)

    # Race condition protection: unique index on active appointment slots
    op.create_index(
        'uq_doctor_slot_active',
        'appointments',
        ['doctor_id', 'appointment_date', 'start_time'],
        unique=True,
        postgresql_where=sa.text("status != 'cancelled'"),
    )

    # Queue tickets table
    op.create_table(
        'queue_tickets',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('appointment_id', sa.Integer(), nullable=False),
        sa.Column('doctor_id', sa.Integer(), nullable=False),
        sa.Column('ticket_number', sa.String(length=50), nullable=False),
        sa.Column('status', sa.Enum('waiting', 'called', 'in_consultation', 'completed', 'no_show', name='queuestatus'), server_default='waiting', nullable=False),
        sa.Column('check_in_time', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('called_time', sa.DateTime(timezone=True), nullable=True),
        sa.Column('consultation_start_time', sa.DateTime(timezone=True), nullable=True),
        sa.Column('completed_time', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['appointment_id'], ['appointments.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['doctor_id'], ['doctors.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('appointment_id'),
    )
    op.create_index(op.f('ix_queue_tickets_check_in_time'), 'queue_tickets', ['check_in_time'], unique=False)
    op.create_index(op.f('ix_queue_tickets_doctor_id'), 'queue_tickets', ['doctor_id'], unique=False)
    op.create_index(op.f('ix_queue_tickets_id'), 'queue_tickets', ['id'], unique=False)
    op.create_index(op.f('ix_queue_tickets_status'), 'queue_tickets', ['status'], unique=False)
    op.create_index(op.f('ix_queue_tickets_ticket_number'), 'queue_tickets', ['ticket_number'], unique=False)

    # Audit logs table
    op.create_table(
        'audit_logs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('user_name', sa.String(length=255), nullable=False),
        sa.Column('user_role', sa.String(length=50), nullable=False),
        sa.Column('action', sa.Enum(
            'booking_created', 'booking_cancelled', 'booking_rescheduled',
            'patient_checked_in', 'patient_called', 'consultation_started',
            'consultation_completed', 'appointment_no_show',
            name='auditaction'
        ), nullable=False),
        sa.Column('entity_type', sa.String(length=50), nullable=False),
        sa.Column('entity_id', sa.Integer(), nullable=False),
        sa.Column('details', sa.JSON(), nullable=True),
        sa.Column('ip_address', sa.String(length=45), nullable=True),
        sa.Column('timestamp', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_audit_logs_action'), 'audit_logs', ['action'], unique=False)
    op.create_index(op.f('ix_audit_logs_entity_id'), 'audit_logs', ['entity_id'], unique=False)
    op.create_index(op.f('ix_audit_logs_entity_type'), 'audit_logs', ['entity_type'], unique=False)
    op.create_index(op.f('ix_audit_logs_id'), 'audit_logs', ['id'], unique=False)
    op.create_index(op.f('ix_audit_logs_timestamp'), 'audit_logs', ['timestamp'], unique=False)
    op.create_index(op.f('ix_audit_logs_user_id'), 'audit_logs', ['user_id'], unique=False)


def downgrade() -> None:
    op.drop_table('audit_logs')
    op.drop_table('queue_tickets')
    op.drop_table('appointments')
    op.drop_table('doctor_schedules')
    op.drop_table('doctors')
    op.drop_table('users')
    op.execute("DROP TYPE IF EXISTS auditaction;")
    op.execute("DROP TYPE IF EXISTS queuestatus;")
    op.execute("DROP TYPE IF EXISTS appointmentstatus;")
    op.execute("DROP TYPE IF EXISTS userrole;")
