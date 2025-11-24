from fastapi import APIRouter, HTTPException
from credit_card_app.models.credit_card_schema import (
    QueryRequest, QueryResponse, SummaryRequest, SummaryResponse, CREDIT_CARD_SCHEMA
)
from credit_card_app.services.ai_query_service import credit_card_query_service
from credit_card_app.services.database_service import cc_db_service
from credit_card_app.services.summarization_service import summarization_service
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
    Convert natural language to MongoDB query for credit card transactions.

    Examples:
    - "Show all dining transactions over $50"
    - "Find transactions at Amazon in the last month"
    - "Show me all refunds"
    - "Get travel expenses from last quarter"
    """
    try:
        # Generate MQL from user input using AI (only schema is sent to AI)
        mql_result = credit_card_query_service.generate_mql(request.user_input)

        response = QueryResponse(
            user_input=request.user_input,
            generated_mql=mql_result.get("query", {}),
            explanation=mql_result.get("explanation", ""),
        )

        # Execute query if requested
        if request.execute:
            start_time = time.time()

            if mql_result.get("query_type") == "aggregation":
                results = cc_db_service.execute_aggregation(mql_result["query"])
            else:
                results = cc_db_service.execute_find(
                    mql_result["query"],
                    projection=mql_result.get("projection")
                )

            execution_time = (time.time() - start_time) * 1000

            response.results = serialize_mongo_results(results)
            response.count = len(results)
            response.execution_time_ms = round(execution_time, 2)

            # Generate summary if requested (only sends aggregated stats, not raw data)
            if request.summarize and results:
                summary_data = cc_db_service.get_summary_data(mql_result["query"])
                summary_result = summarization_service.generate_summary(
                    summary_data,
                    request.user_input
                )
                response.summary = summary_result.get("summary", "")

        return response

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error processing query: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/analyze", response_model=SummaryResponse)
async def analyze_transactions(request: SummaryRequest):
    """
    Generate comprehensive analysis and summary of credit card transactions.

    IMPORTANT: Only aggregated statistics are sent to AI, NO raw transaction data.

    Examples:
    - "Analyze my spending for last month"
    - "Summary of all dining expenses"
    - "What are my top spending categories?"
    """
    try:
        start_time = time.time()

        # Generate query to filter transactions
        mql_result = credit_card_query_service.generate_mql(request.user_input)

        # Get aggregated summary data (NO raw transactions sent to AI)
        summary_data = cc_db_service.get_summary_data(mql_result.get("query", {}))

        # Calculate statistics
        total_stats = summary_data.get("total_stats", [{}])[0]
        category_breakdown = summary_data.get("category_breakdown", [])
        merchant_top10 = summary_data.get("merchant_top10", [])
        transaction_types = summary_data.get("transaction_types", [])

        total_amount = total_stats.get("total_amount", 0)
        total_count = total_stats.get("total_count", 0)
        avg_amount = total_stats.get("avg_amount", 0)

        # Prepare statistics for AI summarization
        statistics = {
            "total_transactions": total_count,
            "total_amount": f"${total_amount:.2f}",
            "average_transaction": f"${avg_amount:.2f}",
            "max_transaction": f"${total_stats.get('max_amount', 0):.2f}",
            "min_transaction": f"${total_stats.get('min_amount', 0):.2f}",
            "spending_by_category": {
                cat['_id']: f"${cat['total']:.2f} ({cat['count']} txns)"
                for cat in category_breakdown[:5]
            },
            "top_merchants": {
                merch['_id']: f"${merch['total']:.2f}"
                for merch in merchant_top10[:5]
            },
            "transaction_types": {
                t['_id']: f"{t['count']} transactions (${t['total']:.2f})"
                for t in transaction_types
            }
        }

        # Generate AI summary (only receives aggregated statistics)
        summary_result = summarization_service.generate_summary(
            statistics,
            request.user_input
        )

        # Generate insights from category data
        insights = summarization_service.generate_spending_insights(category_breakdown)

        execution_time = (time.time() - start_time) * 1000

        return SummaryResponse(
            summary=summary_result.get("summary", "No summary available"),
            statistics=statistics,
            insights=insights,
            total_transactions=total_count,
            total_amount=round(total_amount, 2),
            execution_time_ms=round(execution_time, 2)
        )

    except Exception as e:
        logger.error(f"Error analyzing transactions: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats")
async def get_statistics():
    """Get comprehensive credit card transaction statistics"""
    try:
        stats = cc_db_service.get_statistics()
        return stats
    except Exception as e:
        logger.error(f"Error getting statistics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/schema")
async def get_schema():
    """Get the credit card transaction schema"""
    return CREDIT_CARD_SCHEMA


@router.get("/health")
async def health_check():
    """Health check endpoint for credit card service"""
    try:
        cc_db_service.get_database().command('ping')
        return {
            "status": "healthy",
            "service": "credit_card_transactions",
            "database": "connected"
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "service": "credit_card_transactions",
            "database": str(e)
        }
