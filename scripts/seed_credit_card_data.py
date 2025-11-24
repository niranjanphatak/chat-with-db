"""
Seed script for credit card transaction data
Generates realistic sample transactions for testing
"""

from datetime import datetime, timedelta
import random
from pymongo import MongoClient
import sys
import os

# Add parent directory to path to import app modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.config import settings


# Sample data
MERCHANTS = {
    "groceries": ["Whole Foods", "Trader Joe's", "Safeway", "Walmart", "Target", "Costco"],
    "dining": ["Chipotle", "Starbucks", "McDonald's", "Olive Garden", "Panera Bread", "In-N-Out"],
    "shopping": ["Amazon.com", "Target", "Best Buy", "Nordstrom", "Macy's", "Apple Store"],
    "travel": ["United Airlines", "Delta", "Marriott", "Hilton", "Airbnb", "Enterprise Rent-A-Car"],
    "entertainment": ["Netflix", "Spotify", "AMC Theatres", "Disney+", "Hulu", "PlayStation Store"],
    "utilities": ["PG&E", "Comcast", "AT&T", "Verizon", "Water District", "City Electric"],
    "gas": ["Shell", "Chevron", "76", "Arco", "Mobile", "BP"],
    "healthcare": ["CVS Pharmacy", "Walgreens", "Kaiser Permanente", "LabCorp", "Optum"],
    "education": ["Coursera", "Udemy", "Khan Academy Premium", "LinkedIn Learning", "Skillshare"],
    "other": ["Home Depot", "Lowe's", "Office Depot", "Petco", "Dollar Tree"]
}

CARD_NUMBERS = ["****1234", "****5678", "****9012"]
CARDHOLDERS = ["John Doe", "Jane Smith", "Robert Johnson"]

TRANSACTION_AMOUNTS = {
    "groceries": (20, 150),
    "dining": (10, 80),
    "shopping": (30, 500),
    "travel": (100, 1500),
    "entertainment": (10, 60),
    "utilities": (50, 250),
    "gas": (30, 80),
    "healthcare": (20, 300),
    "education": (20, 100),
    "other": (15, 200)
}

LOCATIONS = [
    {"city": "San Francisco", "state": "CA", "country": "USA"},
    {"city": "New York", "state": "NY", "country": "USA"},
    {"city": "Los Angeles", "state": "CA", "country": "USA"},
    {"city": "Chicago", "state": "IL", "country": "USA"},
    {"city": "Seattle", "state": "WA", "country": "USA"},
]


def generate_transaction_id(index: int) -> str:
    """Generate a unique transaction ID"""
    return f"TXN{str(index).zfill(6)}"


def generate_transaction(index: int, base_date: datetime) -> dict:
    """Generate a single realistic transaction"""
    # Select category and merchant
    category = random.choice(list(MERCHANTS.keys()))
    merchant = random.choice(MERCHANTS[category])

    # Generate amount based on category
    min_amt, max_amt = TRANSACTION_AMOUNTS[category]
    amount = round(random.uniform(min_amt, max_amt), 2)

    # Generate dates
    days_ago = random.randint(0, 90)  # Last 90 days
    transaction_date = base_date - timedelta(days=days_ago, hours=random.randint(0, 23))
    post_date = transaction_date + timedelta(days=random.randint(1, 3))

    # Determine transaction type (most are purchases)
    transaction_type = random.choices(
        ["purchase", "refund", "payment", "fee", "interest", "cashback"],
        weights=[85, 5, 3, 3, 2, 2]
    )[0]

    # Adjust amount for refunds and payments
    if transaction_type in ["refund", "payment", "cashback"]:
        amount = -abs(amount)

    # Determine status (most are posted)
    status = random.choices(
        ["posted", "pending", "declined", "reversed"],
        weights=[85, 10, 3, 2]
    )[0]

    # Select cardholder and card
    cardholder_idx = random.randint(0, len(CARDHOLDERS) - 1)
    cardholder = CARDHOLDERS[cardholder_idx]
    card_number = CARD_NUMBERS[cardholder_idx]

    # Generate rewards (1% for most categories, 2% for dining, 3% for travel)
    rewards_rate = 0.01
    if category == "dining":
        rewards_rate = 0.02
    elif category == "travel":
        rewards_rate = 0.03

    rewards_earned = round(abs(amount) * rewards_rate, 2) if status == "posted" and transaction_type == "purchase" else 0

    # Location
    location = random.choice(LOCATIONS)
    is_international = random.random() < 0.05  # 5% international

    if is_international:
        location = {"city": "London", "state": "", "country": "UK"}

    transaction = {
        "transaction_id": generate_transaction_id(index),
        "card_number": card_number,
        "cardholder_name": cardholder,
        "transaction_date": transaction_date,
        "post_date": post_date,
        "merchant_name": merchant,
        "category": category,
        "amount": amount,
        "currency": "USD",
        "transaction_type": transaction_type,
        "status": status,
        "description": f"{transaction_type.title()} at {merchant} - {category.title()}",
        "location": location,
        "is_international": is_international,
        "rewards_earned": rewards_earned
    }

    return transaction


def seed_database(num_transactions: int = 500):
    """Seed the database with sample credit card transactions"""
    try:
        # Connect to MongoDB
        client = MongoClient(settings.MONGODB_URI)
        db = client[settings.MONGODB_DATABASE]
        collection = db["credit_card_transactions"]

        # Clear existing data
        print(f"Clearing existing transactions...")
        collection.delete_many({})

        # Generate transactions
        print(f"Generating {num_transactions} sample transactions...")
        base_date = datetime.now()
        transactions = [generate_transaction(i + 1, base_date) for i in range(num_transactions)]

        # Insert into database
        print("Inserting transactions into database...")
        result = collection.insert_many(transactions)

        print(f"✅ Successfully inserted {len(result.inserted_ids)} transactions!")

        # Print some statistics
        stats = collection.aggregate([
            {"$group": {
                "_id": "$category",
                "count": {"$sum": 1},
                "total": {"$sum": "$amount"}
            }},
            {"$sort": {"total": -1}}
        ])

        print("\n📊 Transaction Statistics:")
        print("-" * 60)
        for stat in stats:
            print(f"{stat['_id']:15} | Count: {stat['count']:4} | Total: ${stat['total']:,.2f}")

        total_spending = collection.aggregate([
            {"$match": {"status": "posted", "amount": {"$gt": 0}}},
            {"$group": {"_id": None, "total": {"$sum": "$amount"}}}
        ])

        total = list(total_spending)
        if total:
            print("-" * 60)
            print(f"{'Total Spending':15} | ${total[0]['total']:,.2f}")

        print("\n✨ Database seeded successfully!")

        # Close connection
        client.close()

    except Exception as e:
        print(f"❌ Error seeding database: {e}")
        sys.exit(1)


if __name__ == "__main__":
    print("🚀 Credit Card Transaction Data Seeder")
    print("=" * 60)

    # Allow custom number of transactions
    num_transactions = 500
    if len(sys.argv) > 1:
        try:
            num_transactions = int(sys.argv[1])
        except ValueError:
            print("Invalid number of transactions. Using default (500).")

    seed_database(num_transactions)
