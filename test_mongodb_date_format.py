#!/usr/bin/env python3
"""
Test MongoDB date format handling
"""

from datetime import datetime, timedelta, timezone
from app.services.multi_collection_db_service import multi_collection_db_service

def test_date_formats():
    print("Testing MongoDB Date Formats")
    print("=" * 80)

    # Calculate date range
    now = datetime.now(timezone.utc)
    thirty_days_ago = now - timedelta(days=30)

    print(f"Now (UTC): {now}")
    print(f"30 Days Ago (UTC): {thirty_days_ago}")
    print()

    # Test 1: Using Python datetime objects directly
    print("Test 1: Using Python datetime objects")
    query1 = {
        "event_name": "PAYMENT_RECEIVED",
        "created_at": {
            "$gte": thirty_days_ago,
            "$lte": now
        }
    }
    results1 = list(multi_collection_db_service.events.find(query1).limit(5))
    print(f"Results: {len(results1)} found")
    if len(results1) > 0:
        print("✅ Python datetime objects work!")
        for doc in results1[:2]:
            print(f"  - {doc.get('event_tracking_id')}: {doc.get('created_at')}")
    print()

    # Test 2: Using ISODate strings (MongoDB extended JSON)
    print("Test 2: Using ISODate strings with $date")
    query2 = {
        "event_name": "PAYMENT_RECEIVED",
        "created_at": {
            "$gte": {"$date": thirty_days_ago.isoformat()},
            "$lte": {"$date": now.isoformat()}
        }
    }
    try:
        results2 = list(multi_collection_db_service.events.find(query2).limit(5))
        print(f"Results: {len(results2)} found")
        if len(results2) > 0:
            print("✅ $date format works!")
    except Exception as e:
        print(f"❌ $date format failed: {e}")
    print()

    # Test 3: Using ISO format strings directly
    print("Test 3: Using ISO format strings directly")
    query3 = {
        "event_name": "PAYMENT_RECEIVED",
        "created_at": {
            "$gte": thirty_days_ago.isoformat(),
            "$lte": now.isoformat()
        }
    }
    try:
        results3 = list(multi_collection_db_service.events.find(query3).limit(5))
        print(f"Results: {len(results3)} found")
        if len(results3) > 0:
            print("✅ ISO string format works!")
    except Exception as e:
        print(f"❌ ISO string format failed: {e}")

if __name__ == "__main__":
    test_date_formats()
