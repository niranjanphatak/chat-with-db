"""
Script to populate MongoDB with sample customer notification data
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pymongo import MongoClient
from datetime import datetime, timedelta
import random
from app.config import settings

# Sample data
CUSTOMERS = [
    {"id": "C001", "name": "John Smith", "email": "john.smith@email.com", "phone": "+1234567890"},
    {"id": "C002", "name": "Jane Doe", "email": "jane.doe@email.com", "phone": "+1234567891"},
    {"id": "C003", "name": "Bob Johnson", "email": "bob.johnson@email.com", "phone": "+1234567892"},
    {"id": "C004", "name": "Alice Brown", "email": "alice.brown@email.com", "phone": "+1234567893"},
    {"id": "C005", "name": "Charlie Wilson", "email": "charlie.wilson@email.com", "phone": "+1234567894"},
    {"id": "C006", "name": "Diana Lee", "email": "diana.lee@email.com", "phone": "+1234567895"},
    {"id": "C007", "name": "Edward Davis", "email": "edward.davis@email.com", "phone": "+1234567896"},
    {"id": "C008", "name": "Fiona Martinez", "email": "fiona.martinez@email.com", "phone": "+1234567897"},
    {"id": "C009", "name": "George Taylor", "email": "george.taylor@email.com", "phone": "+1234567898"},
    {"id": "C010", "name": "Hannah Anderson", "email": "hannah.anderson@email.com", "phone": "+1234567899"},
]

NOTIFICATION_TYPES = ["promotional", "transactional", "alert", "reminder", "system"]
CHANNELS = ["email", "sms", "push", "in_app"]
STATUSES = ["pending", "sent", "delivered", "failed", "read"]

SUBJECTS = {
    "promotional": [
        "Special Offer: 20% Off Your Next Purchase!",
        "Flash Sale Ends Tonight!",
        "New Products Just for You",
        "Exclusive Member Discount",
        "Weekend Special Deals"
    ],
    "transactional": [
        "Order Confirmation #{}",
        "Payment Received - Thank You!",
        "Your Order Has Been Shipped",
        "Delivery Update",
        "Invoice for Your Recent Purchase"
    ],
    "alert": [
        "Security Alert: New Login Detected",
        "Account Activity Notice",
        "Important: Action Required",
        "Unusual Activity Detected",
        "Password Change Confirmation"
    ],
    "reminder": [
        "Don't Forget: Your Appointment Tomorrow",
        "Subscription Renewal Reminder",
        "Items in Your Cart Are Waiting!",
        "Complete Your Profile",
        "Upcoming Payment Due"
    ],
    "system": [
        "System Maintenance Scheduled",
        "Terms of Service Update",
        "New Feature Available",
        "App Update Required",
        "Service Status Update"
    ]
}

CAMPAIGNS = ["CAMP001", "CAMP002", "CAMP003", "CAMP004", "CAMP005"]
TEMPLATES = ["TPL001", "TPL002", "TPL003", "TPL004", "TPL005"]
TAGS = ["marketing", "urgent", "automated", "vip", "retention", "engagement", "onboarding"]

ERROR_MESSAGES = [
    "Email bounced - invalid address",
    "SMS delivery failed - number not reachable",
    "Push notification failed - device not registered",
    "Rate limit exceeded",
    "Invalid recipient",
    "Service temporarily unavailable"
]


def generate_notifications(count: int = 500):
    """Generate sample notification documents"""
    notifications = []
    base_date = datetime.now() - timedelta(days=30)

    for i in range(count):
        customer = random.choice(CUSTOMERS)
        notification_type = random.choice(NOTIFICATION_TYPES)
        channel = random.choice(CHANNELS)
        status = random.choices(
            STATUSES,
            weights=[0.05, 0.10, 0.60, 0.10, 0.15]  # Weighted distribution
        )[0]

        # Generate timestamps
        created_at = base_date + timedelta(
            days=random.randint(0, 30),
            hours=random.randint(0, 23),
            minutes=random.randint(0, 59)
        )

        sent_at = None
        delivered_at = None
        read_at = None
        error_details = None

        if status in ["sent", "delivered", "failed", "read"]:
            sent_at = created_at + timedelta(minutes=random.randint(1, 30))

        if status in ["delivered", "read"]:
            delivered_at = sent_at + timedelta(minutes=random.randint(1, 60))

        if status == "read":
            read_at = delivered_at + timedelta(minutes=random.randint(1, 1440))

        if status == "failed":
            error_details = random.choice(ERROR_MESSAGES)

        # Get subject
        subject = random.choice(SUBJECTS[notification_type])
        if "{}" in subject:
            subject = subject.format(random.randint(10000, 99999))

        notification = {
            "customer_id": customer["id"],
            "customer_name": customer["name"],
            "customer_email": customer["email"],
            "customer_phone": customer["phone"],
            "notification_type": notification_type,
            "channel": channel,
            "status": status,
            "subject": subject,
            "message": f"This is a {notification_type} notification sent via {channel}.",
            "priority": random.randint(1, 5),
            "created_at": created_at,
            "sent_at": sent_at,
            "delivered_at": delivered_at,
            "read_at": read_at,
            "metadata": {
                "campaign_id": random.choice(CAMPAIGNS) if notification_type == "promotional" else None,
                "template_id": random.choice(TEMPLATES),
                "tags": random.sample(TAGS, random.randint(1, 3)),
                "retry_count": random.randint(0, 3) if status == "failed" else 0,
                "device_info": {
                    "platform": random.choice(["iOS", "Android", "Web"]),
                    "app_version": f"1.{random.randint(0, 9)}.{random.randint(0, 9)}"
                } if channel == "push" else None
            },
            "error_details": error_details
        }

        notifications.append(notification)

    return notifications


def main():
    print("Connecting to MongoDB...")
    client = MongoClient(settings.MONGODB_URI)
    db = client[settings.MONGODB_DATABASE]
    collection = db[settings.NOTIFICATIONS_COLLECTION]

    # Clear existing data
    print("Clearing existing data...")
    collection.delete_many({})

    # Generate and insert notifications
    print("Generating sample notifications...")
    notifications = generate_notifications(500)

    print(f"Inserting {len(notifications)} notifications...")
    result = collection.insert_many(notifications)
    print(f"Inserted {len(result.inserted_ids)} documents")

    # Create indexes
    print("Creating indexes...")
    collection.create_index("customer_id")
    collection.create_index("status")
    collection.create_index("channel")
    collection.create_index("notification_type")
    collection.create_index("created_at")
    collection.create_index("sent_at")
    collection.create_index([("status", 1), ("channel", 1)])
    collection.create_index([("customer_id", 1), ("created_at", -1)])

    print("Indexes created successfully")

    # Print summary
    print("\n--- Data Summary ---")
    print(f"Total notifications: {collection.count_documents({})}")

    for status in STATUSES:
        count = collection.count_documents({"status": status})
        print(f"  {status}: {count}")

    print("\nBy channel:")
    for channel in CHANNELS:
        count = collection.count_documents({"channel": channel})
        print(f"  {channel}: {count}")

    print("\nSeed data complete!")
    client.close()


if __name__ == "__main__":
    main()
