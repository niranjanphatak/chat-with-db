# Data Sent to AI - Credit Card Transaction App

## ⚠️ IMPORTANT UPDATE
**As of the latest version, NO aggregated statistics or transaction data is sent to AI.**

AI is used ONLY for query generation. All analysis and summaries are generated locally without AI.

## Overview
This document details all data being sent to the AI service (Google Gemini 2.0 Flash) in the Credit Card Transaction Analysis application.

---

## AI Service Configuration

**Service:** Google Gemini AI (via OpenAI-compatible API)
- **API Endpoint:** `https://generativelanguage.googleapis.com/v1beta/openai/`
- **Model:** `gemini-2.0-flash`
- **API Key:** Same as main app (configured via environment variable `OPENAI_API_KEY`)

**Temperature Settings:**
- Query Generation: `0` (deterministic)
- ~~Summarization: `0.3`~~ **REMOVED - No longer uses AI for summarization**

**Location:**
- Query Service: [credit_card_app/services/ai_query_service.py](credit_card_app/services/ai_query_service.py#L16-L21)
- ~~Summarization Service~~ **REMOVED - Now generates summaries locally without AI**

---

## Data Sent to AI

### ✅ Current Status: ONLY Query Generation

**AI is now used ONLY for converting natural language to MongoDB queries.**
**NO transaction data, aggregated statistics, or summaries are sent to AI.**

### 1. Query Generation Service (ONLY AI Usage)

#### Database Schema (Sent with EVERY query request)

```json
{
  "collection": "credit_card_transactions",
  "fields": {
    "transaction_id": "Unique transaction identifier (e.g., TXN001234)",
    "card_number": "Last 4 digits masked (e.g., ****1234)",
    "cardholder_name": "Name on card",
    "transaction_date": "datetime - Date/time of transaction",
    "post_date": "datetime - Date posted to account",
    "merchant_name": "Name of merchant/vendor (e.g., Amazon.com)",
    "category": "Transaction category (groceries, dining, shopping, travel, entertainment, utilities, gas, healthcare, education, other)",
    "amount": "Transaction amount (positive=charges, negative=credits)",
    "currency": "Currency code (e.g., USD)",
    "transaction_type": "purchase, refund, payment, fee, interest, cashback",
    "status": "posted, pending, declined, reversed",
    "description": "Additional transaction details",
    "location": {
      "city": "string",
      "state": "string",
      "country": "string"
    },
    "is_international": "boolean - Whether transaction is international",
    "rewards_earned": "Rewards points or cashback earned"
  },
  "indexes": ["transaction_date", "category", "merchant_name", "card_number", "status"]
}
```

**System Prompt Highlights:**
- **CRITICAL NOTE in prompt:** "You will ONLY receive the database schema and user query. You will NEVER receive actual transaction data."
- Query generation rules
- Date handling instructions
- Category and transaction type enumerations
- Example queries with proper formatting

**Location:** [credit_card_app/services/ai_query_service.py](credit_card_app/services/ai_query_service.py#L24-L96)

---

### 2. ~~Transaction Summarization Service~~ **REMOVED**

**⚠️ THIS FEATURE HAS BEEN REMOVED**

The AI summarization service has been completely removed. All summaries and insights are now generated locally using simple rule-based logic.

**Old Behavior (REMOVED):**
- ~~Aggregated statistics were sent to AI~~
- ~~AI generated natural language summaries~~

**New Behavior (Current):**
- ✅ Statistics calculated locally
- ✅ Summaries generated using templates (no AI)
- ✅ Insights generated with simple logic (no AI)
- ✅ **ZERO data sent to AI for analysis**

---

### ~~2. Transaction Summarization Service~~ (DEPRECATED - See Above)

#### What Gets Sent: ONLY Aggregated Statistics

**IMPORTANT:** The summarization service receives **ONLY** aggregated statistics, **NOT** raw transaction data.

**Example of Data Sent to AI:**
```json
{
  "user_query": "Analyze my spending for last month",
  "statistics": {
    "total_transactions": 45,
    "total_amount": "$2,345.67",
    "average_transaction": "$52.13",
    "max_transaction": "$450.00",
    "min_transaction": "$3.50",
    "spending_by_category": {
      "dining": "$678.90 (12 txns)",
      "groceries": "$543.21 (8 txns)",
      "shopping": "$456.78 (15 txns)",
      "travel": "$389.50 (3 txns)",
      "gas": "$277.28 (7 txns)"
    },
    "top_merchants": {
      "Amazon.com": "$234.56",
      "Whole Foods": "$189.32",
      "Starbucks": "$156.78",
      "Shell Gas": "$134.90",
      "Target": "$98.45"
    },
    "transaction_types": {
      "purchase": "42 transactions ($2,456.78)",
      "refund": "2 transactions ($-89.50)",
      "cashback": "1 transaction ($-21.61)"
    }
  }
}
```

**System Prompt for Summarization:**
```
You are a financial analyst assistant helping users understand their credit card spending.

You will receive ONLY aggregated statistics and summaries - NO individual transaction data.

Based on these statistics, provide:
1. A clear, conversational summary (2-3 sentences)
2. 3-5 key insights about spending patterns
3. Any notable observations or recommendations
```

**Location:** [credit_card_app/services/summarization_service.py](credit_card_app/services/summarization_service.py#L34-L56)

---

## Data Flow by Endpoint

### 1. `/api/v1/credit-cards/query` - Query Generation

**Request from Frontend:**
```json
{
  "user_input": "Show all dining transactions over $50",
  "execute": true,
  "summarize": false
}
```

**Sent to AI (Query Service):**
- Database schema (structure only)
- User input: "Show all dining transactions over $50"

**AI Returns:**
```json
{
  "query_type": "find",
  "query": {
    "category": "dining",
    "amount": {"$gt": 50},
    "status": "posted"
  },
  "projection": {
    "merchant_name": 1,
    "amount": 1,
    "transaction_date": 1,
    "description": 1
  },
  "explanation": "Finds all posted dining transactions over $50 with merchant, amount, date and description"
}
```

**What Happens Next:**
- Query is executed against MongoDB locally
- Results are returned to user
- **NO transaction data sent back to AI**

**Code Location:** [credit_card_app/api/credit_card_routes.py](credit_card_app/api/credit_card_routes.py#L23-L92)

---

### 2. `/api/v1/credit-cards/analyze` - Transaction Analysis

**Request from Frontend:**
```json
{
  "user_input": "Analyze my spending for last month"
}
```

**Step 1 - Generate Query (AI receives schema only):**
- Database schema
- User input for query generation

**Step 2 - Get Aggregated Data (Local MongoDB):**
```javascript
// Executed locally, NOT sent to AI
db.credit_card_transactions.aggregate([
  { $match: { transaction_date: { $gte: lastMonth } } },
  { $group: {
    _id: null,
    total_amount: { $sum: "$amount" },
    total_count: { $sum: 1 },
    avg_amount: { $avg: "$amount" },
    max_amount: { $max: "$amount" },
    min_amount: { $min: "$amount" }
  }}
])
```

**Step 3 - Summarize (AI receives ONLY aggregated statistics):**
```json
{
  "total_transactions": 45,
  "total_amount": "$2,345.67",
  "average_transaction": "$52.13",
  "spending_by_category": {
    "dining": "$678.90 (12 txns)",
    "groceries": "$543.21 (8 txns)"
  }
}
```

**AI Returns:**
```json
{
  "summary": "Last month you made 45 transactions totaling $2,345.67. Your spending was highest in dining ($678.90) followed by groceries ($543.21). Average transaction was $52.13.",
  "insights": [
    "Dining represents 29% of your total spending",
    "You averaged 1.5 transactions per day",
    "Your largest single transaction was $450.00",
    "Grocery spending decreased compared to typical monthly average"
  ],
  "observations": [
    "Consider setting a budget for dining expenses",
    "Travel expenses were 17% of total, primarily concentrated in 3 large transactions"
  ]
}
```

**Code Location:** [credit_card_app/api/credit_card_routes.py](credit_card_app/api/credit_card_routes.py#L95-L169)

---

## What Data is NOT Sent to AI

### ❌ Never Sent to AI:

1. **Raw Transaction Records** - No individual transaction details
2. **Full Credit Card Numbers** - Only masked last 4 digits in schema
3. **Cardholder Personal Info** - No real names, addresses, SSNs
4. **Merchant Details** - Only aggregated top merchant names with totals
5. **Transaction Descriptions** - Not sent in summarization
6. **Actual Transaction IDs** - Schema only
7. **Location Data** - Not included in aggregations sent to AI
8. **Rewards Information** - Not sent to AI
9. **Database Credentials** - Never exposed
10. **Query Results** - Results stay local, only aggregated stats sent for summaries

### ✅ Only Sent to AI:

1. **Database Schema** (metadata, field types, enumerations)
2. **User's Natural Language Query**
3. **Aggregated Statistics** (totals, counts, averages - NO individual records)
4. **Category Names** (generic: dining, groceries, etc.)
5. **Top 5 Categories/Merchants** (names + totals only, no transaction details)

---

## Privacy & Security Features

### Data Minimization Examples

#### Example 1: Query Generation
**User:** "Show me Amazon purchases over $100"

**Sent to AI:**
```
Schema: [field definitions]
User Input: "Show me Amazon purchases over $100"
```

**NOT Sent:**
- No actual Amazon transactions
- No purchase details
- No dates of actual purchases
- No cardholder information

---

#### Example 2: Spending Analysis
**User:** "Analyze my dining expenses"

**Sent to AI:**
```json
{
  "spending_by_category": {
    "dining": "$678.90 (12 txns)"
  },
  "top_merchants": {
    "Restaurant A": "$234.56",
    "Restaurant B": "$156.78"
  },
  "average_transaction": "$56.58"
}
```

**NOT Sent:**
- Individual receipt amounts
- Dates of visits
- Tips or itemized details
- Your name or card number
- Specific locations of restaurants

---

### Code Comments Highlighting Privacy

From [credit_card_routes.py](credit_card_app/api/credit_card_routes.py):

**Line 35:**
```python
# Generate MQL from user input using AI (only schema is sent to AI)
```

**Line 74:**
```python
# Generate summary if requested (only sends aggregated stats, not raw data)
```

**Line 100:**
```python
# IMPORTANT: Only aggregated statistics are sent to AI, NO raw transaction data.
```

**Line 113:**
```python
# Get aggregated summary data (NO raw transactions sent to AI)
```

**Line 147:**
```python
# Generate AI summary (only receives aggregated statistics)
```

From [summarization_service.py](credit_card_app/services/summarization_service.py):

**Line 24:**
```python
IMPORTANT: Only statistics/aggregated data is sent to AI, NOT raw transaction data.
```

**Line 36:**
```python
You will receive ONLY aggregated statistics and summaries - NO individual transaction data.
```

---

## Data Processing Flow

```
┌─────────────────────┐
│   User Query        │
│ "Analyze spending"  │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────────┐
│  AI Query Service       │
│  (Schema ONLY sent)     │
└──────────┬──────────────┘
           │
           ▼ Returns MongoDB Query
┌─────────────────────────┐
│  Local MongoDB          │
│  Execute Aggregation    │
│  Calculate Statistics   │
└──────────┬──────────────┘
           │
           ▼ Aggregated Stats Only
┌─────────────────────────┐
│  AI Summarization       │
│  (Stats ONLY sent)      │
└──────────┬──────────────┘
           │
           ▼ Natural Language Summary
┌─────────────────────────┐
│  Return to User         │
└─────────────────────────┘
```

**Key Points:**
1. **Step 1:** Only schema sent to AI for query generation
2. **Step 2:** Query executed locally, results stay local
3. **Step 3:** Only aggregated statistics sent to AI for summarization
4. **No raw transaction data ever leaves your infrastructure**

---

## Logging and Audit Trail

### Query Generation Logging
```python
logger.info(f"Generated MQL for credit card query: {user_input[:50]}...")
```
- Only first 50 characters of user query logged
- No full queries or results logged

### Summarization Logging
```python
logger.info("Generated transaction summary successfully")
```
- Only success/failure logged
- No statistics or summaries logged

**Locations:**
- [ai_query_service.py:113](credit_card_app/services/ai_query_service.py#L113)
- [summarization_service.py:70](credit_card_app/services/summarization_service.py#L70)

---

## Code References

| Component | File Location | Lines |
|-----------|---------------|-------|
| Query Service Config | [ai_query_service.py](credit_card_app/services/ai_query_service.py) | 16-21 |
| Schema Definition | [credit_card_schema.py](credit_card_app/models/credit_card_schema.py) | 6-95 |
| System Prompt | [ai_query_service.py](credit_card_app/services/ai_query_service.py) | 24-96 |
| Query Endpoint | [credit_card_routes.py](credit_card_app/api/credit_card_routes.py) | 23-92 |
| Analysis Endpoint | [credit_card_routes.py](credit_card_app/api/credit_card_routes.py) | 95-169 |
| Summarization Service | [summarization_service.py](credit_card_app/services/summarization_service.py) | 20-79 |
| Statistics Formatting | [summarization_service.py](credit_card_app/services/summarization_service.py) | 81-97 |

---

## Summary

### Data Sent to AI:
✅ Database schema structure (metadata only)
✅ User's natural language query
✅ Aggregated statistics (totals, counts, averages)
✅ Top 5 categories/merchants (names + aggregated totals)

### Data NOT Sent to AI:
❌ Individual transaction records
❌ Credit card numbers (even masked)
❌ Cardholder personal information
❌ Transaction descriptions or details
❌ Exact dates of transactions
❌ Location information
❌ Raw query results

### Privacy Guarantees:
- **Query Generation:** Only schema sent, never data
- **Summarization:** Only aggregated statistics sent, never raw transactions
- **Data Storage:** All transaction data stays in local MongoDB
- **Processing:** AI only sees summaries, not details

The credit card app is designed with **privacy by default** - AI is used ONLY for:
1. Translating natural language → MongoDB queries
2. Converting aggregated statistics → readable summaries

**All actual transaction data processing happens locally on your infrastructure.**
