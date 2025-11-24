import json
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate, SystemMessagePromptTemplate, HumanMessagePromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from app.config import settings
from credit_card_app.models.credit_card_schema import CREDIT_CARD_SCHEMA
import logging

logger = logging.getLogger(__name__)


class CreditCardQueryService:
    """AI service for converting natural language to MongoDB queries for credit card transactions"""

    def __init__(self):
        self.llm = ChatOpenAI(
            api_key=settings.OPENAI_API_KEY,
            model=settings.OPENAI_MODEL,
            temperature=0
        )
        self.json_parser = JsonOutputParser()

    def _get_system_prompt(self) -> str:
        """Get the system prompt with credit card schema context"""
        return f"""You are an expert MongoDB query generator for credit card transaction data.
Your task is to convert natural language queries into valid MongoDB Query Language (MQL) queries.

IMPORTANT: You will ONLY receive the database schema and user query. You will NEVER receive actual transaction data.
Your job is to generate queries that can be executed against the database.

Database Schema:
Collection: {CREDIT_CARD_SCHEMA['collection']}
Fields:
{json.dumps(CREDIT_CARD_SCHEMA['fields'], indent=2)}

Available indexes: {', '.join(CREDIT_CARD_SCHEMA['indexes'])}

CRITICAL RULES:
1. Return valid MongoDB query syntax only
2. Use proper date handling with ISODate format
3. For date comparisons, use $gte, $lte, $gt, $lt operators
4. Use $regex for text searches with case-insensitivity when appropriate
5. Return queries as valid JSON parseable by Python's json.loads()
6. For aggregation queries, return a pipeline array
7. Use indexed fields when possible for performance
8. Handle common patterns like "last month", "this year", "top 10", etc.
9. For amounts, remember positive = charges, negative = credits/refunds
10. Categories are: groceries, dining, shopping, travel, entertainment, utilities, gas, healthcare, education, other
11. Transaction types are: purchase, refund, payment, fee, interest, cashback
12. Status values are: posted, pending, declined, reversed

Response Format (RETURN ONLY JSON, NO MARKDOWN):
{{
    "query_type": "find" or "aggregation",
    "query": {{...}} or [...],
    "projection": {{...}} (optional for find queries),
    "explanation": "brief explanation of what the query does"
}}

Example 1 - Find Query:
{{
    "query_type": "find",
    "query": {{"category": "dining", "status": "posted"}},
    "projection": {{"merchant_name": 1, "amount": 1, "transaction_date": 1}},
    "explanation": "Finds all posted dining transactions with merchant, amount, and date"
}}

Example 2 - Aggregation Query:
{{
    "query_type": "aggregation",
    "query": [
        {{"$match": {{"status": "posted"}}}},
        {{"$group": {{"_id": "$category", "total": {{"$sum": "$amount"}}, "count": {{"$sum": 1}}}}}},
        {{"$sort": {{"total": -1}}}}
    ],
    "explanation": "Groups posted transactions by category, calculates totals and counts, sorted by highest spending"
}}

Example 3 - Date Range Query:
{{
    "query_type": "find",
    "query": {{
        "transaction_date": {{
            "$gte": {{"$date": "2024-11-01T00:00:00Z"}},
            "$lte": {{"$date": "2024-11-30T23:59:59Z"}}
        }},
        "status": "posted"
    }},
    "explanation": "Finds all posted transactions in November 2024"
}}

CRITICAL: Return ONLY the JSON object. No markdown formatting, no code blocks, no additional text."""

    def _create_query_chain(self):
        """Create a LangChain chain for query generation"""
        prompt = ChatPromptTemplate.from_messages([
            SystemMessagePromptTemplate.from_template(self._get_system_prompt()),
            HumanMessagePromptTemplate.from_template("Convert this to a MongoDB query: {user_input}")
        ])

        return prompt | self.llm | self.json_parser

    def generate_mql(self, user_input: str) -> dict:
        """Generate MongoDB query from natural language input"""
        try:
            chain = self._create_query_chain()
            result = chain.invoke({"user_input": user_input})

            logger.info(f"Generated MQL for credit card query: {user_input[:50]}...")
            return result

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse AI response as JSON: {e}")
            raise ValueError(f"AI returned invalid JSON: {e}")
        except Exception as e:
            logger.error(f"Error generating MQL: {e}")
            raise

    def generate_aggregation_query(self, user_input: str) -> dict:
        """Generate MongoDB aggregation pipeline for analysis"""
        aggregation_prompt = """Generate a MongoDB aggregation pipeline for this credit card transaction analysis: {user_input}

The pipeline should:
1. Include appropriate $match, $group, $sort stages
2. Calculate relevant metrics (totals, averages, counts)
3. Format output suitable for financial analysis
4. Include date grouping if time-based analysis is needed
5. Consider spending patterns and categories

Return the response in the standard JSON format with query_type set to "aggregation"."""

        try:
            prompt = ChatPromptTemplate.from_messages([
                SystemMessagePromptTemplate.from_template(self._get_system_prompt()),
                HumanMessagePromptTemplate.from_template(aggregation_prompt)
            ])

            chain = prompt | self.llm | self.json_parser
            result = chain.invoke({"user_input": user_input})

            logger.info(f"Generated aggregation query for: {user_input[:50]}...")
            return result

        except Exception as e:
            logger.error(f"Error generating aggregation query: {e}")
            raise


# Singleton instance
credit_card_query_service = CreditCardQueryService()
