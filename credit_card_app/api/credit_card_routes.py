from fastapi import APIRouter, HTTPException
from credit_card_app.models.credit_card_schema import (
    QueryRequest, QueryResponse, SummaryRequest, SummaryResponse, CREDIT_CARD_SCHEMA
)
from credit_card_app.services.ai_query_service import credit_card_query_service
from credit_card_app.services.database_service import cc_db_service
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

    NOTE: AI is used ONLY for query generation. NO data is sent to AI.
    """
    try:
        # Generate MQL from user input using AI (only schema is sent to AI)
        mql_result = credit_card_query_service.generate_mql(request.user_input)

        # Validate that query exists
        if "query" not in mql_result:
            raise ValueError("AI did not return a query")

        # Detect if query is suitable for charting
        chart_metadata = _detect_chart_type(mql_result)

        response = QueryResponse(
            user_input=request.user_input,
            generated_mql=mql_result.get("query", {}),
            explanation=mql_result.get("explanation", ""),
        )

        # Execute query if requested
        if request.execute:
            start_time = time.time()

            if mql_result.get("query_type") == "aggregation":
                query = mql_result["query"]
                # Validate pipeline is a list
                if not isinstance(query, list):
                    raise ValueError(f"Aggregation pipeline must be a list, got {type(query).__name__}")
                results = cc_db_service.execute_aggregation(query)
            else:
                query = mql_result["query"]
                # Validate query is a dict
                if not isinstance(query, dict):
                    raise ValueError(f"Find query must be a dict, got {type(query).__name__}")
                results = cc_db_service.execute_find(
                    query,
                    projection=mql_result.get("projection")
                )

            execution_time = (time.time() - start_time) * 1000

            response.results = serialize_mongo_results(results)
            response.count = len(results)
            response.execution_time_ms = round(execution_time, 2)

            # Add chart metadata if query is chartable
            if chart_metadata and chart_metadata.get("chartable"):
                response.chart_metadata = chart_metadata

        return response

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error processing query: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/analyze", response_model=SummaryResponse)
async def analyze_transactions(request: SummaryRequest):
    """
    Generate comprehensive analysis and statistics of credit card transactions.

    IMPORTANT: NO AI is used for analysis. All statistics calculated locally.
    NO data is sent to AI services.

    Examples:
    - "Analyze my spending for last month"
    - "Summary of all dining expenses"
    - "What are my top spending categories?"
    """
    try:
        start_time = time.time()

        # Generate query to filter transactions (only schema sent to AI)
        mql_result = credit_card_query_service.generate_mql(request.user_input)

        # Get aggregated summary data (calculated locally, NOT sent to AI)
        summary_data = cc_db_service.get_summary_data(mql_result.get("query", {}))

        # Calculate statistics locally
        total_stats = summary_data.get("total_stats", [{}])[0]
        category_breakdown = summary_data.get("category_breakdown", [])
        merchant_top10 = summary_data.get("merchant_top10", [])
        transaction_types = summary_data.get("transaction_types", [])

        total_amount = total_stats.get("total_amount", 0)
        total_count = total_stats.get("total_count", 0)
        avg_amount = total_stats.get("avg_amount", 0)

        # Format statistics (all done locally, no AI)
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

        # Generate insights locally (no AI used)
        insights = _generate_local_insights(category_breakdown, total_stats, total_amount, total_count)

        # Generate summary text locally (no AI)
        summary = _generate_local_summary(total_count, total_amount, avg_amount, category_breakdown)

        execution_time = (time.time() - start_time) * 1000

        return SummaryResponse(
            summary=summary,
            statistics=statistics,
            insights=insights,
            total_transactions=total_count,
            total_amount=round(total_amount, 2),
            execution_time_ms=round(execution_time, 2)
        )

    except Exception as e:
        logger.error(f"Error analyzing transactions: {e}")
        raise HTTPException(status_code=500, detail=str(e))


def _generate_local_insights(category_breakdown, total_stats, total_amount, total_count):
    """Generate insights locally without AI"""
    insights = []

    if not category_breakdown:
        return ["No transactions found for analysis"]

    # Top spending category
    if category_breakdown:
        top_category = category_breakdown[0]
        insights.append(
            f"Highest spending in {top_category.get('_id', 'unknown')}: "
            f"${top_category.get('total', 0):.2f} "
            f"({top_category.get('count', 0)} transactions)"
        )

    # Total spending
    if total_amount > 0:
        insights.append(f"Total spending: ${total_amount:.2f}")

        # Top category percentage
        if category_breakdown:
            top_percent = (category_breakdown[0].get('total', 0) / total_amount) * 100
            insights.append(
                f"Top category represents {top_percent:.1f}% of total spending"
            )

    # Average transaction
    if total_count > 0:
        avg_transaction = total_amount / total_count
        insights.append(f"Average transaction: ${avg_transaction:.2f}")

    # Transaction frequency
    if total_count > 0:
        insights.append(f"Total of {total_count} transactions")

    return insights


def _detect_chart_type(mql_result: dict) -> dict:
    """Detect if query results can be visualized as charts"""
    query_type = mql_result.get("query_type", "find")
    query = mql_result.get("query", {})
    projection = mql_result.get("projection", {})

    # Aggregation queries with grouping are usually chartable
    if query_type == "aggregation" and isinstance(query, list):
        has_group = any("$group" in stage for stage in query)
        has_sort = any("$sort" in stage for stage in query)

        if has_group:
            # Analyze grouping to determine chart type
            group_stage = next((stage["$group"] for stage in query if "$group" in stage), {})
            group_id = group_stage.get("_id", {})

            # Category/merchant grouping -> bar/pie chart
            if isinstance(group_id, str) and group_id.startswith("$"):
                field_name = group_id[1:]  # Remove $
                return {
                    "chartable": True,
                    "chart_type": "bar",
                    "alternative_charts": ["pie", "doughnut"],
                    "x_field": "_id",
                    "y_field": "total",
                    "label": f"By {field_name.replace('_', ' ').title()}",
                    "grouping_field": field_name
                }

            # Time-based grouping -> line chart
            elif isinstance(group_id, dict) and any(k in group_id for k in ["year", "month", "day"]):
                return {
                    "chartable": True,
                    "chart_type": "line",
                    "alternative_charts": ["bar"],
                    "x_field": "_id",
                    "y_field": "total",
                    "label": "Over Time",
                    "time_based": True
                }

    # Find queries - detect if they have useful numeric data to chart
    elif query_type == "find":
        # Check projection to see what fields are being returned
        projected_fields = []
        if projection:
            # Get explicitly included fields
            projected_fields = [k for k, v in projection.items() if v == 1 or v is True]

        # If no projection specified, assume common fields are available
        # But be conservative - don't assume all fields
        if not projected_fields:
            # When no projection, MongoDB returns all fields
            # Assume amount is available for charting
            return {
                "chartable": True,
                "chart_type": "bar",
                "alternative_charts": ["table"],
                "x_field": "auto",  # Let frontend auto-detect
                "y_field": "amount",
                "label": "Transaction Amounts"
            }

        # With explicit projection, check what's actually available
        has_amount = 'amount' in projected_fields
        has_date = 'transaction_date' in projected_fields
        has_merchant = 'merchant_name' in projected_fields
        has_category = 'category' in projected_fields

        # If we have amount data, it's chartable
        if has_amount:
            # Determine best label based on what fields we actually have
            label_field = "Transaction Amounts"

            # Prioritize based on what's actually projected
            if has_date and not has_merchant and not has_category:
                label_field = "Amounts by Date"
            elif has_merchant:
                label_field = "Amounts by Merchant"
            elif has_category:
                label_field = "Amounts by Category"
            elif has_date:
                label_field = "Amounts by Date"

            return {
                "chartable": True,
                "chart_type": "bar",
                "alternative_charts": ["table"],
                "x_field": "auto",  # Let frontend auto-detect based on available fields
                "y_field": "amount",
                "label": label_field
            }

        # No amount field in projection - not suitable for financial charts
        return {"chartable": False}

    return {"chartable": False}


def _generate_local_summary(total_count, total_amount, avg_amount, category_breakdown):
    """Generate summary text locally without AI"""
    if total_count == 0:
        return "No transactions found for the specified criteria."

    summary_parts = [
        f"You have {total_count} transactions totaling ${total_amount:.2f}.",
        f"Your average transaction is ${avg_amount:.2f}."
    ]

    if category_breakdown:
        top_cat = category_breakdown[0]
        summary_parts.append(
            f"Your highest spending category is {top_cat.get('_id', 'unknown')} "
            f"with ${top_cat.get('total', 0):.2f}."
        )

    return " ".join(summary_parts)


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
