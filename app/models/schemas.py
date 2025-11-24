from pydantic import BaseModel, Field
from typing import Optional, Any
from datetime import datetime
from enum import Enum


class NotificationStatus(str, Enum):
    PENDING = "pending"
    SENT = "sent"
    DELIVERED = "delivered"
    FAILED = "failed"
    READ = "read"


class NotificationChannel(str, Enum):
    EMAIL = "email"
    SMS = "sms"
    PUSH = "push"
    IN_APP = "in_app"


class NotificationType(str, Enum):
    PROMOTIONAL = "promotional"
    TRANSACTIONAL = "transactional"
    ALERT = "alert"
    REMINDER = "reminder"
    SYSTEM = "system"


# Request/Response Models
class QueryRequest(BaseModel):
    user_input: str = Field(..., description="Natural language query from user")
    execute: bool = Field(default=True, description="Whether to execute the generated query")


class QueryResponse(BaseModel):
    user_input: str
    generated_mql: dict
    explanation: str
    results: Optional[list] = None
    count: Optional[int] = None
    execution_time_ms: Optional[float] = None
    error: Optional[str] = None


class ReportRequest(BaseModel):
    user_input: str = Field(..., description="Natural language description of the report needed")
    report_format: str = Field(default="json", description="Output format: json, csv, pdf")


class ReportResponse(BaseModel):
    report_name: str
    generated_at: datetime
    query_used: dict
    data: Any
    summary: dict
    file_path: Optional[str] = None


class AggregationRequest(BaseModel):
    user_input: str = Field(..., description="Natural language aggregation query")
    execute: bool = Field(default=True, description="Whether to execute the aggregation")


class AggregationResponse(BaseModel):
    user_input: str
    generated_pipeline: list
    explanation: str
    results: Optional[list] = None
    execution_time_ms: Optional[float] = None
    error: Optional[str] = None


# Database Schema Reference (for AI context)
NOTIFICATION_SCHEMA = {
    "collection": "customer_notifications",
    "fields": {
        "_id": "ObjectId - Unique identifier",
        "customer_id": "string - Customer unique identifier",
        "customer_name": "string - Customer full name",
        "customer_email": "string - Customer email address",
        "customer_phone": "string - Customer phone number",
        "notification_type": "string - Type: promotional, transactional, alert, reminder, system",
        "channel": "string - Delivery channel: email, sms, push, in_app",
        "status": "string - Status: pending, sent, delivered, failed, read",
        "subject": "string - Notification subject/title",
        "message": "string - Notification content",
        "priority": "integer - Priority level 1-5 (1=highest)",
        "created_at": "datetime - When notification was created",
        "sent_at": "datetime - When notification was sent",
        "delivered_at": "datetime - When notification was delivered",
        "read_at": "datetime - When notification was read",
        "metadata": {
            "campaign_id": "string - Associated campaign ID",
            "template_id": "string - Template used",
            "tags": "array of strings - Tags for categorization",
            "retry_count": "integer - Number of retry attempts",
            "device_info": "object - Device information for push notifications"
        },
        "error_details": "string - Error message if failed"
    },
    "indexes": [
        "customer_id",
        "status",
        "channel",
        "notification_type",
        "created_at",
        "sent_at"
    ]
}
