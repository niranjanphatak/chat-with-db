from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


# ============================================================================
# PRIMARY COLLECTION: notification_events
# ============================================================================

class EventStatus(str, Enum):
    """Status for notification events in primary collection"""
    ACCEPTED = "accepted"  # Event received and validated
    PROCESSED = "processed"  # Event processed and sent to channels


class NotificationType(str, Enum):
    PROMOTIONAL = "promotional"
    TRANSACTIONAL = "transactional"
    ALERT = "alert"
    REMINDER = "reminder"
    SYSTEM = "system"


class NotificationPriority(int, Enum):
    CRITICAL = 1  # Highest priority
    HIGH = 2
    MEDIUM = 3
    LOW = 4
    LOWEST = 5


class NotificationEvent(BaseModel):
    """Primary collection: notification_events"""
    event_tracking_id: str = Field(..., description="Unique tracking ID across all collections")
    event_name: str = Field(..., description="Event name for categorization and analytics (e.g., ORDER_PLACED, PAYMENT_RECEIVED, ACCOUNT_CREATED)")
    customer_id: str
    customer_name: str
    customer_email: Optional[str] = None
    customer_phone: Optional[str] = None

    notification_type: NotificationType
    priority: NotificationPriority = NotificationPriority.MEDIUM

    subject: str
    message: str

    # Channels to send notification through
    channels: List[str] = Field(..., description="List of channels: email, sms, push, in_app")

    status: EventStatus = EventStatus.ACCEPTED

    created_at: datetime
    processed_at: Optional[datetime] = None

    metadata: Optional[Dict[str, Any]] = {
        "campaign_id": None,
        "template_id": None,
        "tags": [],
        "source": "api"
    }


# ============================================================================
# SECONDARY COLLECTIONS: Channel-specific collections
# ============================================================================

class ChannelStatus(str, Enum):
    """Common status for all channel collections"""
    PENDING = "pending"  # Queued for sending
    PROCESSING = "processing"  # Currently being sent
    SENT = "sent"  # Successfully sent to provider
    DELIVERED = "delivered"  # Confirmed delivery
    FAILED = "failed"  # Failed to send
    BLACKLISTED = "blacklisted"  # Recipient is blacklisted
    BOUNCED = "bounced"  # Email bounced back
    UNSUBSCRIBED = "unsubscribed"  # Recipient unsubscribed
    READ = "read"  # Message was read/opened


# Email Notifications Collection
class EmailNotification(BaseModel):
    """Collection: email_notifications"""
    event_tracking_id: str  # Links to notification_events

    recipient_email: str
    recipient_name: str

    subject: str
    message_body: str
    html_body: Optional[str] = None

    status: ChannelStatus = ChannelStatus.PENDING

    sent_at: Optional[datetime] = None
    delivered_at: Optional[datetime] = None
    opened_at: Optional[datetime] = None
    clicked_at: Optional[datetime] = None

    email_provider: str = "smtp"  # smtp, sendgrid, ses, etc.
    message_id: Optional[str] = None  # Provider's message ID

    retry_count: int = 0
    error_details: Optional[str] = None

    metadata: Optional[Dict[str, Any]] = {
        "attachments": [],
        "cc": [],
        "bcc": []
    }


# SMS Notifications Collection
class SmsNotification(BaseModel):
    """Collection: sms_notifications"""
    event_tracking_id: str  # Links to notification_events

    recipient_phone: str
    recipient_name: str

    message_body: str

    status: ChannelStatus = ChannelStatus.PENDING

    sent_at: Optional[datetime] = None
    delivered_at: Optional[datetime] = None

    sms_provider: str = "twilio"  # twilio, sns, nexmo, etc.
    message_id: Optional[str] = None

    retry_count: int = 0
    error_details: Optional[str] = None

    metadata: Optional[Dict[str, Any]] = {
        "country_code": "+1",
        "carrier": None,
        "message_parts": 1
    }


# Push Notifications Collection
class PushNotification(BaseModel):
    """Collection: push_notifications"""
    event_tracking_id: str  # Links to notification_events

    recipient_id: str
    device_tokens: List[str]

    title: str
    message_body: str

    status: ChannelStatus = ChannelStatus.PENDING

    sent_at: Optional[datetime] = None
    delivered_at: Optional[datetime] = None
    received_at: Optional[datetime] = None
    clicked_at: Optional[datetime] = None

    push_provider: str = "fcm"  # fcm, apns, etc.
    notification_id: Optional[str] = None

    retry_count: int = 0
    error_details: Optional[str] = None

    metadata: Optional[Dict[str, Any]] = {
        "action_url": None,
        "image_url": None,
        "badge_count": 0,
        "sound": "default",
        "platform": "android"  # android, ios, web
    }


# In-App Notifications Collection
class InAppNotification(BaseModel):
    """Collection: inapp_notifications"""
    event_tracking_id: str  # Links to notification_events

    recipient_id: str
    recipient_name: str

    title: str
    message_body: str

    status: ChannelStatus = ChannelStatus.PENDING

    sent_at: Optional[datetime] = None
    delivered_at: Optional[datetime] = None
    read_at: Optional[datetime] = None

    retry_count: int = 0
    error_details: Optional[str] = None

    metadata: Optional[Dict[str, Any]] = {
        "action_url": None,
        "icon": None,
        "category": "general",
        "expires_at": None
    }


# ============================================================================
# COMPLETE SCHEMA DEFINITION FOR AI
# ============================================================================

MULTI_COLLECTION_NOTIFICATION_SCHEMA = {
    "description": "Multi-collection notification system with primary events and channel-specific collections",

    "collections": {
        "notification_events": {
            "description": "Primary collection tracking all notification events",
            "fields": {
                "event_tracking_id": {
                    "type": "string",
                    "description": "Unique tracking ID linking all collections",
                    "example": "EVT-20241128-001234",
                    "indexed": True
                },
                "event_name": {
                    "type": "string",
                    "description": "Event name for categorization and analytics",
                    "example": "ORDER_PLACED, PAYMENT_RECEIVED, ACCOUNT_CREATED, ORDER_SHIPPED, PASSWORD_RESET, SUBSCRIPTION_RENEWED",
                    "indexed": True
                },
                "customer_id": {"type": "string", "indexed": True},
                "customer_name": {"type": "string"},
                "customer_email": {"type": "string"},
                "customer_phone": {"type": "string"},
                "notification_type": {
                    "type": "string",
                    "enum": ["promotional", "transactional", "alert", "reminder", "system"]
                },
                "priority": {
                    "type": "integer",
                    "description": "1=critical, 2=high, 3=medium, 4=low, 5=lowest"
                },
                "subject": {"type": "string"},
                "message": {"type": "string"},
                "channels": {
                    "type": "array",
                    "description": "Channels to send through",
                    "items": {"type": "string", "enum": ["email", "sms", "push", "in_app"]}
                },
                "status": {
                    "type": "string",
                    "enum": ["accepted", "processed"],
                    "description": "Event processing status"
                },
                "created_at": {"type": "datetime", "indexed": True},
                "processed_at": {"type": "datetime"},
                "metadata": {"type": "object"}
            }
        },

        "email_notifications": {
            "description": "Email channel notifications",
            "fields": {
                "event_tracking_id": {
                    "type": "string",
                    "description": "Links to notification_events",
                    "indexed": True
                },
                "recipient_email": {"type": "string", "indexed": True},
                "recipient_name": {"type": "string"},
                "subject": {"type": "string"},
                "message_body": {"type": "string"},
                "html_body": {"type": "string"},
                "status": {
                    "type": "string",
                    "enum": ["pending", "processing", "sent", "delivered", "failed",
                            "blacklisted", "bounced", "unsubscribed", "read"],
                    "indexed": True
                },
                "sent_at": {"type": "datetime"},
                "delivered_at": {"type": "datetime"},
                "opened_at": {"type": "datetime"},
                "clicked_at": {"type": "datetime"},
                "email_provider": {"type": "string"},
                "message_id": {"type": "string"},
                "retry_count": {"type": "integer"},
                "error_details": {"type": "string"}
            }
        },

        "sms_notifications": {
            "description": "SMS channel notifications",
            "fields": {
                "event_tracking_id": {"type": "string", "indexed": True},
                "recipient_phone": {"type": "string", "indexed": True},
                "recipient_name": {"type": "string"},
                "message_body": {"type": "string"},
                "status": {
                    "type": "string",
                    "enum": ["pending", "processing", "sent", "delivered", "failed", "blacklisted"],
                    "indexed": True
                },
                "sent_at": {"type": "datetime"},
                "delivered_at": {"type": "datetime"},
                "sms_provider": {"type": "string"},
                "message_id": {"type": "string"},
                "retry_count": {"type": "integer"},
                "error_details": {"type": "string"}
            }
        },

        "push_notifications": {
            "description": "Push notification channel",
            "fields": {
                "event_tracking_id": {"type": "string", "indexed": True},
                "recipient_id": {"type": "string", "indexed": True},
                "device_tokens": {"type": "array"},
                "title": {"type": "string"},
                "message_body": {"type": "string"},
                "status": {
                    "type": "string",
                    "enum": ["pending", "processing", "sent", "delivered", "failed", "blacklisted", "read"],
                    "indexed": True
                },
                "sent_at": {"type": "datetime"},
                "delivered_at": {"type": "datetime"},
                "received_at": {"type": "datetime"},
                "clicked_at": {"type": "datetime"},
                "push_provider": {"type": "string"},
                "notification_id": {"type": "string"},
                "retry_count": {"type": "integer"},
                "error_details": {"type": "string"}
            }
        },

        "inapp_notifications": {
            "description": "In-app notification channel",
            "fields": {
                "event_tracking_id": {"type": "string", "indexed": True},
                "recipient_id": {"type": "string", "indexed": True},
                "recipient_name": {"type": "string"},
                "title": {"type": "string"},
                "message_body": {"type": "string"},
                "status": {
                    "type": "string",
                    "enum": ["pending", "sent", "delivered", "read", "failed"],
                    "indexed": True
                },
                "sent_at": {"type": "datetime"},
                "delivered_at": {"type": "datetime"},
                "read_at": {"type": "datetime"},
                "retry_count": {"type": "integer"},
                "error_details": {"type": "string"}
            }
        }
    },

    "relationships": {
        "description": "Collections are linked via event_tracking_id",
        "example_queries": [
            "Get all channels for event: db.email_notifications.find({event_tracking_id: 'EVT-001'})",
            "Get event status: db.notification_events.findOne({event_tracking_id: 'EVT-001'})"
        ]
    }
}
