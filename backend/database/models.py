"""
SQLAlchemy ORM models for ExportSathi database.
Maps to the PostgreSQL schema defined in schema.sql.
"""
from sqlalchemy import (
    Column, String, Integer, Float, Boolean, Text, TIMESTAMP, 
    ForeignKey, CheckConstraint, Index, DECIMAL
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

Base = declarative_base()


class User(Base):
    """User account and profile information."""
    __tablename__ = 'users'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    business_type = Column(
        String(50), 
        nullable=False,
        index=True
    )
    company_size = Column(String(50), nullable=False)
    company_name = Column(String(255))
    monthly_volume = Column(Integer)
    created_at = Column(TIMESTAMP, server_default=func.current_timestamp())
    updated_at = Column(TIMESTAMP, server_default=func.current_timestamp(), onupdate=func.current_timestamp())
    last_login = Column(TIMESTAMP)
    
    # Relationships
    reports = relationship("Report", back_populates="user", cascade="all, delete-orphan")
    certification_progress = relationship("CertificationProgress", back_populates="user", cascade="all, delete-orphan")
    generated_documents = relationship("GeneratedDocument", back_populates="user", cascade="all, delete-orphan")
    action_plan_progress = relationship("ActionPlanProgress", back_populates="user", cascade="all, delete-orphan")
    chat_sessions = relationship("ChatSession", back_populates="user", cascade="all, delete-orphan")
    finance_analysis = relationship("FinanceAnalysis", back_populates="user", cascade="all, delete-orphan")
    logistics_analysis = relationship("LogisticsAnalysis", back_populates="user", cascade="all, delete-orphan")
    user_metrics = relationship("UserMetrics", back_populates="user", uselist=False, cascade="all, delete-orphan")
    
    __table_args__ = (
        CheckConstraint(
            "business_type IN ('Manufacturing', 'SaaS', 'Merchant')",
            name='check_business_type'
        ),
        CheckConstraint(
            "company_size IN ('Micro', 'Small', 'Medium')",
            name='check_company_size'
        ),
    )


class Report(Base):
    """Export readiness report."""
    __tablename__ = 'reports'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='CASCADE'), index=True)
    product_name = Column(String(255), nullable=False)
    product_image_url = Column(String(500))
    ingredients = Column(Text)
    bom = Column(Text)
    destination_country = Column(String(100), nullable=False, index=True)
    business_type = Column(String(50), nullable=False)
    company_size = Column(String(50), nullable=False)
    monthly_volume = Column(Integer)
    price_range = Column(String(100))
    payment_mode = Column(String(100))
    hs_code = Column(String(20), index=True)
    hs_code_confidence = Column(DECIMAL(5, 2))
    risk_score = Column(Integer)
    estimated_cost = Column(DECIMAL(12, 2))
    estimated_timeline_days = Column(Integer)
    report_data = Column(JSONB, nullable=False)
    status = Column(String(50), default='completed')
    created_at = Column(TIMESTAMP, server_default=func.current_timestamp(), index=True)
    updated_at = Column(TIMESTAMP, server_default=func.current_timestamp(), onupdate=func.current_timestamp())
    
    # Relationships
    user = relationship("User", back_populates="reports")
    certification_progress = relationship("CertificationProgress", back_populates="report", cascade="all, delete-orphan")
    generated_documents = relationship("GeneratedDocument", back_populates="report", cascade="all, delete-orphan")
    action_plan_progress = relationship("ActionPlanProgress", back_populates="report", cascade="all, delete-orphan")
    chat_sessions = relationship("ChatSession", back_populates="report", cascade="all, delete-orphan")
    finance_analysis = relationship("FinanceAnalysis", back_populates="report", cascade="all, delete-orphan")
    logistics_analysis = relationship("LogisticsAnalysis", back_populates="report", cascade="all, delete-orphan")
    
    __table_args__ = (
        CheckConstraint(
            "risk_score >= 0 AND risk_score <= 100",
            name='check_risk_score_range'
        ),
        CheckConstraint(
            "status IN ('processing', 'completed', 'failed')",
            name='check_report_status'
        ),
        Index('idx_reports_created_at', 'created_at', postgresql_using='btree', postgresql_ops={'created_at': 'DESC'}),
    )


class CertificationProgress(Base):
    """Certification progress tracking."""
    __tablename__ = 'certification_progress'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='CASCADE'), index=True)
    report_id = Column(UUID(as_uuid=True), ForeignKey('reports.id', ondelete='CASCADE'), index=True)
    certification_id = Column(String(100), nullable=False)
    certification_name = Column(String(255), nullable=False)
    certification_type = Column(String(50), nullable=False)
    status = Column(String(50), default='not_started', index=True)
    documents_completed = Column(JSONB, default=[])
    notes = Column(Text)
    started_at = Column(TIMESTAMP)
    completed_at = Column(TIMESTAMP)
    created_at = Column(TIMESTAMP, server_default=func.current_timestamp())
    updated_at = Column(TIMESTAMP, server_default=func.current_timestamp(), onupdate=func.current_timestamp())
    
    # Relationships
    user = relationship("User", back_populates="certification_progress")
    report = relationship("Report", back_populates="certification_progress")
    
    __table_args__ = (
        CheckConstraint(
            "status IN ('not_started', 'in_progress', 'completed', 'rejected')",
            name='check_certification_status'
        ),
    )


class GeneratedDocument(Base):
    """Generated export documents."""
    __tablename__ = 'generated_documents'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='CASCADE'), index=True)
    report_id = Column(UUID(as_uuid=True), ForeignKey('reports.id', ondelete='CASCADE'), index=True)
    document_type = Column(String(100), nullable=False, index=True)
    document_data = Column(JSONB, nullable=False)
    pdf_url = Column(String(500))
    editable_url = Column(String(500))
    validation_results = Column(JSONB)
    is_valid = Column(Boolean, default=False)
    created_at = Column(TIMESTAMP, server_default=func.current_timestamp())
    updated_at = Column(TIMESTAMP, server_default=func.current_timestamp(), onupdate=func.current_timestamp())
    
    # Relationships
    user = relationship("User", back_populates="generated_documents")
    report = relationship("Report", back_populates="generated_documents")


class ActionPlanProgress(Base):
    """7-day action plan progress tracking."""
    __tablename__ = 'action_plan_progress'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='CASCADE'), index=True)
    report_id = Column(UUID(as_uuid=True), ForeignKey('reports.id', ondelete='CASCADE'), index=True)
    task_id = Column(String(100), nullable=False)
    day_number = Column(Integer, nullable=False)
    task_title = Column(String(255), nullable=False)
    task_description = Column(Text)
    task_category = Column(String(50))
    completed = Column(Boolean, default=False, index=True)
    completed_at = Column(TIMESTAMP)
    created_at = Column(TIMESTAMP, server_default=func.current_timestamp())
    updated_at = Column(TIMESTAMP, server_default=func.current_timestamp(), onupdate=func.current_timestamp())
    
    # Relationships
    user = relationship("User", back_populates="action_plan_progress")
    report = relationship("Report", back_populates="action_plan_progress")
    
    __table_args__ = (
        CheckConstraint(
            "day_number >= 1 AND day_number <= 7",
            name='check_day_number_range'
        ),
        Index('idx_action_plan_unique', 'report_id', 'task_id', unique=True),
    )


class ChatSession(Base):
    """Chat session for Q&A."""
    __tablename__ = 'chat_sessions'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='CASCADE'), index=True)
    report_id = Column(UUID(as_uuid=True), ForeignKey('reports.id', ondelete='CASCADE'), index=True)
    context_data = Column(JSONB)
    created_at = Column(TIMESTAMP, server_default=func.current_timestamp())
    last_activity = Column(TIMESTAMP, server_default=func.current_timestamp())
    expires_at = Column(TIMESTAMP, index=True)
    
    # Relationships
    user = relationship("User", back_populates="chat_sessions")
    report = relationship("Report", back_populates="chat_sessions")
    messages = relationship("ChatMessage", back_populates="session", cascade="all, delete-orphan")


class ChatMessage(Base):
    """Chat message in a session."""
    __tablename__ = 'chat_messages'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(UUID(as_uuid=True), ForeignKey('chat_sessions.id', ondelete='CASCADE'), index=True)
    role = Column(String(20), nullable=False)
    content = Column(Text, nullable=False)
    sources = Column(JSONB)
    created_at = Column(TIMESTAMP, server_default=func.current_timestamp(), index=True)
    
    # Relationships
    session = relationship("ChatSession", back_populates="messages")
    
    __table_args__ = (
        CheckConstraint(
            "role IN ('user', 'assistant')",
            name='check_message_role'
        ),
    )


class FinanceAnalysis(Base):
    """Finance readiness analysis."""
    __tablename__ = 'finance_analysis'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='CASCADE'), index=True)
    report_id = Column(UUID(as_uuid=True), ForeignKey('reports.id', ondelete='CASCADE'), index=True)
    working_capital_data = Column(JSONB, nullable=False)
    pre_shipment_credit_data = Column(JSONB)
    rodtep_benefit_data = Column(JSONB)
    gst_refund_data = Column(JSONB)
    cash_flow_timeline = Column(JSONB)
    financing_options = Column(JSONB)
    created_at = Column(TIMESTAMP, server_default=func.current_timestamp())
    updated_at = Column(TIMESTAMP, server_default=func.current_timestamp(), onupdate=func.current_timestamp())
    
    # Relationships
    user = relationship("User", back_populates="finance_analysis")
    report = relationship("Report", back_populates="finance_analysis")


class LogisticsAnalysis(Base):
    """Logistics risk analysis."""
    __tablename__ = 'logistics_analysis'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='CASCADE'), index=True)
    report_id = Column(UUID(as_uuid=True), ForeignKey('reports.id', ondelete='CASCADE'), index=True)
    lcl_fcl_comparison = Column(JSONB)
    rms_probability_data = Column(JSONB)
    route_analysis = Column(JSONB)
    freight_estimate = Column(JSONB)
    insurance_recommendation = Column(JSONB)
    created_at = Column(TIMESTAMP, server_default=func.current_timestamp())
    updated_at = Column(TIMESTAMP, server_default=func.current_timestamp(), onupdate=func.current_timestamp())
    
    # Relationships
    user = relationship("User", back_populates="logistics_analysis")
    report = relationship("Report", back_populates="logistics_analysis")


class UserMetrics(Base):
    """User success metrics and analytics."""
    __tablename__ = 'user_metrics'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='CASCADE'), unique=True, index=True)
    reports_generated = Column(Integer, default=0)
    certifications_completed = Column(Integer, default=0)
    documents_generated = Column(Integer, default=0)
    exports_completed = Column(Integer, default=0)
    cost_savings = Column(DECIMAL(12, 2), default=0)
    timeline_reduction_days = Column(Integer, default=0)
    last_export_date = Column(TIMESTAMP)
    created_at = Column(TIMESTAMP, server_default=func.current_timestamp())
    updated_at = Column(TIMESTAMP, server_default=func.current_timestamp(), onupdate=func.current_timestamp())
    
    # Relationships
    user = relationship("User", back_populates="user_metrics")
