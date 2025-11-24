from pydantic import BaseModel, Field
from typing import Optional, Literal, List
from datetime import datetime

# Credit Card Transaction Schema for MongoDB
CREDIT_CARD_SCHEMA = {
    "collection": "credit_card_transactions",
    "description": "Credit card transaction records for statement analysis",
    "fields": {
        "transaction_id": {
            "type": "string",
            "description": "Unique transaction identifier",
            "example": "TXN001234"
        },
        "card_number": {
            "type": "string",
            "description": "Last 4 digits of credit card (masked)",
            "example": "****1234"
        },
        "cardholder_name": {
            "type": "string",
            "description": "Name on the credit card",
            "example": "John Doe"
        },
        "transaction_date": {
            "type": "datetime",
            "description": "Date and time of transaction",
            "example": "2024-11-15T14:30:00Z"
        },
        "post_date": {
            "type": "datetime",
            "description": "Date transaction was posted to account",
            "example": "2024-11-16T09:00:00Z"
        },
        "merchant_name": {
            "type": "string",
            "description": "Name of merchant/vendor",
            "example": "Amazon.com"
        },
        "category": {
            "type": "string",
            "description": "Transaction category",
            "enum": ["groceries", "dining", "shopping", "travel", "entertainment",
                    "utilities", "gas", "healthcare", "education", "other"],
            "example": "shopping"
        },
        "amount": {
            "type": "number",
            "description": "Transaction amount (positive for charges, negative for credits)",
            "example": 45.99
        },
        "currency": {
            "type": "string",
            "description": "Currency code",
            "example": "USD"
        },
        "transaction_type": {
            "type": "string",
            "description": "Type of transaction",
            "enum": ["purchase", "refund", "payment", "fee", "interest", "cashback"],
            "example": "purchase"
        },
        "status": {
            "type": "string",
            "description": "Transaction status",
            "enum": ["posted", "pending", "declined", "reversed"],
            "example": "posted"
        },
        "description": {
            "type": "string",
            "description": "Additional transaction details",
            "example": "Online purchase - Electronics"
        },
        "location": {
            "type": "object",
            "description": "Transaction location",
            "properties": {
                "city": {"type": "string"},
                "state": {"type": "string"},
                "country": {"type": "string"}
            }
        },
        "is_international": {
            "type": "boolean",
            "description": "Whether transaction is international",
            "example": False
        },
        "rewards_earned": {
            "type": "number",
            "description": "Rewards points or cashback earned",
            "example": 45.99
        }
    },
    "indexes": ["transaction_date", "category", "merchant_name", "card_number", "status"]
}


# Pydantic Models for API
class TransactionLocation(BaseModel):
    city: Optional[str] = None
    state: Optional[str] = None
    country: Optional[str] = "USA"


class CreditCardTransaction(BaseModel):
    transaction_id: str
    card_number: str
    cardholder_name: str
    transaction_date: datetime
    post_date: datetime
    merchant_name: str
    category: Literal["groceries", "dining", "shopping", "travel", "entertainment",
                     "utilities", "gas", "healthcare", "education", "other"]
    amount: float
    currency: str = "USD"
    transaction_type: Literal["purchase", "refund", "payment", "fee", "interest", "cashback"]
    status: Literal["posted", "pending", "declined", "reversed"] = "posted"
    description: Optional[str] = None
    location: Optional[TransactionLocation] = None
    is_international: bool = False
    rewards_earned: float = 0.0


class QueryRequest(BaseModel):
    user_input: str = Field(..., description="Natural language query")
    execute: bool = Field(default=True, description="Whether to execute the query")
    summarize: bool = Field(default=False, description="Whether to generate summary")


class QueryResponse(BaseModel):
    user_input: str
    generated_mql: dict
    explanation: str
    results: Optional[List[dict]] = None
    count: Optional[int] = None
    execution_time_ms: Optional[float] = None
    summary: Optional[str] = None


class SummaryRequest(BaseModel):
    user_input: str = Field(..., description="Natural language description for summary")
    date_range: Optional[dict] = None


class SummaryResponse(BaseModel):
    summary: str
    statistics: dict
    insights: List[str]
    total_transactions: int
    total_amount: float
    execution_time_ms: float
