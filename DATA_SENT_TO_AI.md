# Data Sent to AI Service - MongoDB Query AI Project

## Overview
This document details all data being sent to the AI service (Google Gemini 2.0 Flash) in the MongoDB Query AI application.

---

## AI Service Configuration

**Service:** Google Gemini AI (via OpenAI-compatible API)
- **API Endpoint:** `https://generativelanguage.googleapis.com/v1beta/openai/`
- **Model:** `gemini-2.0-flash`
- **API Key:** Configured via environment variable `OPENAI_API_KEY`
- **Temperature:** `0` (deterministic responses)

**Location:** [app/services/ai_service.py](app/services/ai_service.py#L14-L19)

---

## Data Sent to AI

### 1. System Prompt (Sent with EVERY request)

The AI receives a comprehensive system prompt that includes:

#### Database Schema Information
```json
{
  "collection": "customer_notifications",
  "fields": {
    "_id": "ObjectId - Unique identifier",
    "customer_id": "string - Customer unique identifier",
    "customer_name": "string - Customer full name",
    "customer_email": "string - Customer email address",
    "customer_phone": "string - Customer phone number",
    "notification_type": "string - Type: promotional, transactional, alert, reminder, system",
    "channel": "string - Delivery channel: email, sms, push, in_app",
    "status": "string - Status: pending, sent, delivered, failed, read",
    "subject": "string - Notification subject/title",
    "message": "string - Notification content",
    "priority": "integer - Priority level 1-5 (1=highest)",
    "created_at": "datetime - When notification was created",
    "sent_at": "datetime - When notification was sent",
    "delivered_at": "datetime - When notification was delivered",
    "read_at": "datetime - When notification was read",
    "metadata": {
      "campaign_id": "string - Associated campaign ID",
      "template_id": "string - Template used",
      "tags": "array of strings - Tags for categorization",
      "retry_count": "integer - Number of retry attempts",
      "device_info": "object - Device information for push notifications"
    },
    "error_details": "string - Error message if failed"
  },
  "indexes": ["customer_id", "status", "channel", "notification_type", "created_at", "sent_at"]
}
```

#### Instructions for AI
- MongoDB query generation rules
- Date handling with ISODate format
- Regex for text searches
- JSON output requirements
- Query type: "find" or "aggregation"
- Response format with query, projection, and explanation

**Full System Prompt Location:** [app/services/ai_service.py](app/services/ai_service.py#L22-L72)

---

### 2. User Input (User's Natural Language Query)

The actual query from the user is sent as:

```json
{
  "user_input": "<user's natural language query>"
}
```

#### Examples of User Input:
- "Find all failed email notifications"
- "Show me notifications sent in the last 7 days"
- "Get all pending SMS notifications with high priority"
- "Count notifications by status"
- "Top 10 customers by notification count"
- "Daily notification summary for the last 7 days"

---

## Data Flow by Endpoint

### 1. `/api/v1/query` - Query Generation
**Request from Frontend:**
```json
{
  "user_input": "Find all failed notifications",
  "execute": true
}
```

**Sent to AI:**
- System prompt with schema
- User input: "Find all failed notifications"

**AI Returns:**
```json
{
  "query_type": "find",
  "query": {"status": "failed"},
  "projection": {"customer_email": 1, "error_details": 1, "created_at": 1},
  "explanation": "Finds all failed notifications with customer email, error details, and creation date"
}
```

**API Location:** [app/api/routes.py](app/api/routes.py#L25-L81)

---

### 2. `/api/v1/aggregation` - Aggregation Pipeline Generation
**Request from Frontend:**
```json
{
  "user_input": "Count notifications by status",
  "execute": true
}
```

**Sent to AI:**
- System prompt with schema
- User input: "Count notifications by status"

**AI Returns:**
```json
{
  "query_type": "aggregation",
  "query": [
    {"$group": {"_id": "$status", "count": {"$sum": 1}}},
    {"$sort": {"count": -1}}
  ],
  "explanation": "Groups notifications by status and counts them"
}
```

**API Location:** [app/api/routes.py](app/api/routes.py#L84-L132)

---

### 3. `/api/v1/report` - Report Generation
**Request from Frontend:**
```json
{
  "user_input": "Daily notification summary for the last 7 days",
  "report_format": "pdf",
  "chart_type": "bar"
}
```

**Sent to AI:**
- System prompt with schema
- Enhanced prompt for report generation:
  ```
  Generate a MongoDB aggregation pipeline for this report requirement: {user_input}

  The pipeline should:
  1. Include appropriate $match, $group, $sort stages
  2. Calculate relevant metrics (counts, averages, etc.)
  3. Format output suitable for reporting
  4. Include date grouping if time-based analysis is needed
  ```
- User input: "Daily notification summary for the last 7 days"

**AI Returns:**
```json
{
  "query_type": "aggregation",
  "query": [
    {"$match": {"created_at": {"$gte": {"$date": "2025-11-21T00:00:00Z"}}}},
    {"$group": {
      "_id": {"$dateToString": {"format": "%Y-%m-%d", "date": "$created_at"}},
      "count": {"$sum": 1},
      "delivered": {"$sum": {"$cond": [{"$eq": ["$status", "delivered"]}, 1, 0]}},
      "failed": {"$sum": {"$cond": [{"$eq": ["$status", "failed"]}, 1, 0]}}
    }},
    {"$sort": {"_id": 1}}
  ],
  "explanation": "Daily notification summary with counts and status breakdown"
}
```

**API Location:** [app/api/routes.py](app/api/routes.py#L135-L177)

---

## What Data is NOT Sent to AI

### ❌ Not Sent:
1. **Actual notification content** - No customer messages or notification bodies
2. **Customer PII** - No actual customer emails, phone numbers, or names
3. **Customer IDs** - No real customer identifiers
4. **Database credentials** - MongoDB connection strings stay local
5. **API keys** - No sensitive credentials
6. **Actual query results** - Results from MongoDB are NOT sent back to AI
7. **User session data** - No authentication tokens or session info

### ✅ Only Sent:
1. **Database schema structure** (field names and types)
2. **User's natural language query**
3. **MongoDB query generation instructions**

---

## Privacy & Security Considerations

### Data Minimization
- Only schema metadata is shared, not actual data
- User queries are natural language descriptions, not containing sensitive info
- Results from database are NOT sent back to AI

### Example - What Actually Gets Sent:
**User Query:** "Show failed notifications for customer C001"

**Sent to AI:**
```
System Prompt: [Contains schema with field definitions]
User Input: "Show failed notifications for customer C001"
```

**NOT Sent to AI:**
- The actual notification records
- Customer C001's real name, email, or phone
- Actual error messages or notification content

### Data Processing Location
- **AI Processing:** Google Gemini API (cloud-based)
- **Database Queries:** Local MongoDB (your infrastructure)
- **Data Storage:** Local MongoDB only

### Logging
The application logs:
- Truncated user input (first 50 characters) - See [app/services/ai_service.py](app/services/ai_service.py#L98)
- Query generation success/failure
- NOT logging: Full queries or results

---

## API Request Example

### Complete Request to Gemini AI:

```json
{
  "messages": [
    {
      "role": "system",
      "content": "You are a MongoDB query generator expert. Your task is to convert natural language queries into valid MongoDB Query Language (MQL) queries.\n\nYou have access to a database with the following schema:\n\nCollection: customer_notifications\nFields:\n{\n  \"_id\": \"ObjectId - Unique identifier\",\n  \"customer_id\": \"string - Customer unique identifier\",\n  ...\n}\n\nAvailable indexes: customer_id, status, channel, notification_type, created_at, sent_at\n\n[Full instructions and rules...]"
    },
    {
      "role": "user",
      "content": "Convert this to a MongoDB query: Find all failed notifications"
    }
  ],
  "temperature": 0,
  "model": "gemini-2.0-flash"
}
```

---

## Code References

| Component | File Location | Lines |
|-----------|---------------|-------|
| AI Service Configuration | [app/services/ai_service.py](app/services/ai_service.py) | 14-19 |
| System Prompt Generation | [app/services/ai_service.py](app/services/ai_service.py) | 22-72 |
| Query Endpoint | [app/api/routes.py](app/api/routes.py) | 25-81 |
| Aggregation Endpoint | [app/api/routes.py](app/api/routes.py) | 84-132 |
| Report Endpoint | [app/api/routes.py](app/api/routes.py) | 135-177 |
| Schema Definition | [app/models/schemas.py](app/models/schemas.py) | 76-112 |
| Configuration | [app/config.py](app/config.py) | 9-10 |

---

## Summary

**Data Sent to AI:**
- Database schema structure (metadata only)
- User's natural language query
- MongoDB query generation rules and examples

**Data NOT Sent to AI:**
- Actual customer data
- Query results
- Sensitive credentials
- PII (Personally Identifiable Information)

The AI service is used ONLY for translating natural language to MongoDB queries. All actual data retrieval and processing happens locally on your infrastructure.
