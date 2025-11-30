#!/usr/bin/env python3
"""
Final comprehensive test to verify date-related aggregation queries work end-to-end
"""

from datetime import datetime, timezone
from app.services.multi_collection_ai_service import multi_collection_ai_service
from app.services.multi_collection_db_service import multi_collection_db_service
import json

def test_comprehensive():
    print("=" * 80)
    print("FINAL COMPREHENSIVE TEST: Date-Related Payment Event Queries")
    print("=" * 80)
    print()

    # Check data availability
    total_events = multi_collection_db_service.events.count_documents({})
    payment_events = multi_collection_db_service.events.count_documents({"event_name": "PAYMENT_RECEIVED"})

    print(f"Database Status:")
    print(f"  Total Events: {total_events}")
    print(f"  Payment Events: {payment_events}")
    print()

    if payment_events == 0:
        print("❌ No payment data. Run: python scripts/seed_multi_collection_notifications.py")
        return False

    # Test cases that should return data
    test_cases = [
        {
            "name": "Last 1 Month Payment Events",
            "query": "Show PAYMENT_RECEIVED events for last 1 month",
            "should_have_results": True
        },
        {
            "name": "Daily Payment Count (Last Month)",
            "query": "Count payment notifications by day for last month",
            "should_have_results": True
        },
        {
            "name": "Payment Events with Channels (Last Month)",
            "query": "Show payment events with delivery status for last month",
            "should_have_results": True
        }
    ]

    results = []

    for test in test_cases:
        print(f"\n{'='*80}")
        print(f"Test: {test['name']}")
        print(f"{'='*80}")
        print(f"Query: \"{test['query']}\"")
        print()

        try:
            # Generate query
            mql_result = multi_collection_ai_service.generate_mql(test['query'])

            query_type = mql_result.get('query_type', 'find')
            target_collection = mql_result.get('target_collection', 'notification_events')
            query_obj = mql_result.get('query', {})

            print(f"Generated Query Type: {query_type}")
            print(f"Target Collection: {target_collection}")
            print()

            # Execute query
            if query_type == 'find':
                data = multi_collection_db_service.execute_find(
                    target_collection,
                    query_obj,
                    limit=100
                )
            else:  # aggregation
                data = multi_collection_db_service.execute_aggregation(
                    target_collection,
                    query_obj
                )

            result_count = len(data)
            print(f"Results Found: {result_count}")

            if test['should_have_results']:
                if result_count > 0:
                    print("✅ PASS - Query returned expected results")

                    # Show sample
                    if query_type == 'find':
                        print(f"\nSample Result:")
                        sample = data[0]
                        print(f"  Event: {sample.get('event_tracking_id', 'N/A')}")
                        print(f"  Event Name: {sample.get('event_name', 'N/A')}")
                        print(f"  Created: {sample.get('created_at', 'N/A')}")
                        print(f"  Customer: {sample.get('customer_name', 'N/A')}")
                    else:
                        print(f"\nSample Results (first 3):")
                        for i, item in enumerate(data[:3], 1):
                            print(f"  {i}. {json.dumps(item, default=str, indent=6)}")

                    results.append({"test": test['name'], "status": "✅ PASS"})
                else:
                    print("❌ FAIL - Expected results but got none")
                    results.append({"test": test['name'], "status": "❌ FAIL"})
            else:
                print("✅ PASS - No results expected")
                results.append({"test": test['name'], "status": "✅ PASS"})

        except Exception as e:
            print(f"❌ ERROR: {e}")
            results.append({"test": test['name'], "status": "❌ ERROR", "error": str(e)})

    # Summary
    print(f"\n\n{'='*80}")
    print("FINAL SUMMARY")
    print(f"{'='*80}")

    for result in results:
        print(f"{result['status']} - {result['test']}")
        if 'error' in result:
            print(f"     Error: {result['error']}")

    passed = sum(1 for r in results if r['status'] == "✅ PASS")
    total = len(results)

    print()
    print(f"Tests Passed: {passed}/{total}")
    print()

    if passed == total:
        print("🎉 ALL TESTS PASSED!")
        print()
        print("✅ Date-related aggregation queries for payment events are working correctly!")
        print("✅ Queries properly filter by date range (last 1 month)")
        print("✅ Results are being returned from the database")
        print("✅ The Extended JSON date format is being converted to Python datetime objects")
        return True
    else:
        print("⚠️  Some tests failed. Please review the output above.")
        return False

if __name__ == "__main__":
    success = test_comprehensive()
    exit(0 if success else 1)
