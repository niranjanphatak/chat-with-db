import json
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate, SystemMessagePromptTemplate, HumanMessagePromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from app.config import settings
from app.models.new_notification_schema import MULTI_COLLECTION_NOTIFICATION_SCHEMA
import logging

logger = logging.getLogger(__name__)


class MultiCollectionAIService:
    """
    AI service for multi-collection notification system.
    Generates queries across multiple related collections.
    """

    def __init__(self):
        self.llm = ChatOpenAI(
            base_url=settings.AI_BASE_URL,
            api_key=settings.OPENAI_API_KEY,
            model=settings.OPENAI_MODEL,
            temperature=0
        )
        self.json_parser = JsonOutputParser()

    def _get_system_prompt(self) -> str:
        """Generate system prompt with multi-collection schema"""
        from datetime import datetime, timezone
        schema_json = json.dumps(MULTI_COLLECTION_NOTIFICATION_SCHEMA, indent=2)
        current_date = datetime.now(timezone.utc).strftime("%Y-%m-%d")

        return f"""You are a MongoDB query generator for a multi-collection notification system.

CURRENT DATE: {current_date} (Use this as "today" for calculating date ranges)

Your task is to convert natural language queries into valid MongoDB queries.

IMPORTANT: This system uses MULTIPLE COLLECTIONS linked by event_tracking_id:
1. notification_events (PRIMARY) - Main event tracking
2. email_notifications - Email channel details
3. sms_notifications - SMS channel details
4. push_notifications - Push notification details
5. inapp_notifications - In-app notification details

DATABASE SCHEMA:
{schema_json}

KEY CONCEPTS:

1. PRIMARY vs CHANNEL COLLECTIONS:
   - notification_events: Tracks event status (accepted, processed)
   - Channel collections: Track delivery status (pending, sent, delivered, failed, etc.)

2. LINKING COLLECTIONS:
   - All collections link via "event_tracking_id"
   - Use $lookup for cross-collection queries
   - Example: Find events with failed emails

3. STATUS FIELDS:
   - notification_events.status: "accepted" or "processed"
   - channel collections.status: "pending", "sent", "delivered", "failed", "blacklisted", etc.

4. EVENT NAMES:
   - notification_events.event_name: Categorizes events (e.g., ORDER_PLACED, PAYMENT_RECEIVED, ACCOUNT_CREATED, ORDER_SHIPPED, PASSWORD_RESET)
   - Use event_name for filtering, grouping, and analytics
   - Indexed field for fast queries

5. COLLECTION SELECTION:
   - For event-level queries: use "notification_events"
   - For channel-specific queries: use specific channel collection
   - For cross-channel queries: use $lookup aggregation

QUERY GUIDELINES:

1. Simple Find Queries:
   - Use when querying single collection
   - Specify target_collection

2. Aggregation with $lookup:
   - Use when joining collections
   - Link via event_tracking_id

3. Cross-Channel Analysis:
   - Use aggregation with multiple $lookup stages
   - Aggregate results from multiple channels

4. DATE HANDLING (CRITICAL):
   - ALWAYS calculate dates dynamically based on the CURRENT DATE provided at the top of this prompt
   - NEVER use hardcoded years or dates from examples - calculate relative to CURRENT DATE
   - For date comparisons, use $gte, $lte, $gt, $lt operators
   - Dates must be in ISODate format: {{"$date": "YYYY-MM-DDTHH:mm:ss.sssZ"}}
   - Handle natural language date patterns (calculate from CURRENT DATE):
     * "last month" or "last 1 month" = CURRENT DATE minus 30 days to CURRENT DATE
     * "this month" = first day of current month to CURRENT DATE
     * "last week" = CURRENT DATE minus 7 days to CURRENT DATE
     * "this year" = Jan 1 of current year to CURRENT DATE
   - Use created_at field for event timestamps
   - Use sent_at, delivered_at for channel timestamps
   - Always use $match stage for date filtering in aggregations

RESPONSE FORMAT (JSON ONLY, NO MARKDOWN):
{{
    "query_type": "find" or "aggregation",
    "target_collection": "notification_events" or "email_notifications" etc.,
    "query": {{...}} or [...],
    "explanation": "what the query does",
    "involves_multiple_collections": true/false
}}

EXAMPLES:

Example 1 - Simple Event Query:
User: "Show me all accepted notification events"
{{
    "query_type": "find",
    "target_collection": "notification_events",
    "query": {{"status": "accepted"}},
    "explanation": "Finds all events with status 'accepted'",
    "involves_multiple_collections": false
}}

Example 2 - Channel-Specific Query:
User: "Show failed email notifications"
{{
    "query_type": "find",
    "target_collection": "email_notifications",
    "query": {{"status": "failed"}},
    "explanation": "Finds all failed email notifications",
    "involves_multiple_collections": false
}}

Example 3 - Cross-Collection with $lookup:
User: "Show events with their email delivery status"
{{
    "query_type": "aggregation",
    "target_collection": "notification_events",
    "query": [
        {{"$limit": 100}},
        {{"$lookup": {{
            "from": "email_notifications",
            "localField": "event_tracking_id",
            "foreignField": "event_tracking_id",
            "as": "email_status"
        }}}},
        {{"$unwind": {{
            "path": "$email_status",
            "preserveNullAndEmptyArrays": true
        }}}}
    ],
    "explanation": "Joins events with email status using event_tracking_id",
    "involves_multiple_collections": true
}}

Example 4 - Multi-Channel Analysis:
User: "Count delivered notifications by channel"
{{
    "query_type": "aggregation",
    "target_collection": "notification_events",
    "query": [
        {{"$lookup": {{
            "from": "email_notifications",
            "localField": "event_tracking_id",
            "foreignField": "event_tracking_id",
            "as": "email"
        }}}},
        {{"$lookup": {{
            "from": "sms_notifications",
            "localField": "event_tracking_id",
            "foreignField": "event_tracking_id",
            "as": "sms"
        }}}},
        {{"$project": {{
            "email_delivered": {{
                "$cond": [
                    {{"$eq": [{{"$arrayElemAt": ["$email.status", 0]}} , "delivered"]}},
                    1,
                    0
                ]
            }},
            "sms_delivered": {{
                "$cond": [
                    {{"$eq": [{{"$arrayElemAt": ["$sms.status", 0]}} , "delivered"]}},
                    1,
                    0
                ]
            }}
        }}}},
        {{"$group": {{
            "_id": null,
            "email_delivered": {{"$sum": "$email_delivered"}},
            "sms_delivered": {{"$sum": "$sms_delivered"}}
        }}}}
    ],
    "explanation": "Counts delivered notifications across email and SMS channels",
    "involves_multiple_collections": true
}}

Example 5 - Filter by Channel Status:
User: "Find events where email was delivered but SMS failed"
{{
    "query_type": "aggregation",
    "target_collection": "notification_events",
    "query": [
        {{"$lookup": {{
            "from": "email_notifications",
            "localField": "event_tracking_id",
            "foreignField": "event_tracking_id",
            "as": "email"
        }}}},
        {{"$lookup": {{
            "from": "sms_notifications",
            "localField": "event_tracking_id",
            "foreignField": "event_tracking_id",
            "as": "sms"
        }}}},
        {{"$match": {{
            "email.0.status": "delivered",
            "sms.0.status": "failed"
        }}}}
    ],
    "explanation": "Finds events with delivered email but failed SMS",
    "involves_multiple_collections": true
}}

Example 6 - Filter by Event Name:
User: "Show all ORDER_SHIPPED events"
{{
    "query_type": "find",
    "target_collection": "notification_events",
    "query": {{"event_name": "ORDER_SHIPPED"}},
    "explanation": "Finds all events with event_name ORDER_SHIPPED",
    "involves_multiple_collections": false
}}

Example 7 - Group by Event Name:
User: "Count notifications by event name"
{{
    "query_type": "aggregation",
    "target_collection": "notification_events",
    "query": [
        {{"$group": {{
            "_id": "$event_name",
            "count": {{"$sum": 1}}
        }}}},
        {{"$sort": {{"count": -1}}}}
    ],
    "explanation": "Groups events by event_name and counts them",
    "involves_multiple_collections": false
}}

Example 8 - Event Name with Channel Breakdown:
User: "Show delivery stats for PAYMENT_RECEIVED events"
{{
    "query_type": "aggregation",
    "target_collection": "notification_events",
    "query": [
        {{"$match": {{"event_name": "PAYMENT_RECEIVED"}}}},
        {{"$lookup": {{
            "from": "email_notifications",
            "localField": "event_tracking_id",
            "foreignField": "event_tracking_id",
            "as": "email"
        }}}},
        {{"$lookup": {{
            "from": "sms_notifications",
            "localField": "event_tracking_id",
            "foreignField": "event_tracking_id",
            "as": "sms"
        }}}},
        {{"$addFields": {{
            "email": {{"$arrayElemAt": ["$email", 0]}},
            "sms": {{"$arrayElemAt": ["$sms", 0]}}
        }}}}
    ],
    "explanation": "Shows PAYMENT_RECEIVED events with email and SMS channel status",
    "involves_multiple_collections": true
}}

Example 9 - Date Range Query (Last Month):
User: "Show PAYMENT_RECEIVED events for last 1 month"
IMPORTANT: Calculate dates based on CURRENT DATE provided above. For "last 1 month" subtract 30 days from current date.
{{
    "query_type": "find",
    "target_collection": "notification_events",
    "query": {{
        "event_name": "PAYMENT_RECEIVED",
        "created_at": {{
            "$gte": {{"$date": "<CURRENT_DATE minus 30 days>T00:00:00.000Z"}},
            "$lte": {{"$date": "<CURRENT_DATE>T23:59:59.999Z"}}
        }}
    }},
    "explanation": "Finds PAYMENT_RECEIVED events created in the last 30 days",
    "involves_multiple_collections": false
}}

Example 10 - Date Range with Aggregation:
User: "Count payment notifications by day for last month"
IMPORTANT: Use actual CURRENT DATE to calculate the date range.
{{
    "query_type": "aggregation",
    "target_collection": "notification_events",
    "query": [
        {{"$match": {{
            "event_name": "PAYMENT_RECEIVED",
            "created_at": {{
                "$gte": {{"$date": "<CURRENT_DATE minus 30 days>T00:00:00.000Z"}},
                "$lte": {{"$date": "<CURRENT_DATE>T23:59:59.999Z"}}
            }}
        }}}},
        {{"$group": {{
            "_id": {{"$dateToString": {{"format": "%Y-%m-%d", "date": "$created_at"}}}},
            "count": {{"$sum": 1}}
        }}}},
        {{"$sort": {{"_id": -1}}}}
    ],
    "explanation": "Groups PAYMENT_RECEIVED events by day for the last 30 days",
    "involves_multiple_collections": false
}}

Example 11 - Payment Events with Channel Status (Last Month):
User: "Show payment events with delivery status for last month"
IMPORTANT: Calculate actual date range based on CURRENT DATE.
{{
    "query_type": "aggregation",
    "target_collection": "notification_events",
    "query": [
        {{"$match": {{
            "event_name": "PAYMENT_RECEIVED",
            "created_at": {{
                "$gte": {{"$date": "<CURRENT_DATE minus 30 days>T00:00:00.000Z"}},
                "$lte": {{"$date": "<CURRENT_DATE>T23:59:59.999Z"}}
            }}
        }}}},
        {{"$lookup": {{
            "from": "email_notifications",
            "localField": "event_tracking_id",
            "foreignField": "event_tracking_id",
            "as": "email"
        }}}},
        {{"$lookup": {{
            "from": "sms_notifications",
            "localField": "event_tracking_id",
            "foreignField": "event_tracking_id",
            "as": "sms"
        }}}},
        {{"$addFields": {{
            "email": {{"$arrayElemAt": ["$email", 0]}},
            "sms": {{"$arrayElemAt": ["$sms", 0]}}
        }}}},
        {{"$limit": 100}}
    ],
    "explanation": "Shows PAYMENT_RECEIVED events from last month with email and SMS delivery status",
    "involves_multiple_collections": true
}}

Example 12 - Monthly Aggregation with Event Count:
User: "Group payment notifications by month"
{{
    "query_type": "aggregation",
    "target_collection": "notification_events",
    "query": [
        {{"$match": {{"event_name": "PAYMENT_RECEIVED"}}}},
        {{"$group": {{
            "_id": {{
                "year": {{"$year": "$created_at"}},
                "month": {{"$month": "$created_at"}}
            }},
            "count": {{"$sum": 1}},
            "by_status": {{"$push": "$status"}}
        }}}},
        {{"$sort": {{"_id.year": -1, "_id.month": -1}}}},
        {{"$limit": 12}}
    ],
    "explanation": "Groups PAYMENT_RECEIVED events by year and month, showing last 12 months",
    "involves_multiple_collections": false
}}

CRITICAL: Return ONLY valid JSON. No markdown, no code blocks, no extra text."""

    def _create_query_chain(self):
        """Create LangChain chain for query generation"""
        from langchain_core.messages import SystemMessage

        prompt = ChatPromptTemplate.from_messages([
            SystemMessage(content=self._get_system_prompt()),
            HumanMessagePromptTemplate.from_template("Convert this to MongoDB query: {user_input}")
        ])
        return prompt | self.llm | self.json_parser

    def generate_mql(self, user_input: str) -> dict:
        """Generate MongoDB query for multi-collection system"""
        try:
            chain = self._create_query_chain()
            result = chain.invoke({"user_input": user_input})

            logger.info(f"Generated MQL for multi-collection query: {user_input[:50]}...")

            # Ensure target_collection is set
            if "target_collection" not in result:
                result["target_collection"] = "notification_events"

            return result

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse AI response as JSON: {e}")
            raise ValueError(f"AI returned invalid JSON: {e}")
        except Exception as e:
            logger.error(f"Error generating MQL: {e}")
            raise


# Singleton instance
multi_collection_ai_service = MultiCollectionAIService()
