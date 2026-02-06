"""Initial database schema

Revision ID: 001
Revises: 
Create Date: 2024-01-15 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create all tables for ExportSathi."""
    
    # Enable UUID extension
    op.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"')
    
    # Create users table
    op.create_table(
        'users',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('uuid_generate_v4()')),
        sa.Column('email', sa.String(255), nullable=False, unique=True),
        sa.Column('password_hash', sa.String(255), nullable=False),
        sa.Column('business_type', sa.String(50), nullable=False),
        sa.Column('company_size', sa.String(50), nullable=False),
        sa.Column('company_name', sa.String(255)),
        sa.Column('monthly_volume', sa.Integer()),
        sa.Column('created_at', sa.TIMESTAMP(), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.TIMESTAMP(), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('last_login', sa.TIMESTAMP()),
        sa.CheckConstraint("business_type IN ('Manufacturing', 'SaaS', 'Merchant')", name='check_business_type'),
        sa.CheckConstraint("company_size IN ('Micro', 'Small', 'Medium')", name='check_company_size'),
    )
    op.create_index('idx_users_email', 'users', ['email'])
    op.create_index('idx_users_business_type', 'users', ['business_type'])
    
    # Create reports table
    op.create_table(
        'reports',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('uuid_generate_v4()')),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE')),
        sa.Column('product_name', sa.String(255), nullable=False),
        sa.Column('product_image_url', sa.String(500)),
        sa.Column('ingredients', sa.Text()),
        sa.Column('bom', sa.Text()),
        sa.Column('destination_country', sa.String(100), nullable=False),
        sa.Column('business_type', sa.String(50), nullable=False),
        sa.Column('company_size', sa.String(50), nullable=False),
        sa.Column('monthly_volume', sa.Integer()),
        sa.Column('price_range', sa.String(100)),
        sa.Column('payment_mode', sa.String(100)),
        sa.Column('hs_code', sa.String(20)),
        sa.Column('hs_code_confidence', sa.DECIMAL(5, 2)),
        sa.Column('risk_score', sa.Integer()),
        sa.Column('estimated_cost', sa.DECIMAL(12, 2)),
        sa.Column('estimated_timeline_days', sa.Integer()),
        sa.Column('report_data', postgresql.JSONB(), nullable=False),
        sa.Column('status', sa.String(50), server_default='completed'),
        sa.Column('created_at', sa.TIMESTAMP(), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.TIMESTAMP(), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.CheckConstraint('risk_score >= 0 AND risk_score <= 100', name='check_risk_score_range'),
        sa.CheckConstraint("status IN ('processing', 'completed', 'failed')", name='check_report_status'),
    )
    op.create_index('idx_reports_user_id', 'reports', ['user_id'])
    op.create_index('idx_reports_hs_code', 'reports', ['hs_code'])
    op.create_index('idx_reports_destination', 'reports', ['destination_country'])
    op.create_index('idx_reports_created_at', 'reports', ['created_at'], postgresql_using='btree', postgresql_ops={'created_at': 'DESC'})
    
    # Create certification_progress table
    op.create_table(
        'certification_progress',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('uuid_generate_v4()')),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE')),
        sa.Column('report_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('reports.id', ondelete='CASCADE')),
        sa.Column('certification_id', sa.String(100), nullable=False),
        sa.Column('certification_name', sa.String(255), nullable=False),
        sa.Column('certification_type', sa.String(50), nullable=False),
        sa.Column('status', sa.String(50), server_default='not_started'),
        sa.Column('documents_completed', postgresql.JSONB(), server_default=sa.text("'[]'::jsonb")),
        sa.Column('notes', sa.Text()),
        sa.Column('started_at', sa.TIMESTAMP()),
        sa.Column('completed_at', sa.TIMESTAMP()),
        sa.Column('created_at', sa.TIMESTAMP(), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.TIMESTAMP(), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.CheckConstraint("status IN ('not_started', 'in_progress', 'completed', 'rejected')", name='check_certification_status'),
    )
    op.create_index('idx_cert_progress_user_id', 'certification_progress', ['user_id'])
    op.create_index('idx_cert_progress_report_id', 'certification_progress', ['report_id'])
    op.create_index('idx_cert_progress_status', 'certification_progress', ['status'])
    
    # Create generated_documents table
    op.create_table(
        'generated_documents',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('uuid_generate_v4()')),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE')),
        sa.Column('report_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('reports.id', ondelete='CASCADE')),
        sa.Column('document_type', sa.String(100), nullable=False),
        sa.Column('document_data', postgresql.JSONB(), nullable=False),
        sa.Column('pdf_url', sa.String(500)),
        sa.Column('editable_url', sa.String(500)),
        sa.Column('validation_results', postgresql.JSONB()),
        sa.Column('is_valid', sa.Boolean(), server_default='false'),
        sa.Column('created_at', sa.TIMESTAMP(), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.TIMESTAMP(), server_default=sa.text('CURRENT_TIMESTAMP')),
    )
    op.create_index('idx_gen_docs_user_id', 'generated_documents', ['user_id'])
    op.create_index('idx_gen_docs_report_id', 'generated_documents', ['report_id'])
    op.create_index('idx_gen_docs_type', 'generated_documents', ['document_type'])
    
    # Create action_plan_progress table
    op.create_table(
        'action_plan_progress',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('uuid_generate_v4()')),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE')),
        sa.Column('report_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('reports.id', ondelete='CASCADE')),
        sa.Column('task_id', sa.String(100), nullable=False),
        sa.Column('day_number', sa.Integer(), nullable=False),
        sa.Column('task_title', sa.String(255), nullable=False),
        sa.Column('task_description', sa.Text()),
        sa.Column('task_category', sa.String(50)),
        sa.Column('completed', sa.Boolean(), server_default='false'),
        sa.Column('completed_at', sa.TIMESTAMP()),
        sa.Column('created_at', sa.TIMESTAMP(), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.TIMESTAMP(), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.CheckConstraint('day_number >= 1 AND day_number <= 7', name='check_day_number_range'),
        sa.UniqueConstraint('report_id', 'task_id', name='idx_action_plan_unique'),
    )
    op.create_index('idx_action_plan_user_id', 'action_plan_progress', ['user_id'])
    op.create_index('idx_action_plan_report_id', 'action_plan_progress', ['report_id'])
    op.create_index('idx_action_plan_completed', 'action_plan_progress', ['completed'])
    
    # Create chat_sessions table
    op.create_table(
        'chat_sessions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('uuid_generate_v4()')),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE')),
        sa.Column('report_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('reports.id', ondelete='CASCADE')),
        sa.Column('context_data', postgresql.JSONB()),
        sa.Column('created_at', sa.TIMESTAMP(), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('last_activity', sa.TIMESTAMP(), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('expires_at', sa.TIMESTAMP()),
    )
    op.create_index('idx_chat_sessions_user_id', 'chat_sessions', ['user_id'])
    op.create_index('idx_chat_sessions_report_id', 'chat_sessions', ['report_id'])
    op.create_index('idx_chat_sessions_expires_at', 'chat_sessions', ['expires_at'])
    
    # Create chat_messages table
    op.create_table(
        'chat_messages',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('uuid_generate_v4()')),
        sa.Column('session_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('chat_sessions.id', ondelete='CASCADE')),
        sa.Column('role', sa.String(20), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('sources', postgresql.JSONB()),
        sa.Column('created_at', sa.TIMESTAMP(), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.CheckConstraint("role IN ('user', 'assistant')", name='check_message_role'),
    )
    op.create_index('idx_chat_messages_session_id', 'chat_messages', ['session_id'])
    op.create_index('idx_chat_messages_created_at', 'chat_messages', ['created_at'])
    
    # Create finance_analysis table
    op.create_table(
        'finance_analysis',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('uuid_generate_v4()')),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE')),
        sa.Column('report_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('reports.id', ondelete='CASCADE')),
        sa.Column('working_capital_data', postgresql.JSONB(), nullable=False),
        sa.Column('pre_shipment_credit_data', postgresql.JSONB()),
        sa.Column('rodtep_benefit_data', postgresql.JSONB()),
        sa.Column('gst_refund_data', postgresql.JSONB()),
        sa.Column('cash_flow_timeline', postgresql.JSONB()),
        sa.Column('financing_options', postgresql.JSONB()),
        sa.Column('created_at', sa.TIMESTAMP(), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.TIMESTAMP(), server_default=sa.text('CURRENT_TIMESTAMP')),
    )
    op.create_index('idx_finance_analysis_user_id', 'finance_analysis', ['user_id'])
    op.create_index('idx_finance_analysis_report_id', 'finance_analysis', ['report_id'])
    
    # Create logistics_analysis table
    op.create_table(
        'logistics_analysis',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('uuid_generate_v4()')),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE')),
        sa.Column('report_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('reports.id', ondelete='CASCADE')),
        sa.Column('lcl_fcl_comparison', postgresql.JSONB()),
        sa.Column('rms_probability_data', postgresql.JSONB()),
        sa.Column('route_analysis', postgresql.JSONB()),
        sa.Column('freight_estimate', postgresql.JSONB()),
        sa.Column('insurance_recommendation', postgresql.JSONB()),
        sa.Column('created_at', sa.TIMESTAMP(), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.TIMESTAMP(), server_default=sa.text('CURRENT_TIMESTAMP')),
    )
    op.create_index('idx_logistics_analysis_user_id', 'logistics_analysis', ['user_id'])
    op.create_index('idx_logistics_analysis_report_id', 'logistics_analysis', ['report_id'])
    
    # Create user_metrics table
    op.create_table(
        'user_metrics',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('uuid_generate_v4()')),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), unique=True),
        sa.Column('reports_generated', sa.Integer(), server_default='0'),
        sa.Column('certifications_completed', sa.Integer(), server_default='0'),
        sa.Column('documents_generated', sa.Integer(), server_default='0'),
        sa.Column('exports_completed', sa.Integer(), server_default='0'),
        sa.Column('cost_savings', sa.DECIMAL(12, 2), server_default='0'),
        sa.Column('timeline_reduction_days', sa.Integer(), server_default='0'),
        sa.Column('last_export_date', sa.TIMESTAMP()),
        sa.Column('created_at', sa.TIMESTAMP(), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.TIMESTAMP(), server_default=sa.text('CURRENT_TIMESTAMP')),
    )
    op.create_index('idx_user_metrics_user_id', 'user_metrics', ['user_id'])
    
    # Create function for updating updated_at timestamp
    op.execute("""
        CREATE OR REPLACE FUNCTION update_updated_at_column()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.updated_at = CURRENT_TIMESTAMP;
            RETURN NEW;
        END;
        $$ language 'plpgsql';
    """)
    
    # Create triggers for updated_at
    op.execute("""
        CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
            FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
    """)
    op.execute("""
        CREATE TRIGGER update_reports_updated_at BEFORE UPDATE ON reports
            FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
    """)
    op.execute("""
        CREATE TRIGGER update_cert_progress_updated_at BEFORE UPDATE ON certification_progress
            FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
    """)
    op.execute("""
        CREATE TRIGGER update_gen_docs_updated_at BEFORE UPDATE ON generated_documents
            FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
    """)
    op.execute("""
        CREATE TRIGGER update_action_plan_updated_at BEFORE UPDATE ON action_plan_progress
            FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
    """)
    op.execute("""
        CREATE TRIGGER update_finance_analysis_updated_at BEFORE UPDATE ON finance_analysis
            FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
    """)
    op.execute("""
        CREATE TRIGGER update_logistics_analysis_updated_at BEFORE UPDATE ON logistics_analysis
            FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
    """)
    op.execute("""
        CREATE TRIGGER update_user_metrics_updated_at BEFORE UPDATE ON user_metrics
            FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
    """)


def downgrade() -> None:
    """Drop all tables."""
    
    # Drop triggers
    op.execute('DROP TRIGGER IF EXISTS update_users_updated_at ON users')
    op.execute('DROP TRIGGER IF EXISTS update_reports_updated_at ON reports')
    op.execute('DROP TRIGGER IF EXISTS update_cert_progress_updated_at ON certification_progress')
    op.execute('DROP TRIGGER IF EXISTS update_gen_docs_updated_at ON generated_documents')
    op.execute('DROP TRIGGER IF EXISTS update_action_plan_updated_at ON action_plan_progress')
    op.execute('DROP TRIGGER IF EXISTS update_finance_analysis_updated_at ON finance_analysis')
    op.execute('DROP TRIGGER IF EXISTS update_logistics_analysis_updated_at ON logistics_analysis')
    op.execute('DROP TRIGGER IF EXISTS update_user_metrics_updated_at ON user_metrics')
    
    # Drop function
    op.execute('DROP FUNCTION IF EXISTS update_updated_at_column()')
    
    # Drop tables in reverse order (respecting foreign keys)
    op.drop_table('user_metrics')
    op.drop_table('logistics_analysis')
    op.drop_table('finance_analysis')
    op.drop_table('chat_messages')
    op.drop_table('chat_sessions')
    op.drop_table('action_plan_progress')
    op.drop_table('generated_documents')
    op.drop_table('certification_progress')
    op.drop_table('reports')
    op.drop_table('users')
    
    # Drop UUID extension
    op.execute('DROP EXTENSION IF EXISTS "uuid-ossp"')
