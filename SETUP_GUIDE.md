# Complete Setup Guide - Credit Card Statement Analyzer

## 🚀 Quick Start Instructions

Follow these steps to get the Credit Card Statement Analyzer up and running.

### Step 1: Verify Prerequisites

Check that you have:
```bash
# Python 3.8 or higher
python3 --version

# MongoDB (should be running)
# If using Docker:
docker ps | grep mongo

# Or start MongoDB with Docker:
docker run -d -p 27017:27017 --name mongodb mongo:latest
```

### Step 2: Install Dependencies

All dependencies are in `requirements.txt`:
```bash
pip install -r requirements.txt
```

If you get permission errors, use:
```bash
pip install --user -r requirements.txt
```

### Step 3: Configure Environment

1. Make sure your `.env` file has an OpenAI API key:
```bash
cat .env
```

Should show:
```
MONGODB_URI=mongodb://localhost:27017
MONGODB_DATABASE=notifications_db
OPENAI_API_KEY=sk-your-actual-key-here  # ← Must be a real key!
OPENAI_MODEL=gpt-4o
APP_HOST=0.0.0.0
APP_PORT=8000
DEBUG=True
```

2. If `.env` doesn't exist or needs the API key:
```bash
echo "OPENAI_API_KEY=your-key-here" >> .env
```

### Step 4: Seed Credit Card Data

Generate 100 sample transactions:
```bash
python3 scripts/seed_credit_card_data.py 100
```

Or generate 500 transactions (default):
```bash
python3 scripts/seed_credit_card_data.py
```

You should see output like:
```
🚀 Credit Card Transaction Data Seeder
============================================================
Clearing existing transactions...
Generating 100 sample transactions...
Inserting transactions into database...
✅ Successfully inserted 100 transactions!

📊 Transaction Statistics:
------------------------------------------------------------
shopping        | Count:   25 | Total: $3,456.78
dining          | Count:   20 | Total: $1,234.56
...
✨ Database seeded successfully!
```

### Step 5: Start the Application

```bash
python3 -m app.main
```

You should see:
```
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Starting up MongoDB Query AI application...
INFO:     Successfully connected to MongoDB for credit card transactions
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000
```

### Step 6: Access the Application

Open your browser to:
- **Credit Card Analyzer**: http://localhost:8000/credit-card
- **Original App**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **API Info**: http://localhost:8000/api

## 📱 Using the Credit Card Analyzer

### 1. Transaction Search

Click the "Transaction Search" tab and try:
```
Show all dining transactions over $50
```

Enable "Generate AI Summary" to get insights!

### 2. Smart Analysis

Click the "Smart Analysis" tab and try:
```
Analyze my spending for last month
```

You'll get:
- AI-generated summary
- Total statistics
- Key insights
- Detailed breakdown by category and merchant

### 3. Dashboard

Click the "Dashboard" tab to see:
- Total transactions and spending
- Category breakdown
- Monthly trends
- Transaction types

## 🔧 Troubleshooting

### MongoDB Connection Issues

**Error**: "Failed to connect to MongoDB"

**Solution**:
```bash
# Check if MongoDB is running
docker ps | grep mongo

# If not, start it:
docker run -d -p 27017:27017 --name mongodb mongo:latest

# Or restart existing container:
docker start mongodb
```

### OpenAI API Issues

**Error**: "Error generating MQL" or "Authentication failed"

**Solution**:
1. Verify your API key in `.env`:
```bash
cat .env | grep OPENAI_API_KEY
```

2. Test your API key:
```bash
curl https://api.openai.com/v1/models \
  -H "Authorization: Bearer YOUR_API_KEY"
```

3. Make sure the key has credits: https://platform.openai.com/usage

### Port Already in Use

**Error**: "Address already in use"

**Solution**:
```bash
# Find what's using port 8000
lsof -i :8000

# Kill the process
kill -9 <PID>

# Or change the port in .env
echo "APP_PORT=8001" >> .env
```

### No Transactions Found

**Error**: Search returns no results

**Solution**:
```bash
# Re-seed the database
python3 scripts/seed_credit_card_data.py 100
```

### Module Not Found Errors

**Error**: "ModuleNotFoundError: No module named 'xyz'"

**Solution**:
```bash
# Reinstall dependencies
pip install -r requirements.txt

# Or install the specific module
pip install langchain-openai
```

## 📊 Project Structure

```
chat-with-db/
├── app/                          # Original notification app
│   ├── api/routes.py
│   ├── services/
│   └── main.py                   # Main application
│
├── credit_card_app/              # New credit card analyzer
│   ├── models/
│   │   └── credit_card_schema.py # Transaction schema
│   ├── services/
│   │   ├── ai_query_service.py   # AI query generation
│   │   ├── summarization_service.py # AI summarization
│   │   └── database_service.py   # MongoDB operations
│   ├── api/
│   │   └── credit_card_routes.py # API endpoints
│   └── static/                   # Web UI
│       ├── index.html
│       ├── css/style.css
│       └── js/app.js
│
├── scripts/
│   └── seed_credit_card_data.py  # Data seeding script
│
├── requirements.txt              # Python dependencies
├── .env                          # Configuration
├── CREDIT_CARD_README.md         # Feature documentation
└── SETUP_GUIDE.md                # This file!
```

## 🎯 What Makes This Special

### Privacy-First Design
- ✅ Only schema sent to AI for query generation
- ✅ Only aggregated stats sent for summarization
- ❌ NO individual transaction data sent to AI
- ❌ NO merchant names or personal details shared

### AI-Powered Features
1. **Natural Language Queries** - ChatOpenAI converts plain English to MongoDB queries
2. **Smart Summaries** - AI analyzes spending patterns from aggregated data
3. **Intelligent Insights** - Get actionable recommendations

### Modern Tech Stack
- **Backend**: FastAPI, PyMongo, LangChain, ChatOpenAI
- **Frontend**: Vanilla JavaScript, Modern CSS
- **Database**: MongoDB with optimized indexes
- **AI**: OpenAI GPT-4o via LangChain

## 📝 Example Workflows

### Workflow 1: Monthly Budget Review
```bash
# 1. Start the app
python3 -m app.main

# 2. Open browser to http://localhost:8000/credit-card

# 3. Go to "Smart Analysis" tab

# 4. Enter: "Analyze my spending for last month"

# 5. Review:
#    - AI summary of spending patterns
#    - Category breakdown
#    - Top merchants
#    - Key insights
```

### Workflow 2: Find Specific Transactions
```bash
# 1. Go to "Transaction Search" tab

# 2. Enter: "Show all dining transactions over $50"

# 3. Enable "Generate AI Summary"

# 4. Click "Search Transactions"

# 5. Review:
#    - MongoDB query generated
#    - Matching transactions in table
#    - AI summary of results
```

### Workflow 3: Dashboard Overview
```bash
# 1. Go to "Dashboard" tab

# 2. View automatic statistics:
#    - Total spending
#    - Category breakdown
#    - Monthly trends
#    - Transaction types

# 3. Click "Refresh Dashboard" to update
```

## 🚀 Next Steps

1. **Explore Example Queries** - Click the example items in each tab
2. **Try Your Own Queries** - Ask questions in natural language
3. **Review the Code** - Check out the services to see how it works
4. **Customize** - Modify categories, add new features
5. **Deploy** - Consider deploying to production with authentication

## 📚 Additional Resources

- [Credit Card App Documentation](CREDIT_CARD_README.md)
- [API Documentation](http://localhost:8000/docs) (when running)
- [FastAPI Docs](https://fastapi.tiangolo.com/)
- [MongoDB Query Language](https://docs.mongodb.com/manual/tutorial/query-documents/)
- [LangChain Docs](https://python.langchain.com/)

## ✅ Checklist

Before asking questions, verify:
- [ ] MongoDB is running
- [ ] `.env` has valid OPENAI_API_KEY
- [ ] Dependencies installed (`pip install -r requirements.txt`)
- [ ] Data seeded (`python3 scripts/seed_credit_card_data.py`)
- [ ] App started (`python3 -m app.main`)
- [ ] Browser opened to http://localhost:8000/credit-card

---

**Questions?** Check the logs in the terminal where you ran `python3 -m app.main`

**Enjoy analyzing your credit card transactions with AI!** 💳✨
