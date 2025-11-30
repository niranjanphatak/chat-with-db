"""
Seed script for multi-collection notification system.

Creates sample data across:
- notification_events (primary)
- email_notifications
- sms_notifications
- push_notifications
- inapp_notifications
"""

import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from datetime import datetime, timedelta
import random
from app.services.multi_collection_db_service import multi_collection_db_service

# Sample data
CUSTOMERS = [
    {"id": "C001", "name": "John Doe", "email": "john.doe@example.com", "phone": "+1-555-0101"},
    {"id": "C002", "name": "Jane Smith", "email": "jane.smith@example.com", "phone": "+1-555-0102"},
    {"id": "C003", "name": "Bob Johnson", "email": "bob.johnson@example.com", "phone": "+1-555-0103"},
    {"id": "C004", "name": "Alice Williams", "email": "alice.williams@example.com", "phone": "+1-555-0104"},
    {"id": "C005", "name": "Charlie Brown", "email": "charlie.brown@example.com", "phone": "+1-555-0105"},
    {"id": "C006", "name": "Emma Davis", "email": "emma.davis@example.com", "phone": "+1-555-0106"},
    {"id": "C007", "name": "Michael Chen", "email": "michael.chen@example.com", "phone": "+1-555-0107"},
    {"id": "C008", "name": "Sarah Martinez", "email": "sarah.martinez@example.com", "phone": "+1-555-0108"},
    {"id": "C009", "name": "David Lee", "email": "david.lee@example.com", "phone": "+1-555-0109"},
    {"id": "C010", "name": "Lisa Anderson", "email": "lisa.anderson@example.com", "phone": "+1-555-0110"},
    {"id": "C011", "name": "James Wilson", "email": "james.wilson@example.com", "phone": "+1-555-0111"},
    {"id": "C012", "name": "Maria Garcia", "email": "maria.garcia@example.com", "phone": "+1-555-0112"},
    {"id": "C013", "name": "Robert Taylor", "email": "robert.taylor@example.com", "phone": "+1-555-0113"},
    {"id": "C014", "name": "Jennifer White", "email": "jennifer.white@example.com", "phone": "+1-555-0114"},
    {"id": "C015", "name": "Daniel Kim", "email": "daniel.kim@example.com", "phone": "+1-555-0115"},
    {"id": "C016", "name": "Patricia Brown", "email": "patricia.brown@example.com", "phone": "+1-555-0116"},
    {"id": "C017", "name": "Christopher Jones", "email": "christopher.jones@example.com", "phone": "+1-555-0117"},
    {"id": "C018", "name": "Nancy Miller", "email": "nancy.miller@example.com", "phone": "+1-555-0118"},
    {"id": "C019", "name": "Matthew Davis", "email": "matthew.davis@example.com", "phone": "+1-555-0119"},
    {"id": "C020", "name": "Linda Rodriguez", "email": "linda.rodriguez@example.com", "phone": "+1-555-0120"},
]

NOTIFICATION_TYPES = ["promotional", "transactional", "alert", "reminder", "system"]

PRIORITIES = [1, 2, 3, 4, 5]  # 1=critical, 5=lowest

# Event Names for categorization and analytics
EVENT_NAMES = [
    "ORDER_PLACED",
    "ORDER_SHIPPED",
    "ORDER_DELIVERED",
    "PAYMENT_RECEIVED",
    "PAYMENT_FAILED",
    "ACCOUNT_CREATED",
    "PASSWORD_RESET",
    "SUBSCRIPTION_RENEWED",
    "SUBSCRIPTION_CANCELLED",
    "PROMOTIONAL_OFFER",
    "SECURITY_ALERT",
    "REMINDER_DUE_DATE",
    "SYSTEM_MAINTENANCE",
    "FRAUD_ALERT",
    "WELCOME_MESSAGE"
]

CHANNEL_COMBINATIONS = [
    ["email"],
    ["sms"],
    ["push"],
    ["in_app"],
    ["email", "sms"],
    ["email", "push"],
    ["sms", "push"],
    ["email", "sms", "push"],
    ["email", "push", "in_app"],
    ["email", "sms", "push", "in_app"]
]

# Channel status options
EMAIL_STATUSES = ["pending", "processing", "sent", "delivered", "failed", "blacklisted", "bounced", "read"]
SMS_STATUSES = ["pending", "processing", "sent", "delivered", "failed", "blacklisted"]
PUSH_STATUSES = ["pending", "processing", "sent", "delivered", "failed", "blacklisted", "read"]
INAPP_STATUSES = ["pending", "sent", "delivered", "read", "failed"]


def generate_event_tracking_id(index: int) -> str:
    """Generate unique event tracking ID"""
    date_str = datetime.now().strftime("%Y%m%d")
    return f"EVT-{date_str}-{index:06d}"


def random_datetime(days_ago: int = 30) -> datetime:
    """Generate random datetime within last N days"""
    start = datetime.now() - timedelta(days=days_ago)
    random_days = random.randint(0, days_ago)
    random_hours = random.randint(0, 23)
    random_minutes = random.randint(0, 59)
    return start + timedelta(days=random_days, hours=random_hours, minutes=random_minutes)


def seed_notification_event(index: int) -> dict:
    """Create a notification event"""
    customer = random.choice(CUSTOMERS)
    created_at = random_datetime(30)

    channels = random.choice(CHANNEL_COMBINATIONS)
    status = random.choice(["accepted", "processed"])
    event_name = random.choice(EVENT_NAMES)

    event = {
        "event_tracking_id": generate_event_tracking_id(index),
        "event_name": event_name,
        "customer_id": customer["id"],
        "customer_name": customer["name"],
        "customer_email": customer["email"],
        "customer_phone": customer["phone"],
        "notification_type": random.choice(NOTIFICATION_TYPES),
        "priority": random.choice(PRIORITIES),
        "subject": f"{event_name.replace('_', ' ').title()} - Notification #{index}",
        "message": f"This is a {event_name} notification for {customer['name']}",
        "channels": channels,
        "status": status,
        "created_at": created_at,
        "processed_at": created_at + timedelta(seconds=random.randint(1, 300)) if status == "processed" else None,
        "metadata": {
            "campaign_id": f"CAMP-{random.randint(1, 10):03d}",
            "template_id": f"TMPL-{random.randint(1, 5):03d}",
            "tags": random.sample(["promo", "alert", "update", "reminder"], k=random.randint(1, 3)),
            "source": random.choice(["api", "web", "mobile"])
        }
    }

    return event


def seed_email_notification(event: dict) -> dict:
    """Create email notification for an event"""
    sent_at = event["processed_at"] or event["created_at"]
    status = random.choice(EMAIL_STATUSES)

    email = {
        "event_tracking_id": event["event_tracking_id"],
        "recipient_email": event["customer_email"],
        "recipient_name": event["customer_name"],
        "subject": event["subject"],
        "message_body": event["message"],
        "html_body": f"<html><body><h1>{event['subject']}</h1><p>{event['message']}</p></body></html>",
        "status": status,
        "sent_at": sent_at if status != "pending" else None,
        "delivered_at": sent_at + timedelta(minutes=2) if status in ["delivered", "read"] else None,
        "opened_at": sent_at + timedelta(hours=1) if status == "read" else None,
        "clicked_at": sent_at + timedelta(hours=1, minutes=30) if status == "read" and random.random() > 0.5 else None,
        "email_provider": random.choice(["smtp", "sendgrid", "ses", "mailgun"]),
        "message_id": f"MSG-{random.randint(100000, 999999)}",
        "retry_count": random.randint(0, 3) if status == "failed" else 0,
        "error_details": "SMTP connection timeout" if status == "failed" else None,
        "metadata": {
            "attachments": [],
            "cc": [],
            "bcc": []
        }
    }

    return email


def seed_sms_notification(event: dict) -> dict:
    """Create SMS notification for an event"""
    sent_at = event["processed_at"] or event["created_at"]
    status = random.choice(SMS_STATUSES)

    sms = {
        "event_tracking_id": event["event_tracking_id"],
        "recipient_phone": event["customer_phone"],
        "recipient_name": event["customer_name"],
        "message_body": event["message"][:160],  # SMS limit
        "status": status,
        "sent_at": sent_at if status != "pending" else None,
        "delivered_at": sent_at + timedelta(seconds=30) if status == "delivered" else None,
        "sms_provider": random.choice(["twilio", "sns", "nexmo", "plivo"]),
        "message_id": f"SMS-{random.randint(100000, 999999)}",
        "retry_count": random.randint(0, 2) if status == "failed" else 0,
        "error_details": "Number not reachable" if status == "failed" else None,
        "metadata": {
            "country_code": "+1",
            "carrier": random.choice(["AT&T", "Verizon", "T-Mobile", "Sprint"]),
            "message_parts": 1
        }
    }

    return sms


def seed_push_notification(event: dict) -> dict:
    """Create push notification for an event"""
    sent_at = event["processed_at"] or event["created_at"]
    status = random.choice(PUSH_STATUSES)

    push = {
        "event_tracking_id": event["event_tracking_id"],
        "recipient_id": event["customer_id"],
        "device_tokens": [f"token_{random.randint(1000, 9999)}"],
        "title": event["subject"],
        "message_body": event["message"],
        "status": status,
        "sent_at": sent_at if status != "pending" else None,
        "delivered_at": sent_at + timedelta(seconds=10) if status in ["delivered", "read"] else None,
        "received_at": sent_at + timedelta(seconds=15) if status in ["delivered", "read"] else None,
        "clicked_at": sent_at + timedelta(minutes=30) if status == "read" else None,
        "push_provider": random.choice(["fcm", "apns"]),
        "notification_id": f"PUSH-{random.randint(100000, 999999)}",
        "retry_count": random.randint(0, 2) if status == "failed" else 0,
        "error_details": "Device token invalid" if status == "failed" else None,
        "metadata": {
            "action_url": f"https://app.example.com/notification/{event['event_tracking_id']}",
            "image_url": None,
            "badge_count": random.randint(1, 10),
            "sound": "default",
            "platform": random.choice(["android", "ios", "web"])
        }
    }

    return push


def seed_inapp_notification(event: dict) -> dict:
    """Create in-app notification for an event"""
    sent_at = event["processed_at"] or event["created_at"]
    status = random.choice(INAPP_STATUSES)

    inapp = {
        "event_tracking_id": event["event_tracking_id"],
        "recipient_id": event["customer_id"],
        "recipient_name": event["customer_name"],
        "title": event["subject"],
        "message_body": event["message"],
        "status": status,
        "sent_at": sent_at if status != "pending" else None,
        "delivered_at": sent_at + timedelta(seconds=1) if status in ["delivered", "read"] else None,
        "read_at": sent_at + timedelta(hours=2) if status == "read" else None,
        "retry_count": 0,
        "error_details": "User session expired" if status == "failed" else None,
        "metadata": {
            "action_url": f"/notifications/{event['event_tracking_id']}",
            "icon": "notification_icon.png",
            "category": random.choice(["general", "promotion", "alert", "update"]),
            "expires_at": sent_at + timedelta(days=30)
        }
    }

    return inapp


def main():
    """Main seeding function"""
    print("🌱 Seeding multi-collection notification system...")
    print("=" * 60)

    # Clear existing data
    print("\n⚠️  Clearing existing data...")
    multi_collection_db_service.drop_all_collections()
    print("✅ Collections cleared")

    # Recreate indexes
    print("\n📑 Creating indexes...")
    multi_collection_db_service._create_indexes()

    # Generate events
    num_events = 2000
    print(f"\n📧 Generating {num_events} notification events...")

    events_created = 0
    emails_created = 0
    sms_created = 0
    push_created = 0
    inapp_created = 0

    for i in range(1, num_events + 1):
        # Create notification event
        event = seed_notification_event(i)
        multi_collection_db_service.insert_notification_event(event)
        events_created += 1

        # Create channel-specific notifications based on channels list
        if "email" in event["channels"]:
            email = seed_email_notification(event)
            multi_collection_db_service.insert_channel_notification("email_notifications", email)
            emails_created += 1

        if "sms" in event["channels"]:
            sms = seed_sms_notification(event)
            multi_collection_db_service.insert_channel_notification("sms_notifications", sms)
            sms_created += 1

        if "push" in event["channels"]:
            push = seed_push_notification(event)
            multi_collection_db_service.insert_channel_notification("push_notifications", push)
            push_created += 1

        if "in_app" in event["channels"]:
            inapp = seed_inapp_notification(event)
            multi_collection_db_service.insert_channel_notification("inapp_notifications", inapp)
            inapp_created += 1

        if i % 200 == 0:
            print(f"  ✓ Created {i} events...")

    print("\n✅ Data seeding complete!")
    print("=" * 60)
    print(f"📊 Summary:")
    print(f"  - Notification Events: {events_created}")
    print(f"  - Email Notifications: {emails_created}")
    print(f"  - SMS Notifications: {sms_created}")
    print(f"  - Push Notifications: {push_created}")
    print(f"  - In-App Notifications: {inapp_created}")
    print(f"  - Total Channel Notifications: {emails_created + sms_created + push_created + inapp_created}")
    print("=" * 60)

    # Show sample data
    print("\n📝 Sample Event with Channels:")
    sample_event = multi_collection_db_service.events.find_one()
    if sample_event:
        print(f"  Event ID: {sample_event['event_tracking_id']}")
        print(f"  Customer: {sample_event['customer_name']}")
        print(f"  Type: {sample_event['notification_type']}")
        print(f"  Status: {sample_event['status']}")
        print(f"  Channels: {', '.join(sample_event['channels'])}")

        full_event = multi_collection_db_service.get_event_with_channels(sample_event['event_tracking_id'])
        if full_event['email']:
            print(f"    ├─ Email: {full_event['email']['status']}")
        if full_event['sms']:
            print(f"    ├─ SMS: {full_event['sms']['status']}")
        if full_event['push']:
            print(f"    ├─ Push: {full_event['push']['status']}")
        if full_event['inapp']:
            print(f"    └─ In-App: {full_event['inapp']['status']}")

    print("\n✨ Ready to use! Run your application to query this data.")


if __name__ == "__main__":
    main()
