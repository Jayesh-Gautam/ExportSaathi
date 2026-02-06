"""
Enums for ExportSathi data models.
"""
from enum import Enum


class BusinessType(str, Enum):
    """Type of business for the exporter."""
    MANUFACTURING = "Manufacturing"
    SAAS = "SaaS"
    MERCHANT = "Merchant"


class CompanySize(str, Enum):
    """Size classification of the company."""
    MICRO = "Micro"
    SMALL = "Small"
    MEDIUM = "Medium"


class CertificationType(str, Enum):
    """Types of certifications required for export."""
    FDA = "FDA"
    CE = "CE"
    REACH = "REACH"
    BIS = "BIS"
    ZED = "ZED"
    SOFTEX = "SOFTEX"
    OTHER = "other"


class RiskSeverity(str, Enum):
    """Severity level for risks."""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class Priority(str, Enum):
    """Priority level for tasks or certifications."""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class DocumentType(str, Enum):
    """Types of export documents."""
    COMMERCIAL_INVOICE = "commercial_invoice"
    PACKING_LIST = "packing_list"
    SHIPPING_BILL = "shipping_bill"
    GST_LUT = "gst_lut"
    SOFTEX = "softex"
    CERTIFICATE_OF_ORIGIN = "certificate_of_origin"


class TaskCategory(str, Enum):
    """Categories for action plan tasks."""
    CERTIFICATION = "certification"
    DOCUMENTATION = "documentation"
    LOGISTICS = "logistics"
    FINANCE = "finance"


class ShippingMode(str, Enum):
    """Shipping container modes."""
    LCL = "LCL"  # Less than Container Load
    FCL = "FCL"  # Full Container Load


class FreightMode(str, Enum):
    """Freight transportation modes."""
    SEA = "sea"
    AIR = "air"


class ReportStatus(str, Enum):
    """Status of report generation."""
    COMPLETED = "completed"
    PROCESSING = "processing"
    FAILED = "failed"


class CertificationStatus(str, Enum):
    """Status of certification progress."""
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"


class MessageRole(str, Enum):
    """Role in chat conversation."""
    USER = "user"
    ASSISTANT = "assistant"


class RejectionSource(str, Enum):
    """Source of past rejection data."""
    FDA = "FDA"
    EU_RASFF = "EU_RASFF"
    OTHER = "other"


class CashFlowEventType(str, Enum):
    """Type of cash flow event."""
    EXPENSE = "expense"
    INCOME = "income"


class ValidationSeverity(str, Enum):
    """Severity of validation issues."""
    ERROR = "error"
    WARNING = "warning"
