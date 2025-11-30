#!/usr/bin/env python3
"""
Test script to verify date-related aggregation queries work properly
for payment notifications in the last month.
"""

import sys
from datetime import datetime, timedelta, timezone
from app.services.multi_collection_ai_service import multi_collection_ai_service

def test_date_queries():
    """Test various date-related query patterns"""

    print("=" * 80)
    print("Testing Date-Related Aggregation Queries for Payment Notifications")
    print("=" * 80)
    print()

    # Calculate expected date range (last 30 days)
    now = datetime.now(timezone.utc)
    thirty_days_ago = now - timedelta(days=30)

    print(f"Current Date: {now.strftime('%Y-%m-%d')}")
    print(f"Expected Date Range: {thirty_days_ago.strftime('%Y-%m-%d')} to {now.strftime('%Y-%m-%d')}")
    print()

    # Test cases
    test_cases = [
        {
            "name": "Test 1: Payment events for last 1 month",
            "query": "Show PAYMENT_RECEIVED events for last 1 month"
        },
        {
            "name": "Test 2: Payment events for last month",
            "query": "Show payment events for last month"
        },
        {
            "name": "Test 3: Count payment notifications by day for last month",
            "query": "Count payment notifications by day for last month"
        },
        {
            "name": "Test 4: Payment events with delivery status for last month",
            "query": "Show payment events with delivery status for last month"
        },
        {
            "name": "Test 5: Group payment notifications by month",
            "query": "Group payment notifications by month"
        }
    ]

    results = []

    for i, test_case in enumerate(test_cases, 1):
        print(f"\n{'-' * 80}")
        print(f"{test_case['name']}")
        print(f"{'-' * 80}")
        print(f"User Query: \"{test_case['query']}\"")
        print()

        try:
            # Generate MQL using AI service
            result = multi_collection_ai_service.generate_mql(test_case['query'])

            # Display results
            print(f"✅ Query generated successfully!")
            print(f"\nQuery Type: {result.get('query_type', 'N/A')}")
            print(f"Target Collection: {result.get('target_collection', 'N/A')}")
            print(f"Involves Multiple Collections: {result.get('involves_multiple_collections', False)}")
            print(f"\nExplanation: {result.get('explanation', 'N/A')}")
            print(f"\nGenerated MongoDB Query:")

            import json
            query = result.get('query', {})
            print(json.dumps(query, indent=2, default=str))

            # Check if date handling is present
            has_date_filter = False
            if isinstance(query, dict):
                # Check for date fields in find query
                if 'created_at' in query or 'sent_at' in query:
                    has_date_filter = True
            elif isinstance(query, list):
                # Check for date fields in aggregation pipeline
                for stage in query:
                    if '$match' in stage:
                        match_stage = stage['$match']
                        if 'created_at' in match_stage or 'sent_at' in match_stage:
                            has_date_filter = True
                            break

            if has_date_filter:
                print("\n✅ Date filtering detected in query")
            else:
                print("\n⚠️  WARNING: No date filtering found in query")

            results.append({
                "test": test_case['name'],
                "status": "✅ PASS" if has_date_filter else "⚠️  PARTIAL",
                "has_date_filter": has_date_filter
            })

        except Exception as e:
            print(f"❌ Error generating query: {e}")
            results.append({
                "test": test_case['name'],
                "status": "❌ FAIL",
                "error": str(e)
            })

    # Summary
    print(f"\n\n{'=' * 80}")
    print("SUMMARY")
    print(f"{'=' * 80}")

    for result in results:
        status_icon = result['status']
        print(f"{status_icon} - {result['test']}")
        if 'error' in result:
            print(f"   Error: {result['error']}")

    print()

    passed = sum(1 for r in results if r['status'] == "✅ PASS")
    total = len(results)

    print(f"Tests Passed: {passed}/{total}")

    if passed == total:
        print("\n🎉 All tests passed! Date aggregation queries are working correctly.")
        return 0
    else:
        print("\n⚠️  Some tests failed or need attention. Please review the output above.")
        return 1


if __name__ == "__main__":
    try:
        exit_code = test_date_queries()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user.")
        sys.exit(130)
    except Exception as e:
        print(f"\n\n❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
