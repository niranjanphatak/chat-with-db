#!/usr/bin/env python3
"""
Test to see what actual dates the AI is generating
"""

from datetime import datetime, timezone
from app.services.multi_collection_ai_service import multi_collection_ai_service

def test_ai_dates():
    print("Testing AI Date Generation")
    print("=" * 80)
    print(f"Current Date (UTC): {datetime.now(timezone.utc).isoformat()}")
    print()

    query = "Show PAYMENT_RECEIVED events for last 1 month"
    print(f"User Query: {query}")
    print()

    try:
        result = multi_collection_ai_service.generate_mql(query)

        print("Generated Query:")
        import json
        print(json.dumps(result, indent=2, default=str))

        # Extract dates from query
        query_obj = result.get('query', {})
        if 'created_at' in query_obj:
            created_at = query_obj['created_at']
            if '$gte' in created_at:
                print(f"\nStart Date in Query: {created_at['$gte']}")
            if '$lte' in created_at:
                print(f"End Date in Query: {created_at['$lte']}")

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_ai_dates()
