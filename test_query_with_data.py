#!/usr/bin/env python3
"""
Test to verify that queries actually return data from the database
"""

from datetime import datetime, timezone
from app.services.multi_collection_ai_service import multi_collection_ai_service
from app.services.multi_collection_db_service import multi_collection_db_service

def test_query_with_data():
    print("Testing Query Execution with Real Data")
    print("=" * 80)

    # First, check if there's any data in the database
    total_events = multi_collection_db_service.events.count_documents({})
    payment_events = multi_collection_db_service.events.count_documents({"event_name": "PAYMENT_RECEIVED"})

    print(f"Total Events in Database: {total_events}")
    print(f"Payment Events in Database: {payment_events}")
    print()

    if total_events == 0:
        print("❌ No data in database. Please run: python scripts/seed_multi_collection_notifications.py")
        return

    # Check date range of data
    oldest = multi_collection_db_service.events.find_one(sort=[("created_at", 1)])
    newest = multi_collection_db_service.events.find_one(sort=[("created_at", -1)])

    if oldest and newest:
        print(f"Data Date Range:")
        print(f"  Oldest Event: {oldest['created_at']}")
        print(f"  Newest Event: {newest['created_at']}")
        print()

    # Test the AI query
    query_text = "Show PAYMENT_RECEIVED events for last 1 month"
    print(f"User Query: {query_text}")
    print()

    try:
        # Generate query
        result = multi_collection_ai_service.generate_mql(query_text)

        query_obj = result.get('query', {})
        print("Generated MongoDB Query:")
        import json
        print(json.dumps(query_obj, indent=2, default=str))
        print()

        # Execute the query
        target_collection = result.get('target_collection', 'notification_events')
        query_type = result.get('query_type', 'find')

        if query_type == 'find':
            results = multi_collection_db_service.execute_find(
                target_collection,
                query_obj,
                limit=10
            )
        else:
            results = multi_collection_db_service.execute_aggregation(
                target_collection,
                query_obj
            )

        print(f"Query Results: {len(results)} documents found")

        if len(results) > 0:
            print("\n✅ SUCCESS! Query returned data!")
            print("\nSample Results (first 3):")
            for i, doc in enumerate(results[:3], 1):
                print(f"\n{i}. Event: {doc.get('event_tracking_id', 'N/A')}")
                print(f"   Event Name: {doc.get('event_name', 'N/A')}")
                print(f"   Created At: {doc.get('created_at', 'N/A')}")
                print(f"   Status: {doc.get('status', 'N/A')}")
                print(f"   Customer: {doc.get('customer_name', 'N/A')}")
        else:
            print("\n⚠️  Query returned no results")
            print("\nDebugging info:")

            # Check if date range is the issue
            if 'created_at' in query_obj:
                date_filter = query_obj['created_at']
                if '$gte' in date_filter:
                    start_date = date_filter['$gte'].get('$date', 'N/A')
                    print(f"Query Start Date: {start_date}")
                if '$lte' in date_filter:
                    end_date = date_filter['$lte'].get('$date', 'N/A')
                    print(f"Query End Date: {end_date}")

            # Try without date filter
            simple_query = {"event_name": "PAYMENT_RECEIVED"}
            simple_results = multi_collection_db_service.execute_find(
                target_collection,
                simple_query,
                limit=5
            )
            print(f"\nPayment events (without date filter): {len(simple_results)} found")

            if len(simple_results) > 0:
                print("Sample dates from payment events:")
                for doc in simple_results[:5]:
                    print(f"  - {doc.get('created_at', 'N/A')}")

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_query_with_data()
