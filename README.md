# MongoDB Query AI

A Python application that converts natural language to MongoDB queries using AI and generates reports for customer notifications.

## Features

- **Natural Language to MQL**: Convert plain English queries to MongoDB Query Language
- **Query Execution**: Execute generated queries and return results
- **Aggregation Pipelines**: Generate complex aggregation pipelines from descriptions
- **Report Generation**: Create reports in JSON, CSV, or PDF formats
- **RESTful API**: FastAPI-based endpoints for integration

## Installation

1. **Clone and setup environment**:
```bash
cd chat-with-db
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

2. **Configure environment**:
```bash
cp .env.example .env
# Edit .env with your settings
```

3. **Set your OpenAI API key** in `.env`:
```
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_MODEL=gpt-4o  # or gpt-4, gpt-3.5-turbo
```

4. **Start MongoDB** (if not running):
```bash
# Using Docker
docker run -d -p 27017:27017 --name mongodb mongo:latest

# Or install MongoDB locally
```

5. **Seed sample data**:
```bash
python scripts/seed_data.py
```

6. **Run the application**:
```bash
python -m app.main
# Or
uvicorn app.main:app --reload
```

## API Endpoints

### Generate and Execute Query
**POST** `/api/v1/query`

Convert natural language to MongoDB query and execute it.

```bash
curl -X POST "http://localhost:8000/api/v1/query" \
  -H "Content-Type: application/json" \
  -d '{
    "user_input": "Find all failed email notifications from last week",
    "execute": true
  }'
```

### Generate Aggregation Pipeline
**POST** `/api/v1/aggregation`

Generate and execute aggregation pipelines.

```bash
curl -X POST "http://localhost:8000/api/v1/aggregation" \
  -H "Content-Type: application/json" \
  -d '{
    "user_input": "Count notifications by status and channel",
    "execute": true
  }'
```

### Generate Report
**POST** `/api/v1/report`

Generate reports in various formats.

```bash
curl -X POST "http://localhost:8000/api/v1/report" \
  -H "Content-Type: application/json" \
  -d '{
    "user_input": "Daily notification summary for the last 7 days",
    "report_format": "pdf"
  }'
```

### Get Schema
**GET** `/api/v1/schema`

View the notification schema.

### Get Statistics
**GET** `/api/v1/stats`

Get database statistics.

### Health Check
**GET** `/api/v1/health`

Check application health.

## Example Queries

### Find Queries
- "Find all failed notifications"
- "Show me email notifications for customer C001"
- "Get notifications with priority 1 that are pending"
- "Find all promotional notifications sent in the last 24 hours"
- "Show notifications with error details containing 'bounced'"

### Aggregation Queries
- "Count notifications by status"
- "Show average delivery time by channel"
- "Top 10 customers by notification count"
- "Group notifications by type and show success rate"
- "Daily notification volume for the past month"

### Report Queries
- "Channel performance report showing delivery rates"
- "Customer engagement report by notification type"
- "Failed notifications summary with error breakdown"
- "Weekly notification trends by channel"

## Project Structure

```
chat-with-db/
├── app/
│   ├── api/
│   │   └── routes.py       # API endpoints
│   ├── models/
│   │   └── schemas.py      # Pydantic models
│   ├── services/
│   │   ├── ai_service.py   # AI query generation
│   │   ├── database.py     # MongoDB operations
│   │   └── report_service.py # Report generation
│   ├── config.py           # Configuration
│   └── main.py             # FastAPI application
├── scripts/
│   └── seed_data.py        # Sample data generator
├── reports/                # Generated reports
├── requirements.txt
├── .env.example
└── README.md
```

## API Documentation

Once running, visit:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Technology Stack

- **FastAPI**: Web framework
- **PyMongo**: MongoDB driver
- **OpenAI GPT**: AI model for query generation
- **LangChain**: AI orchestration framework
- **ReportLab**: PDF generation
- **Pandas**: Data manipulation
