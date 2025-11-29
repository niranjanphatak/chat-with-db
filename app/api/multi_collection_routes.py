from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, List, Any
from app.services.multi_collection_ai_service import multi_collection_ai_service
from app.services.multi_collection_db_service import multi_collection_db_service
import time
import logging
from bson import json_util
import json

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/v2", tags=["Multi-Collection Notifications"])


# ============================================================================
# Request/Response Models
# ============================================================================

class MultiCollectionQueryRequest(BaseModel):
    user_input: str = Field(..., description="Natural language query")
    execute: bool = Field(default=True, description="Whether to execute the query")


class MultiCollectionQueryResponse(BaseModel):
    user_input: str
    target_collection: str
    generated_mql: dict | list
    explanation: str
    involves_multiple_collections: bool
    results: Optional[List[dict]] = None
    count: Optional[int] = None
    execution_time_ms: Optional[float] = None


def serialize_mongo_results(results: list) -> list:
    """Serialize MongoDB results to JSON"""
    return json.loads(json_util.dumps(results))


# ============================================================================
# API Endpoints
# ============================================================================

@router.post("/query", response_model=MultiCollectionQueryResponse)
async def query_multi_collection(request: MultiCollectionQueryRequest):
    """
    Query the multi-collection notification system using natural language.

    The system understands:
    - Primary collection (notification_events)
    - Channel collections (email, SMS, push, in-app)
    - Cross-collection queries with $lookup

    Examples:
    - "Show all accepted notification events"
    - "Find failed email notifications"
    - "Show events with delivered emails"
    - "Count notifications by channel and status"
    - "Find events where email delivered but SMS failed"

    NOTE: AI is used ONLY for query generation. NO data is sent to AI.
    """
    try:
        # Generate MQL using AI (only schema sent)
        mql_result = multi_collection_ai_service.generate_mql(request.user_input)

        # Validate response
        if "query" not in mql_result:
            raise ValueError("AI did not return a query")

        target_collection = mql_result.get("target_collection", "notification_events")
        query_type = mql_result.get("query_type", "find")
        involves_multiple = mql_result.get("involves_multiple_collections", False)

        response = MultiCollectionQueryResponse(
            user_input=request.user_input,
            target_collection=target_collection,
            generated_mql=mql_result["query"],
            explanation=mql_result.get("explanation", ""),
            involves_multiple_collections=involves_multiple
        )

        # Execute if requested
        if request.execute:
            start_time = time.time()

            if query_type == "aggregation":
                pipeline = mql_result["query"]
                if not isinstance(pipeline, list):
                    raise ValueError(f"Aggregation pipeline must be a list, got {type(pipeline).__name__}")

                results = multi_collection_db_service.execute_aggregation(
                    target_collection,
                    pipeline
                )
            else:
                query = mql_result["query"]
                if not isinstance(query, dict):
                    raise ValueError(f"Find query must be a dict, got {type(query).__name__}")

                results = multi_collection_db_service.execute_find(
                    target_collection,
                    query,
                    projection=mql_result.get("projection"),
                    limit=100
                )

            execution_time = (time.time() - start_time) * 1000

            response.results = serialize_mongo_results(results)
            response.count = len(results)
            response.execution_time_ms = round(execution_time, 2)

        return response

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error processing multi-collection query: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/dashboard")
async def get_multi_collection_dashboard():
    """
    Get comprehensive dashboard data across all collections.

    Returns statistics for:
    - Notification events (by status, type, priority)
    - Email channel (delivery rates, status distribution)
    - SMS channel (delivery rates, status distribution)
    - Push channel (delivery rates, status distribution)
    - In-app channel (delivery rates, status distribution)
    - Cross-channel insights
    - Time-based trends
    """
    try:
        stats = multi_collection_db_service.get_dashboard_stats()
        return serialize_mongo_results([stats])[0]
    except Exception as e:
        logger.error(f"Error fetching dashboard data: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/event/{event_tracking_id}")
async def get_event_details(event_tracking_id: str):
    """
    Get complete details of a notification event including all channel statuses.

    Returns:
    - Event details from notification_events
    - Email status (if sent via email)
    - SMS status (if sent via SMS)
    - Push status (if sent via push)
    - In-app status (if sent via in-app)
    """
    try:
        result = multi_collection_db_service.get_event_with_channels(event_tracking_id)

        if not result["event"]:
            raise HTTPException(status_code=404, detail=f"Event {event_tracking_id} not found")

        return serialize_mongo_results([result])[0]
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching event details: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/events/with-channels")
async def get_events_with_channels(limit: int = 50, skip: int = 0):
    """
    Get events with their channel statuses using MongoDB $lookup.

    Query parameters:
    - limit: Number of events to return (default: 50, max: 200)
    - skip: Number of events to skip (for pagination)

    Returns events joined with all their channel statuses.
    """
    try:
        if limit > 200:
            limit = 200

        pipeline = [
            {"$skip": skip},
            {"$limit": limit},
            {"$sort": {"created_at": -1}},

            # Lookup all channels
            {"$lookup": {
                "from": "email_notifications",
                "localField": "event_tracking_id",
                "foreignField": "event_tracking_id",
                "as": "email"
            }},
            {"$lookup": {
                "from": "sms_notifications",
                "localField": "event_tracking_id",
                "foreignField": "event_tracking_id",
                "as": "sms"
            }},
            {"$lookup": {
                "from": "push_notifications",
                "localField": "event_tracking_id",
                "foreignField": "event_tracking_id",
                "as": "push"
            }},
            {"$lookup": {
                "from": "inapp_notifications",
                "localField": "event_tracking_id",
                "foreignField": "event_tracking_id",
                "as": "inapp"
            }},

            # Convert arrays to single objects
            {"$addFields": {
                "email": {"$arrayElemAt": ["$email", 0]},
                "sms": {"$arrayElemAt": ["$sms", 0]},
                "push": {"$arrayElemAt": ["$push", 0]},
                "inapp": {"$arrayElemAt": ["$inapp", 0]}
            }}
        ]

        results = multi_collection_db_service.execute_aggregation("notification_events", pipeline)
        return serialize_mongo_results(results)

    except Exception as e:
        logger.error(f"Error fetching events with channels: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats/channel/{channel_name}")
async def get_channel_stats(channel_name: str):
    """
    Get statistics for a specific channel.

    Channels: email, sms, push, inapp

    Returns:
    - Total notifications
    - Status distribution
    - Delivery rate
    - Recent activity
    """
    try:
        collection_map = {
            "email": "email_notifications",
            "sms": "sms_notifications",
            "push": "push_notifications",
            "inapp": "inapp_notifications"
        }

        if channel_name not in collection_map:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid channel. Must be one of: {', '.join(collection_map.keys())}"
            )

        collection_name = collection_map[channel_name]
        collection = multi_collection_db_service.get_collection(collection_name)

        stats = {
            "channel": channel_name,
            "total": collection.count_documents({}),
            "by_status": list(collection.aggregate([
                {"$group": {"_id": "$status", "count": {"$sum": 1}}},
                {"$sort": {"count": -1}}
            ])),
            "recent_activity": list(collection.aggregate([
                {"$match": {"sent_at": {"$exists": True}}},
                {"$group": {
                    "_id": {"$dateToString": {"format": "%Y-%m-%d", "date": "$sent_at"}},
                    "count": {"$sum": 1}
                }},
                {"$sort": {"_id": -1}},
                {"$limit": 7}
            ])),
            "delivery_metrics": multi_collection_db_service._calculate_delivery_rate(collection_name)
        }

        return serialize_mongo_results([stats])[0]

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching channel stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def health_check():
    """Health check for multi-collection API"""
    try:
        multi_collection_db_service.get_database().command('ping')

        # Check all collections exist
        collections = multi_collection_db_service.get_collection_names()
        collection_status = {}
        for coll_name in collections:
            count = multi_collection_db_service.get_collection(coll_name).count_documents({})
            collection_status[coll_name] = count

        return {
            "status": "healthy",
            "database": "connected",
            "version": "2.0-multi-collection",
            "collections": collection_status
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "database": str(e),
            "version": "2.0-multi-collection"
        }


@router.get("/schema")
async def get_schema():
    """Get the multi-collection schema for reference"""
    from app.models.new_notification_schema import MULTI_COLLECTION_NOTIFICATION_SCHEMA
    return MULTI_COLLECTION_NOTIFICATION_SCHEMA


@router.get("/stats/event-name")
async def get_event_name_stats():
    """
    Get statistics grouped by event_name.

    Returns counts, status breakdown, and channel distribution for each event name.
    Useful for charts showing event type distribution.
    """
    try:
        stats = multi_collection_db_service.get_event_name_stats()
        return serialize_mongo_results(stats)
    except Exception as e:
        logger.error(f"Error fetching event name stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats/event-name/{event_name}")
async def get_event_name_channel_breakdown(event_name: str):
    """
    Get detailed channel delivery breakdown for a specific event_name.

    Returns delivery/failure counts across all channels for the specified event name.
    Useful for charts showing channel performance by event type.

    Examples:
    - /api/v2/stats/event-name/ORDER_PLACED
    - /api/v2/stats/event-name/PAYMENT_RECEIVED
    """
    try:
        breakdown = multi_collection_db_service.get_event_name_channel_breakdown(event_name)

        if not breakdown:
            raise HTTPException(
                status_code=404,
                detail=f"No data found for event_name: {event_name}"
            )

        return serialize_mongo_results([breakdown])[0]
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching event name breakdown: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/events/by-event-name/{event_name}")
async def get_events_by_event_name(event_name: str, limit: int = 100):
    """
    Get all events for a specific event_name.

    Query parameters:
    - limit: Number of events to return (default: 100, max: 200)

    Returns all events matching the specified event_name.
    """
    try:
        if limit > 200:
            limit = 200

        events = multi_collection_db_service.get_events_by_event_name(event_name, limit)
        return serialize_mongo_results(events)
    except Exception as e:
        logger.error(f"Error fetching events by event_name: {e}")
        raise HTTPException(status_code=500, detail=str(e))
