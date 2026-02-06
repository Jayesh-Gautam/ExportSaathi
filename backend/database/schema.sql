-- ExportSathi Database Schema for PostgreSQL
-- This schema supports the complete ExportSathi platform

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Users table
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    business_type VARCHAR(50) NOT NULL CHECK (business_type IN ('Manufacturing', 'SaaS', 'Merchant')),
    company_size VARCHAR(50) NOT NULL CHECK (company_size IN ('Micro', 'Small', 'Medium')),
    company_name VARCHAR(255),
    monthly_volume INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP
);

CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_business_type ON users(business_type);

-- Export readiness reports table
CREATE TABLE reports (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    product_name VARCHAR(255) NOT NULL,
    product_image_url VARCHAR(500),
    ingredients TEXT,
    bom TEXT,
    destination_country VARCHAR(100) NOT NULL,
    business_type VARCHAR(50) NOT NULL,
    company_size VARCHAR(50) NOT NULL,
    monthly_volume INTEGER,
    price_range VARCHAR(100),
    payment_mode VARCHAR(100),
    hs_code VARCHAR(20),
    hs_code_confidence DECIMAL(5,2),
    risk_score INTEGER CHECK (risk_score >= 0 AND risk_score <= 100),
    estimated_cost DECIMAL(12,2),
    estimated_timeline_days INTEGER,
    report_data JSONB NOT NULL,
    status VARCHAR(50) DEFAULT 'completed' CHECK (status IN ('processing', 'completed', 'failed')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_reports_user_id ON reports(user_id);
CREATE INDEX idx_reports_hs_code ON reports(hs_code);
CREATE INDEX idx_reports_destination ON reports(destination_country);
CREATE INDEX idx_reports_created_at ON reports(created_at DESC);

-- Certifications progress tracking
CREATE TABLE certification_progress (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    report_id UUID REFERENCES reports(id) ON DELETE CASCADE,
    certification_id VARCHAR(100) NOT NULL,
    certification_name VARCHAR(255) NOT NULL,
    certification_type VARCHAR(50) NOT NULL,
    status VARCHAR(50) DEFAULT 'not_started' CHECK (status IN ('not_started', 'in_progress', 'completed', 'rejected')),
    documents_completed JSONB DEFAULT '[]'::jsonb,
    notes TEXT,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_cert_progress_user_id ON certification_progress(user_id);
CREATE INDEX idx_cert_progress_report_id ON certification_progress(report_id);
CREATE INDEX idx_cert_progress_status ON certification_progress(status);

-- Generated documents table
CREATE TABLE generated_documents (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    report_id UUID REFERENCES reports(id) ON DELETE CASCADE,
    document_type VARCHAR(100) NOT NULL,
    document_data JSONB NOT NULL,
    pdf_url VARCHAR(500),
    editable_url VARCHAR(500),
    validation_results JSONB,
    is_valid BOOLEAN DEFAULT false,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_gen_docs_user_id ON generated_documents(user_id);
CREATE INDEX idx_gen_docs_report_id ON generated_documents(report_id);
CREATE INDEX idx_gen_docs_type ON generated_documents(document_type);

-- Action plan progress tracking
CREATE TABLE action_plan_progress (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    report_id UUID REFERENCES reports(id) ON DELETE CASCADE,
    task_id VARCHAR(100) NOT NULL,
    day_number INTEGER NOT NULL CHECK (day_number >= 1 AND day_number <= 7),
    task_title VARCHAR(255) NOT NULL,
    task_description TEXT,
    task_category VARCHAR(50),
    completed BOOLEAN DEFAULT false,
    completed_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(report_id, task_id)
);

CREATE INDEX idx_action_plan_user_id ON action_plan_progress(user_id);
CREATE INDEX idx_action_plan_report_id ON action_plan_progress(report_id);
CREATE INDEX idx_action_plan_completed ON action_plan_progress(completed);

-- Chat sessions table
CREATE TABLE chat_sessions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    report_id UUID REFERENCES reports(id) ON DELETE CASCADE,
    context_data JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP
);

CREATE INDEX idx_chat_sessions_user_id ON chat_sessions(user_id);
CREATE INDEX idx_chat_sessions_report_id ON chat_sessions(report_id);
CREATE INDEX idx_chat_sessions_expires_at ON chat_sessions(expires_at);

-- Chat messages table
CREATE TABLE chat_messages (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id UUID REFERENCES chat_sessions(id) ON DELETE CASCADE,
    role VARCHAR(20) NOT NULL CHECK (role IN ('user', 'assistant')),
    content TEXT NOT NULL,
    sources JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_chat_messages_session_id ON chat_messages(session_id);
CREATE INDEX idx_chat_messages_created_at ON chat_messages(created_at);

-- Finance analysis table
CREATE TABLE finance_analysis (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    report_id UUID REFERENCES reports(id) ON DELETE CASCADE,
    working_capital_data JSONB NOT NULL,
    pre_shipment_credit_data JSONB,
    rodtep_benefit_data JSONB,
    gst_refund_data JSONB,
    cash_flow_timeline JSONB,
    financing_options JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_finance_analysis_user_id ON finance_analysis(user_id);
CREATE INDEX idx_finance_analysis_report_id ON finance_analysis(report_id);

-- Logistics analysis table
CREATE TABLE logistics_analysis (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    report_id UUID REFERENCES reports(id) ON DELETE CASCADE,
    lcl_fcl_comparison JSONB,
    rms_probability_data JSONB,
    route_analysis JSONB,
    freight_estimate JSONB,
    insurance_recommendation JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_logistics_analysis_user_id ON logistics_analysis(user_id);
CREATE INDEX idx_logistics_analysis_report_id ON logistics_analysis(report_id);

-- User metrics table
CREATE TABLE user_metrics (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    reports_generated INTEGER DEFAULT 0,
    certifications_completed INTEGER DEFAULT 0,
    documents_generated INTEGER DEFAULT 0,
    exports_completed INTEGER DEFAULT 0,
    cost_savings DECIMAL(12,2) DEFAULT 0,
    timeline_reduction_days INTEGER DEFAULT 0,
    last_export_date TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id)
);

CREATE INDEX idx_user_metrics_user_id ON user_metrics(user_id);

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create triggers for updated_at
CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_reports_updated_at BEFORE UPDATE ON reports
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_cert_progress_updated_at BEFORE UPDATE ON certification_progress
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_gen_docs_updated_at BEFORE UPDATE ON generated_documents
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_action_plan_updated_at BEFORE UPDATE ON action_plan_progress
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_finance_analysis_updated_at BEFORE UPDATE ON finance_analysis
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_logistics_analysis_updated_at BEFORE UPDATE ON logistics_analysis
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_user_metrics_updated_at BEFORE UPDATE ON user_metrics
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
