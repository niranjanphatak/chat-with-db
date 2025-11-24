# Credit Card Statement Analyzer 💳

An AI-powered credit card transaction analyzer that converts natural language queries to MongoDB queries and generates intelligent summaries of your spending patterns.

## 🌟 Key Features

### 1. Natural Language Queries
Convert plain English to MongoDB queries without knowing MQL:
- "Show all dining transactions over $50"
- "Find transactions at Amazon in the last month"
- "Get all refunds from last week"

### 2. Smart Analysis with AI Summarization
Get intelligent insights about your spending:
- AI-powered summaries of transaction patterns
- Category-wise breakdown
- Top merchant analysis
- **Privacy-First**: Only aggregated statistics are sent to AI, never individual transaction details

### 3. Interactive Dashboard
Visual overview of your credit card activity:
- Total spending and transaction count
- Category breakdown
- Monthly trends
- Transaction type analysis

### 4. Real-time Query Execution
Execute generated MongoDB queries and see results instantly in a beautiful table format.

## 🔒 Privacy & Security

**IMPORTANT**: This application is designed with privacy in mind:
- ✅ Only database **schema** is sent to AI for query generation
- ✅ Only **aggregated statistics** (totals, counts, averages) are sent for summarization
- ❌ **NO individual transaction data** is ever sent to the AI model
- ❌ **NO merchant names, amounts, or personal details** are shared with AI

## 🚀 Quick Start

### 1. Prerequisites
- Python 3.8+
- MongoDB running on localhost:27017
- OpenAI API key

### 2. Installation

Already included in the main project. No additional installation needed!

### 3. Configuration

Your existing `.env` file already has everything needed:
```env
MONGODB_URI=mongodb://localhost:27017
MONGODB_DATABASE=notifications_db
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_MODEL=gpt-4o
```

### 4. Seed Sample Data

Generate realistic credit card transactions:
```bash
python scripts/seed_credit_card_data.py
```

This creates 500 sample transactions across various categories:
- Groceries, Dining, Shopping, Travel
- Entertainment, Utilities, Gas
- Healthcare, Education, and more

To generate a custom number of transactions:
```bash
python scripts/seed_credit_card_data.py 1000
```

### 5. Start the Application

```bash
python -m app.main
```

### 6. Access the UI

Open your browser to:
```
http://localhost:8000/credit-card
```

## 📱 How to Use

### Transaction Search Tab

1. **Enter a natural language query:**
   - Type what you're looking for in plain English
   - Example: "Show all dining transactions over $50"

2. **Enable AI Summary (optional):**
   - Check the "Generate AI Summary" box for insights
   - AI will analyze patterns in your results

3. **View Results:**
   - See the generated MongoDB query
   - View matching transactions in a table
   - Read AI-generated summary and insights

### Smart Analysis Tab

1. **Request an analysis:**
   - Ask about spending patterns
   - Example: "Analyze my spending for last month"

2. **Get Comprehensive Insights:**
   - AI-generated summary of spending patterns
   - Total transaction count and amount
   - Key insights about your spending
   - Detailed statistics by category and merchant

### Dashboard Tab

View your complete credit card overview:
- Total transactions and spending
- Category breakdown with amounts
- Monthly spending trends
- Transaction type distribution

Click "Refresh Dashboard" to update statistics.

## 💡 Example Queries

### Transaction Searches
```
Show all dining transactions over $50
Find transactions at Amazon
Show me all refunds
Get travel expenses from last quarter
Find pending transactions
Show grocery purchases in November
List all international transactions
```

### Smart Analyses
```
Analyze my spending for last month
Summary of all dining expenses
What are my top spending categories?
Show me my travel spending patterns
Analyze shopping expenses this year
Compare spending across different categories
```

## 🏗️ Architecture

### Backend Components

**1. Schema Definition** ([credit_card_schema.py](credit_card_app/models/credit_card_schema.py))
- Pydantic models for transaction data
- Schema definition for MongoDB
- API request/response models

**2. AI Query Service** ([ai_query_service.py](credit_card_app/services/ai_query_service.py))
- Converts natural language to MongoDB queries
- Uses ChatOpenAI via LangChain
- Only sends schema to AI, never data

**3. Summarization Service** ([summarization_service.py](credit_card_app/services/summarization_service.py))
- Generates intelligent summaries
- Provides spending insights
- Only processes aggregated statistics

**4. Database Service** ([database_service.py](credit_card_app/services/database_service.py))
- Executes MongoDB queries
- Provides aggregation functions
- Returns only statistics for AI analysis

**5. API Routes** ([credit_card_routes.py](credit_card_app/api/credit_card_routes.py))
- `/query` - Search transactions
- `/analyze` - Generate analysis
- `/stats` - Get statistics
- `/schema` - View schema
- `/health` - Health check

### Frontend Components

**1. HTML UI** ([index.html](credit_card_app/static/index.html))
- Three main tabs: Search, Analysis, Dashboard
- Click-to-use example queries
- Responsive design

**2. Modern CSS** ([style.css](credit_card_app/static/css/style.css))
- Purple theme (credit card aesthetic)
- Card-based layout
- Mobile-responsive

**3. Interactive JavaScript** ([app.js](credit_card_app/static/js/app.js))
- API communication
- Dynamic result rendering
- Real-time updates

## 📊 Sample Data Structure

Each transaction includes:
```json
{
  "transaction_id": "TXN001234",
  "card_number": "****1234",
  "cardholder_name": "John Doe",
  "transaction_date": "2024-11-15T14:30:00Z",
  "merchant_name": "Amazon.com",
  "category": "shopping",
  "amount": 45.99,
  "transaction_type": "purchase",
  "status": "posted",
  "description": "Online purchase",
  "location": {"city": "San Francisco", "state": "CA"},
  "rewards_earned": 0.46
}
```

### Categories
- Groceries, Dining, Shopping
- Travel, Entertainment, Utilities
- Gas, Healthcare, Education, Other

### Transaction Types
- Purchase, Refund, Payment
- Fee, Interest, Cashback

## 🔧 API Endpoints

### Query Transactions
```bash
POST /credit-card/api/query
{
  "user_input": "Show dining over $50",
  "execute": true,
  "summarize": true
}
```

### Analyze Spending
```bash
POST /credit-card/api/analyze
{
  "user_input": "Analyze my spending for last month"
}
```

### Get Statistics
```bash
GET /credit-card/api/stats
```

### View Schema
```bash
GET /credit-card/api/schema
```

## 🎯 Use Cases

1. **Monthly Budget Review**
   - Analyze spending by category
   - Identify high-spending areas
   - Track budget adherence

2. **Expense Reporting**
   - Find business travel expenses
   - Generate category summaries
   - Export transaction lists

3. **Fraud Detection**
   - Search for unusual transactions
   - Review international charges
   - Check pending transactions

4. **Rewards Optimization**
   - Track rewards earned
   - Analyze category spending
   - Optimize card usage

## 🔐 Security Best Practices

1. **Never commit your `.env` file** with real API keys
2. **Use environment variables** for sensitive data
3. **Mask credit card numbers** (only last 4 digits)
4. **Review AI prompts** - they only contain schema, not data
5. **Implement authentication** for production use

## 🚀 Future Enhancements

Potential features to add:
- [ ] Multi-user support with authentication
- [ ] Budget setting and alerts
- [ ] Spending predictions
- [ ] Fraud detection alerts
- [ ] Export to CSV/PDF
- [ ] Mobile app
- [ ] Email notifications
- [ ] Custom category rules

## 📝 Technical Details

**MongoDB Indexes:**
- transaction_date
- category
- merchant_name
- card_number
- status

**AI Models Supported:**
- GPT-4o (default)
- GPT-4
- GPT-3.5-turbo

**Performance:**
- Typical query: < 100ms
- AI query generation: 1-3s
- Summarization: 2-4s

## 🐛 Troubleshooting

**Issue**: UI shows "Unhealthy" status
- Check MongoDB is running
- Verify OPENAI_API_KEY in .env

**Issue**: No transactions found
- Run the seed script: `python scripts/seed_credit_card_data.py`

**Issue**: AI queries fail
- Verify OpenAI API key is valid
- Check API has credits
- Review logs for errors

## 📚 Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [MongoDB Documentation](https://docs.mongodb.com/)
- [LangChain Documentation](https://python.langchain.com/)
- [OpenAI API Documentation](https://platform.openai.com/docs)

## 🤝 Contributing

This is part of the MongoDB Query AI platform. To add features:
1. Add new routes in `credit_card_app/api/`
2. Extend services in `credit_card_app/services/`
3. Update UI in `credit_card_app/static/`

## 📄 License

Part of the MongoDB Query AI project.

---

**Built with ChatOpenAI, FastAPI, MongoDB, and LangChain** 🚀
