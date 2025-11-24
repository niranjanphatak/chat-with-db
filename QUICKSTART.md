# 🚀 Credit Card Statement Analyzer - Quick Start

Get up and running in 5 minutes!

## Prerequisites Check ✅

```bash
# 1. Python installed?
python3 --version  # Should show 3.8+

# 2. MongoDB running?
# Using Docker (recommended):
docker run -d -p 27017:27017 --name mongodb mongo:latest

# 3. Dependencies installed?
pip install -r requirements.txt
```

## Step-by-Step Setup 📋

### 1️⃣ Configure OpenAI API Key

Edit `.env` file:
```bash
OPENAI_API_KEY=sk-your-actual-key-here  # ← Add your real key!
```

### 2️⃣ Seed Sample Data

```bash
python3 scripts/seed_credit_card_data.py
```

Expected output:
```
✅ Successfully inserted 500 transactions!
```

### 3️⃣ Start the Application

```bash
python3 -m app.main
```

Wait for:
```
INFO:     Uvicorn running on http://0.0.0.0:8000
```

### 4️⃣ Open Your Browser

Go to: **http://localhost:8000/credit-card**

## Try It Out! 🎯

### Example 1: Search Transactions
1. Click "Transaction Search" tab
2. Type: `Show all dining transactions over $50`
3. Check "Generate AI Summary"
4. Click "Search Transactions"

**Result**: See matching transactions + AI summary!

### Example 2: Analyze Spending
1. Click "Smart Analysis" tab
2. Type: `Analyze my spending for last month`
3. Click "Generate Analysis"

**Result**: Complete spending analysis with insights!

### Example 3: View Dashboard
1. Click "Dashboard" tab
2. See automatic overview of all spending

## Key Features 💡

| Feature | What It Does |
|---------|-------------|
| 🔍 Natural Language Search | "Show dining over $50" → MongoDB query |
| 🧠 AI Analysis | Get spending insights from aggregated data |
| 📊 Dashboard | Visual overview of transactions |
| 🔒 Privacy-First | NO raw data sent to AI, only schema & stats |

## Common Issues & Fixes 🔧

### Issue: "Connection refused"
```bash
# MongoDB not running - start it:
docker start mongodb
# or
docker run -d -p 27017:27017 --name mongodb mongo:latest
```

### Issue: "Authentication failed"
```bash
# Invalid OpenAI key - check .env:
cat .env | grep OPENAI_API_KEY
# Get a key from: https://platform.openai.com/api-keys
```

### Issue: "No transactions found"
```bash
# Re-seed the database:
python3 scripts/seed_credit_card_data.py
```

## What Makes This Special? ⭐

### Privacy-Focused Design
- ✅ Only **database schema** sent to AI for query generation
- ✅ Only **aggregated statistics** sent for summarization
- ❌ **NO individual transactions** ever sent to AI
- ❌ **NO merchant names or personal data** shared

### AI-Powered
- ChatOpenAI converts natural language to MongoDB queries
- Intelligent summarization of spending patterns
- Key insights and recommendations

### Production-Ready
- FastAPI backend with error handling
- MongoDB with optimized indexes
- Modern, responsive UI
- Comprehensive documentation

## Project Structure 📁

```
chat-with-db/
├── credit_card_app/           ← NEW Credit Card Analyzer
│   ├── models/                ← Schema definitions
│   ├── services/              ← AI & database services
│   ├── api/                   ← REST API routes
│   └── static/                ← Web UI (HTML/CSS/JS)
├── scripts/
│   └── seed_credit_card_data.py  ← Generate sample data
├── app/main.py                ← Main application (updated)
└── requirements.txt           ← Dependencies (unchanged)
```

## API Endpoints 🔌

Access at: http://localhost:8000/credit-card/api

| Endpoint | What It Does |
|----------|-------------|
| `POST /query` | Search transactions |
| `POST /analyze` | Generate spending analysis |
| `GET /stats` | Get statistics |
| `GET /health` | Check service health |

Full docs: http://localhost:8000/docs

## Sample Queries 💬

### Transaction Searches
- "Show all dining transactions over $50"
- "Find transactions at Amazon"
- "Get all refunds from last month"
- "Show travel expenses this quarter"
- "List pending transactions"

### Analyses
- "Analyze my spending for last month"
- "What are my top spending categories?"
- "Show me dining expense patterns"
- "Compare spending across categories"

## Next Steps 🎓

1. ✅ **Try Example Queries** - Click examples in each tab
2. ✅ **Explore AI Summaries** - Enable summary generation
3. ✅ **Review Generated Queries** - See the MongoDB queries
4. ✅ **Check the Code** - Understand how it works
5. ✅ **Read Full Docs** - See [CREDIT_CARD_README.md](CREDIT_CARD_README.md)

## Full Documentation 📚

- **[CREDIT_CARD_README.md](CREDIT_CARD_README.md)** - Complete features & architecture
- **[SETUP_GUIDE.md](SETUP_GUIDE.md)** - Detailed setup instructions
- **[CREDIT_CARD_SUMMARY.md](CREDIT_CARD_SUMMARY.md)** - Project overview

## Need Help? 🆘

1. Check logs in terminal where you ran `python3 -m app.main`
2. Review [SETUP_GUIDE.md](SETUP_GUIDE.md) troubleshooting
3. Verify all prerequisites are met
4. Check MongoDB connection
5. Verify OpenAI API key

## Technology Stack 🛠️

- **Backend**: FastAPI + PyMongo + LangChain + ChatOpenAI
- **Frontend**: HTML5 + CSS3 + Vanilla JavaScript
- **Database**: MongoDB
- **AI**: OpenAI GPT-4o

---

**Ready to analyze credit card statements with AI!** 💳✨

**Start here**: http://localhost:8000/credit-card
