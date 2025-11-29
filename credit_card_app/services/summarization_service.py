from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from app.config import settings
import logging
from typing import List, Dict

logger = logging.getLogger(__name__)


class TransactionSummarizationService:
    """Service for generating intelligent summaries of credit card transactions"""

    def __init__(self):
        self.llm = ChatOpenAI(
            api_key=settings.OPENAI_API_KEY,
            model=settings.OPENAI_MODEL,
            temperature=0.3  # Slightly higher for more natural summaries
        )

    def generate_summary(self, statistics: Dict, user_query: str = "") -> Dict:
        """
        Generate a comprehensive summary based on transaction statistics.

        IMPORTANT: Only statistics/aggregated data is sent to AI, NOT raw transaction data.

        Args:
            statistics: Aggregated statistics (totals, counts, averages)
            user_query: Original user query for context

        Returns:
            Dict with summary text and insights
        """
        try:
            prompt_template = """You are a financial analyst assistant helping users understand their credit card spending.

You will receive ONLY aggregated statistics and summaries - NO individual transaction data.

User Query: {user_query}

Statistics:
{statistics}

Based on these statistics, provide:
1. A clear, conversational summary (2-3 sentences)
2. 3-5 key insights about spending patterns
3. Any notable observations or recommendations

Format your response as JSON:
{{{{
    "summary": "Natural language summary of the data",
    "insights": ["insight 1", "insight 2", "insight 3"],
    "observations": ["observation 1", "observation 2"]
}}}}

Be specific with numbers and percentages. Focus on patterns, trends, and actionable insights.
"""

            prompt = ChatPromptTemplate.from_template(prompt_template)
            chain = prompt | self.llm

            response = chain.invoke({
                "user_query": user_query,
                "statistics": self._format_statistics(statistics)
            })

            # Parse response
            import json
            result = json.loads(response.content)

            logger.info("Generated transaction summary successfully")
            return result

        except Exception as e:
            logger.error(f"Error generating summary: {e}")
            return {
                "summary": "Summary generation failed. Please try again.",
                "insights": [],
                "observations": []
            }

    def _format_statistics(self, stats: Dict) -> str:
        """Format statistics into a readable string for the AI"""
        formatted = []

        for key, value in stats.items():
            if isinstance(value, dict):
                formatted.append(f"\n{key}:")
                for sub_key, sub_value in value.items():
                    formatted.append(f"  - {sub_key}: {sub_value}")
            elif isinstance(value, list):
                formatted.append(f"\n{key}:")
                for item in value:
                    formatted.append(f"  - {item}")
            else:
                formatted.append(f"{key}: {value}")

        return "\n".join(formatted)

    def generate_spending_insights(self, category_totals: List[Dict]) -> List[str]:
        """Generate insights from category spending data"""
        insights = []

        if not category_totals:
            return ["No transactions found for analysis"]

        # Find top spending category
        if category_totals:
            top_category = category_totals[0]
            insights.append(
                f"Highest spending in {top_category.get('_id', 'unknown')}: "
                f"${top_category.get('total', 0):.2f} "
                f"({top_category.get('count', 0)} transactions)"
            )

        # Calculate total spending
        total_spent = sum(cat.get('total', 0) for cat in category_totals)
        if total_spent > 0:
            insights.append(f"Total spending: ${total_spent:.2f}")

            # Calculate top category percentage
            if category_totals:
                top_percent = (category_totals[0].get('total', 0) / total_spent) * 100
                insights.append(
                    f"Top category represents {top_percent:.1f}% of total spending"
                )

        # Average transaction
        total_transactions = sum(cat.get('count', 0) for cat in category_totals)
        if total_transactions > 0:
            avg_transaction = total_spent / total_transactions
            insights.append(f"Average transaction: ${avg_transaction:.2f}")

        return insights

    def create_statement_summary(self, aggregation_results: List[Dict],
                                 total_count: int, total_amount: float) -> str:
        """Create a comprehensive statement summary"""
        try:
            summary_parts = []

            # Overall summary
            summary_parts.append(
                f"Statement Summary: {total_count} transactions totaling ${total_amount:.2f}"
            )

            # Category breakdown
            if aggregation_results:
                summary_parts.append("\nSpending by Category:")
                for result in aggregation_results[:5]:  # Top 5 categories
                    category = result.get('_id', 'Unknown')
                    total = result.get('total', 0)
                    count = result.get('count', 0)
                    avg = result.get('average', 0)

                    summary_parts.append(
                        f"  • {category.title()}: ${total:.2f} "
                        f"({count} transactions, avg ${avg:.2f})"
                    )

            return "\n".join(summary_parts)

        except Exception as e:
            logger.error(f"Error creating statement summary: {e}")
            return "Summary unavailable"


# Singleton instance
summarization_service = TransactionSummarizationService()
