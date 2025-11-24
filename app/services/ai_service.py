import json
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate, SystemMessagePromptTemplate, HumanMessagePromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from app.config import settings
from app.models.schemas import NOTIFICATION_SCHEMA
import logging

logger = logging.getLogger(__name__)


class AIQueryService:
    def __init__(self):
        self.llm = ChatOpenAI(
            api_key=settings.OPENAI_API_KEY,
            model=settings.OPENAI_MODEL,
            temperature=0
        )
        self.json_parser = JsonOutputParser()

    def _get_system_prompt(self) -> str:
        """Get the system prompt with schema context"""
        return f"""You are a MongoDB query generator expert. Your task is to convert natural language queries into valid MongoDB Query Language (MQL) queries.

You have access to a database with the following schema:

Collection: {NOTIFICATION_SCHEMA['collection']}
Fields:
{json.dumps(NOTIFICATION_SCHEMA['fields'], indent=2)}

Available indexes: {', '.join(NOTIFICATION_SCHEMA['indexes'])}

IMPORTANT RULES:
1. Always return valid MongoDB query syntax
2. Use proper date handling with ISODate format
3. For date comparisons, use $gte, $lte, $gt, $lt operators
4. Use $regex for text searches with case-insensitivity when appropriate
5. Return queries as valid JSON that can be parsed by Python's json.loads()
6. For aggregation queries, return a pipeline array
7. Consider query performance - use indexed fields when possible
8. Handle common patterns like "last 7 days", "this month", etc.

Response Format:
You must respond with a JSON object containing:
- "query_type": either "find" or "aggregation"
- "query": the MongoDB query object (for find) or pipeline array (for aggregation)
- "projection": optional field projection for find queries
- "explanation": brief explanation of what the query does

Example response for a find query:
{{
    "query_type": "find",
    "query": {{"status": "failed", "channel": "email"}},
    "projection": {{"customer_email": 1, "error_details": 1, "created_at": 1}},
    "explanation": "Finds all failed email notifications with customer email, error details, and creation date"
}}

Example response for an aggregation:
{{
    "query_type": "aggregation",
    "query": [
        {{"$match": {{"status": "delivered"}}}},
        {{"$group": {{"_id": "$channel", "count": {{"$sum": 1}}}}}}
    ],
    "explanation": "Groups delivered notifications by channel and counts them"
}}

CRITICAL: Return ONLY the JSON object, no additional text or markdown formatting."""

    def _create_query_chain(self):
        """Create a LangChain chain for query generation"""
        prompt = ChatPromptTemplate.from_messages([
            SystemMessagePromptTemplate.from_template(self._get_system_prompt()),
            HumanMessagePromptTemplate.from_template("Convert this to a MongoDB query: {user_input}")
        ])

        return prompt | self.llm | self.json_parser

    def _clean_response(self, response_text: str) -> str:
        """Clean up response if it has markdown code blocks"""
        if response_text.startswith("```"):
            response_text = response_text.split("```")[1]
            if response_text.startswith("json"):
                response_text = response_text[4:]
            response_text = response_text.strip()
        return response_text

    def generate_mql(self, user_input: str) -> dict:
        """Generate MongoDB query from natural language input"""
        try:
            chain = self._create_query_chain()
            result = chain.invoke({"user_input": user_input})

            logger.info(f"Generated MQL for: {user_input[:50]}...")
            return result

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse AI response as JSON: {e}")
            raise ValueError(f"AI returned invalid JSON: {e}")
        except Exception as e:
            logger.error(f"Error generating MQL: {e}")
            raise

    def generate_report_query(self, user_input: str) -> dict:
        """Generate MongoDB aggregation pipeline for report generation"""
        report_prompt_template = """Generate a MongoDB aggregation pipeline for this report requirement: {user_input}

The pipeline should:
1. Include appropriate $match, $group, $sort stages
2. Calculate relevant metrics (counts, averages, etc.)
3. Format output suitable for reporting
4. Include date grouping if time-based analysis is needed

Return the response in the standard JSON format with query_type set to "aggregation"."""

        try:
            prompt = ChatPromptTemplate.from_messages([
                SystemMessagePromptTemplate.from_template(self._get_system_prompt()),
                HumanMessagePromptTemplate.from_template(report_prompt_template)
            ])

            chain = prompt | self.llm | self.json_parser
            result = chain.invoke({"user_input": user_input})

            logger.info(f"Generated report query for: {user_input[:50]}...")
            return result

        except Exception as e:
            logger.error(f"Error generating report query: {e}")
            raise


# Singleton instance
ai_service = AIQueryService()
