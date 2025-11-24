from fastapi import APIRouter, HTTPException
from app.models.schemas import (
    QueryRequest, QueryResponse,
    AggregationRequest, AggregationResponse,
    ReportRequest, ReportResponse
)
from app.services.ai_service import ai_service
from app.services.database import db_service
from app.services.report_service import report_service
import time
import logging
from bson import json_util
import json

logger = logging.getLogger(__name__)

router = APIRouter()


def serialize_mongo_results(results: list) -> list:
    """Serialize MongoDB results to JSON-compatible format"""
    return json.loads(json_util.dumps(results))


@router.post("/query", response_model=QueryResponse)
async def generate_and_execute_query(request: QueryRequest):
    """
    Convert natural language to MongoDB query and optionally execute it.

    Examples:
    - "Find all failed notifications from last week"
    - "Show me email notifications for customer C001"
    - "Get notifications with priority 1 that are pending"
    """
    try:
        # Generate MQL from user input using AI
        mql_result = ai_service.generate_mql(request.user_input)

        response = QueryResponse(
            user_input=request.user_input,
            generated_mql=mql_result.get("query", {}),
            explanation=mql_result.get("explanation", ""),
        )

        # Execute query if requested
        if request.execute:
            start_time = time.time()

            if mql_result.get("query_type") == "aggregation":
                results = db_service.execute_aggregation(mql_result["query"])
            else:
                results = db_service.execute_find(
                    mql_result["query"],
                    projection=mql_result.get("projection")
                )

            execution_time = (time.time() - start_time) * 1000

            response.results = serialize_mongo_results(results)
            response.count = len(results)
            response.execution_time_ms = round(execution_time, 2)

        return response

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error processing query: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/aggregation", response_model=AggregationResponse)
async def generate_and_execute_aggregation(request: AggregationRequest):
    """
    Convert natural language to MongoDB aggregation pipeline and execute it.

    Examples:
    - "Count notifications by status"
    - "Show average delivery time by channel"
    - "Top 10 customers by notification count"
    """
    try:
        # Generate aggregation pipeline using AI
        mql_result = ai_service.generate_mql(request.user_input)

        if mql_result.get("query_type") != "aggregation":
            # If AI returned a find query, wrap it in aggregation
            pipeline = [{"$match": mql_result.get("query", {})}]
        else:
            pipeline = mql_result.get("query", [])

        response = AggregationResponse(
            user_input=request.user_input,
            generated_pipeline=pipeline,
            explanation=mql_result.get("explanation", ""),
        )

        # Execute aggregation if requested
        if request.execute:
            start_time = time.time()
            results = db_service.execute_aggregation(pipeline)
            execution_time = (time.time() - start_time) * 1000

            response.results = serialize_mongo_results(results)
            response.execution_time_ms = round(execution_time, 2)

        return response

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error processing aggregation: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/report", response_model=ReportResponse)
async def generate_report(request: ReportRequest):
    """
    Generate a report based on natural language description.

    Examples:
    - "Daily notification summary for the last 7 days"
    - "Channel performance report showing delivery rates"
    - "Customer engagement report by notification type"
    """
    try:
        # Generate report query using AI
        mql_result = ai_service.generate_report_query(request.user_input)

        # Generate the report
        report = report_service.generate_report(
            report_name=request.user_input[:50],
            pipeline=mql_result.get("query", []),
            output_format=request.report_format
        )

        return report

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error generating report: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/schema")
async def get_schema():
    """Get the notification schema for reference"""
    from app.models.schemas import NOTIFICATION_SCHEMA
    return NOTIFICATION_SCHEMA


@router.get("/stats")
async def get_database_stats():
    """Get basic database statistics"""
    try:
        collection = db_service.get_collection()

        total_count = collection.count_documents({})

        # Get counts by status
        status_counts = list(collection.aggregate([
            {"$group": {"_id": "$status", "count": {"$sum": 1}}}
        ]))

        # Get counts by channel
        channel_counts = list(collection.aggregate([
            {"$group": {"_id": "$channel", "count": {"$sum": 1}}}
        ]))

        return {
            "total_notifications": total_count,
            "by_status": {item["_id"]: item["count"] for item in status_counts},
            "by_channel": {item["_id"]: item["count"] for item in channel_counts}
        }
    except Exception as e:
        logger.error(f"Error getting stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        # Test database connection
        db_service.get_database().command('ping')
        return {"status": "healthy", "database": "connected"}
    except Exception as e:
        return {"status": "unhealthy", "database": str(e)}
