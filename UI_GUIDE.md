# MongoDB Query AI - Web UI Guide

## Overview
A beautiful, intuitive web interface for MongoDB Query AI that allows you to convert natural language to MongoDB queries without any coding knowledge.

## Features

### 1. Query Builder Tab
- Convert natural language to MongoDB find queries
- View generated MQL (MongoDB Query Language)
- Execute queries directly and see results in a table
- Click example queries to get started quickly

### 2. Aggregation Tab
- Generate complex MongoDB aggregation pipelines
- View the generated pipeline stages
- Execute aggregations and visualize results
- Perfect for analytics and reporting

### 3. Reports Tab
- Generate reports from natural language descriptions
- Export in multiple formats: JSON, CSV, or PDF
- Reports are saved on the server for download

### 4. Statistics Tab
- View real-time database statistics
- See notification counts by status and channel
- View the database schema
- Monitor total records

## Getting Started

### 1. Start the Application

```bash
# Make sure MongoDB is running
docker run -d -p 27017:27017 --name mongodb mongo:latest

# Start the FastAPI server
python -m app.main
```

### 2. Access the Web UI

Open your browser and navigate to:
```
http://localhost:8000
```

The UI will automatically check the API and database status.

### 3. Using the Interface

#### Query Builder
1. Type a natural language query like:
   - "Find all failed email notifications"
   - "Show me notifications sent in the last 7 days"
   - "Get all pending SMS notifications with high priority"

2. Click **"Generate Query"** to see the MongoDB query without executing it
   - OR -
   Click **"Generate & Execute"** to run the query immediately

3. View results:
   - See the generated MongoDB query
   - Read the AI's explanation
   - View results in a formatted table
   - See execution time and result count

#### Aggregation Pipeline
1. Describe your aggregation:
   - "Count notifications by status"
   - "Group notifications by channel and show counts"
   - "Top 10 customers by notification count"

2. Generate and optionally execute the pipeline

3. View the aggregation stages and results

#### Reports
1. Describe the report you need:
   - "Daily notification summary for the last 7 days"
   - "Channel performance report showing delivery rates"

2. Select format (JSON, CSV, or PDF)

3. Click **"Generate Report"**

4. The report will be saved on the server (check the file path shown)

#### Statistics
1. Click the **Statistics** tab
2. View:
   - Total notification count
   - Breakdown by status (delivered, failed, pending, etc.)
   - Breakdown by channel (email, sms, push)
3. Click **"View Schema"** to see the database schema

## Tips & Tricks

### Keyboard Shortcuts
- Press **Ctrl+Enter** (or **Cmd+Enter** on Mac) in any textarea to execute the query

### Click Examples
- Click any example query to automatically fill it in the input box
- Great for learning what kinds of queries you can ask

### Status Indicators
- **Green** status = Everything working
- **Red** status = Connection issues

### Query Examples by Type

**Simple Filters:**
- "Find notifications for customer C001"
- "Show all failed notifications"
- "Get pending SMS messages"

**Date-Based Queries:**
- "Find notifications from last week"
- "Show notifications sent in the last 24 hours"
- "Get notifications created in November 2024"

**Complex Filters:**
- "Find failed email notifications with high priority"
- "Show pending SMS for customer C001 with priority 1"

**Aggregations:**
- "Count notifications by status"
- "Average delivery time by channel"
- "Top 5 customers with most notifications"
- "Success rate by notification type"

## Troubleshooting

### UI Won't Load
- Check that the FastAPI server is running
- Verify you're accessing http://localhost:8000
- Check browser console for errors

### "API Unhealthy" Status
- Ensure MongoDB is running
- Check your `.env` file has correct `MONGODB_URI`
- Verify OpenAI API key is set

### Queries Failing
- Check the error toast message (top-right)
- Verify your OpenAI API key is valid and has credits
- Check the API health status at the top

### No Results Showing
- Make sure you seeded the database with sample data
- Run: `python scripts/seed_data.py`

## Architecture

### Frontend
- **HTML5** - Structure
- **CSS3** - Modern, responsive styling
- **Vanilla JavaScript** - No frameworks, fast and lightweight
- **Fetch API** - For backend communication

### Backend Integration
- All API calls go to `/api/v1/*` endpoints
- Real-time status checking
- Error handling with user-friendly messages
- Loading indicators for better UX

### Features
- **Responsive Design** - Works on desktop, tablet, and mobile
- **Real-time Validation** - Immediate feedback
- **Toast Notifications** - Success and error messages
- **Tab Navigation** - Organized interface
- **Example Queries** - Interactive learning
- **Dark Code Blocks** - Easy to read generated queries

## Browser Support

Tested and working on:
- Chrome 90+
- Firefox 88+
- Safari 14+
- Edge 90+

## Next Steps

1. Try the example queries in each tab
2. Experiment with your own natural language queries
3. View the generated MongoDB queries to learn MQL
4. Generate reports to analyze your data
5. Check the `/docs` endpoint for API documentation

## Support

- For API documentation: http://localhost:8000/docs
- For ReDoc: http://localhost:8000/redoc
- For API info: http://localhost:8000/api

Enjoy using MongoDB Query AI!
