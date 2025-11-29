# Quick Start Guide - Multi-Collection Notification System V2

## 🎉 What's New

The notification system now uses a **multi-collection architecture**:
- **1 Primary Collection**: `notification_events` (tracks events)
- **4 Channel Collections**: `email_notifications`, `sms_notifications`, `push_notifications`, `inapp_notifications`
- **Linked by**: `event_tracking_id`

## 🚀 Quick Start (5 Minutes)

### Step 1: Seed Sample Data

```bash
cd /Users/niranjan/python_projects/mongo-query-ai
python scripts/seed_multi_collection_notifications.py
```

**Output:**
```
🌱 Seeding multi-collection notification system...
✅ Collections cleared
📑 Creating indexes...
📧 Generating 2000 notification events...
  ✓ Created 200 events...
  ✓ Created 400 events...
  ...
  ✓ Created 2000 events...
✅ Data seeding complete!
📊 Summary:
  - Notification Events: 2000
  - Email Notifications: ~1400
  - SMS Notifications: ~1100
  - Push Notifications: ~1300
  - In-App Notifications: ~1200
```

### Step 2: Start the Application

```bash
# If not already running
python -m uvicorn app.main:app --reload
```

### Step 3: Test the API

#### Check Health
```bash
curl http://localhost:8000/api/v2/health
```

**Response:**
```json
{
  "status": "healthy",
  "database": "connected",
  "version": "2.0-multi-collection",
  "collections": {
    "notification_events": 2000,
    "email_notifications": 1400,
    "sms_notifications": 1100,
    "push_notifications": 1300,
    "inapp_notifications": 1200
  }
}
```

#### Get Dashboard Statistics
```bash
curl http://localhost:8000/api/v2/dashboard
```

#### Query with Natural Language
```bash
curl -X POST http://localhost:8000/api/v2/query \
  -H "Content-Type: application/json" \
  -d '{
    "user_input": "Show failed email notifications",
    "execute": true
  }'
```

**Response:**
```json
{
  "user_input": "Show failed email notifications",
  "target_collection": "email_notifications",
  "generated_mql": {
    "status": "failed"
  },
  "explanation": "Finds all failed email notifications",
  "involves_multiple_collections": false,
  "results": [...],
  "count": 15,
  "execution_time_ms": 12.5
}
```

---

## 📖 Example Queries

### 1. Simple Event Queries

```bash
# All accepted events
curl -X POST http://localhost:8000/api/v2/query \
  -H "Content-Type: application/json" \
  -d '{"user_input": "Show all accepted notification events", "execute": true}'

# Events from last 7 days
curl -X POST http://localhost:8000/api/v2/query \
  -H "Content-Type: application/json" \
  -d '{"user_input": "Show events from last 7 days", "execute": true}'

# High priority events
curl -X POST http://localhost:8000/api/v2/query \
  -H "Content-Type: application/json" \
  -d '{"user_input": "Show high priority events", "execute": true}'
```

### 2. Channel-Specific Queries

```bash
# Failed emails
curl -X POST http://localhost:8000/api/v2/query \
  -H "Content-Type: application/json" \
  -d '{"user_input": "Show failed email notifications", "execute": true}'

# Delivered SMS
curl -X POST http://localhost:8000/api/v2/query \
  -H "Content-Type: application/json" \
  -d '{"user_input": "Show delivered SMS notifications", "execute": true}'

# Read push notifications
curl -X POST http://localhost:8000/api/v2/query \
  -H "Content-Type: application/json" \
  -d '{"user_input": "Show read push notifications", "execute": true}'

# Pending in-app notifications
curl -X POST http://localhost:8000/api/v2/query \
  -H "Content-Type: application/json" \
  -d '{"user_input": "Show pending in-app notifications", "execute": true}'
```

### 3. Cross-Collection Queries

```bash
# Events with email status
curl -X POST http://localhost:8000/api/v2/query \
  -H "Content-Type: application/json" \
  -d '{"user_input": "Show events with their email delivery status", "execute": true}'

# Events where email delivered but SMS failed
curl -X POST http://localhost:8000/api/v2/query \
  -H "Content-Type: application/json" \
  -d '{"user_input": "Find events where email was delivered but SMS failed", "execute": true}'

# Count delivered by channel
curl -X POST http://localhost:8000/api/v2/query \
  -H "Content-Type: application/json" \
  -d '{"user_input": "Count delivered notifications by channel", "execute": true}'
```

### 4. Analytics Queries

```bash
# Delivery rate by channel
curl -X POST http://localhost:8000/api/v2/query \
  -H "Content-Type: application/json" \
  -d '{"user_input": "Show delivery rate for each channel", "execute": true}'

# Multi-channel events
curl -X POST http://localhost:8000/api/v2/query \
  -H "Content-Type: application/json" \
  -d '{"user_input": "Show events sent through multiple channels", "execute": true}'

# Failed notifications analysis
curl -X POST http://localhost:8000/api/v2/query \
  -H "Content-Type: application/json" \
  -d '{"user_input": "Count failed notifications by channel", "execute": true}'
```

### 5. Event Name Queries (NEW!)

```bash
# Show all ORDER_SHIPPED events
curl -X POST http://localhost:8000/api/v2/query \
  -H "Content-Type: application/json" \
  -d '{"user_input": "Show all ORDER_SHIPPED events", "execute": true}'

# Count events by event name
curl -X POST http://localhost:8000/api/v2/query \
  -H "Content-Type: application/json" \
  -d '{"user_input": "Count notifications by event name", "execute": true}'

# Show delivery stats for specific event type
curl -X POST http://localhost:8000/api/v2/query \
  -H "Content-Type: application/json" \
  -d '{"user_input": "Show delivery stats for PAYMENT_RECEIVED events", "execute": true}'

# Get event name statistics (direct endpoint)
curl http://localhost:8000/api/v2/stats/event-name

# Get channel breakdown for specific event name
curl http://localhost:8000/api/v2/stats/event-name/ORDER_PLACED

# Get all events for a specific event name
curl http://localhost:8000/api/v2/events/by-event-name/PAYMENT_RECEIVED
```

---

## 🔍 Explore Specific Events

### Get Event Details
```bash
# Get complete event with all channel statuses
curl http://localhost:8000/api/v2/event/EVT-20241128-000001
```

**Response:**
```json
{
  "event": {
    "event_tracking_id": "EVT-20241128-000001",
    "customer_id": "C001",
    "customer_name": "John Doe",
    "status": "processed",
    "channels": ["email", "sms", "push"]
  },
  "email": {
    "event_tracking_id": "EVT-20241128-000001",
    "status": "delivered",
    "sent_at": "2024-11-28T10:00:10Z",
    "delivered_at": "2024-11-28T10:00:15Z"
  },
  "sms": {
    "event_tracking_id": "EVT-20241128-000001",
    "status": "sent",
    "sent_at": "2024-11-28T10:01:00Z"
  },
  "push": {
    "event_tracking_id": "EVT-20241128-000001",
    "status": "delivered",
    "sent_at": "2024-11-28T10:00:05Z",
    "delivered_at": "2024-11-28T10:00:10Z"
  },
  "inapp": null
}
```

### Get Events with Channels (Paginated)
```bash
curl "http://localhost:8000/api/v2/events/with-channels?limit=10&skip=0"
```

---

## 📊 Event Name Statistics (NEW!)

### Get All Event Name Stats
```bash
curl http://localhost:8000/api/v2/stats/event-name
```

**Response:**
```json
[
  {
    "_id": "ORDER_PLACED",
    "event_name": "ORDER_PLACED",
    "count": 45,
    "accepted": 20,
    "processed": 25
  },
  {
    "_id": "PAYMENT_RECEIVED",
    "event_name": "PAYMENT_RECEIVED",
    "count": 38,
    "accepted": 15,
    "processed": 23
  },
  ...
]
```

### Get Channel Breakdown for Specific Event
```bash
curl http://localhost:8000/api/v2/stats/event-name/ORDER_SHIPPED
```

**Response:**
```json
{
  "_id": "ORDER_SHIPPED",
  "total_events": 32,
  "email_delivered": 28,
  "email_failed": 2,
  "sms_delivered": 25,
  "sms_failed": 5,
  "push_delivered": 30,
  "push_failed": 1,
  "inapp_read": 20,
  "inapp_failed": 0
}
```

---

## 📊 Channel Statistics

### Email Channel Stats
```bash
curl http://localhost:8000/api/v2/stats/channel/email
```

**Response:**
```json
{
  "channel": "email",
  "total": 350,
  "by_status": [
    {"_id": "delivered", "count": 180},
    {"_id": "sent", "count": 85},
    {"_id": "failed", "count": 45},
    {"_id": "pending", "count": 30},
    {"_id": "read", "count": 10}
  ],
  "recent_activity": [
    {"_id": "2024-11-28", "count": 120},
    {"_id": "2024-11-27", "count": 95},
    ...
  ],
  "delivery_metrics": {
    "rate": 77.14,
    "total": 350,
    "delivered": 270
  }
}
```

### All Channels
```bash
# Email
curl http://localhost:8000/api/v2/stats/channel/email

# SMS
curl http://localhost:8000/api/v2/stats/channel/sms

# Push
curl http://localhost:8000/api/v2/stats/channel/push

# In-App
curl http://localhost:8000/api/v2/stats/channel/inapp
```

---

## 🎯 Common Use Cases

### 1. Find Failed Deliveries
```bash
curl -X POST http://localhost:8000/api/v2/query \
  -H "Content-Type: application/json" \
  -d '{"user_input": "Show all failed notifications across all channels", "execute": true}'
```

### 2. Track Multi-Channel Campaign
```bash
curl -X POST http://localhost:8000/api/v2/query \
  -H "Content-Type: application/json" \
  -d '{"user_input": "Show events using email and SMS channels", "execute": true}'
```

### 3. Monitor Real-Time Delivery
```bash
curl -X POST http://localhost:8000/api/v2/query \
  -H "Content-Type: application/json" \
  -d '{"user_input": "Show events processed in the last hour", "execute": true}'
```

### 4. Analyze Customer Engagement
```bash
curl -X POST http://localhost:8000/api/v2/query \
  -H "Content-Type: application/json" \
  -d '{"user_input": "Count read notifications by channel", "execute": true}'
```

### 5. Channel Performance Comparison
```bash
curl http://localhost:8000/api/v2/dashboard
# Then compare delivery_rate across channels
```

### 6. Event Name Analytics
```bash
# Get distribution of events by event name
curl http://localhost:8000/api/v2/stats/event-name

# Analyze channel performance for specific event types
curl http://localhost:8000/api/v2/stats/event-name/ORDER_PLACED
curl http://localhost:8000/api/v2/stats/event-name/PAYMENT_RECEIVED
curl http://localhost:8000/api/v2/stats/event-name/SECURITY_ALERT
```

---

## 🌐 API Documentation

Visit the interactive API documentation:
```
http://localhost:8000/docs
```

Look for the **"Notifications V2 - Multi-Collection"** section.

---

## 📚 Full Documentation

- **Architecture**: [MULTI_COLLECTION_ARCHITECTURE.md](MULTI_COLLECTION_ARCHITECTURE.md)
- **API Reference**: http://localhost:8000/docs
- **Schema**: http://localhost:8000/api/v2/schema

---

## 🔄 Comparison: V1 vs V2

### V1 (Single Collection)
```javascript
// Everything in one collection
{
  customer_id: "C001",
  channel: "email",
  status: "delivered",
  // All fields mixed together
}
```

**Query:**
```
db.customer_notifications.find({
  channel: "email",
  status: "failed"
})
```

### V2 (Multi-Collection)
```javascript
// Primary collection
{
  event_tracking_id: "EVT-001",
  customer_id: "C001",
  channels: ["email", "sms"],
  status: "processed"
}

// Email collection
{
  event_tracking_id: "EVT-001",
  status: "delivered",
  sent_at: "..."
}

// SMS collection
{
  event_tracking_id: "EVT-001",
  status: "failed",
  error_details: "..."
}
```

**Query:**
```javascript
// Simple: Just email failures
db.email_notifications.find({ status: "failed" })

// Complex: Events with mixed channel results
db.notification_events.aggregate([
  { $lookup: { from: "email_notifications", ... } },
  { $lookup: { from: "sms_notifications", ... } },
  { $match: {
    "email.status": "delivered",
    "sms.status": "failed"
  }}
])
```

---

## ✨ Benefits of V2

1. **Better Scalability** - Each channel can scale independently
2. **Clearer Structure** - Separation of event tracking vs. channel delivery
3. **Flexible Queries** - Target specific channels or join across all
4. **Performance** - Smaller collections, better indexes
5. **Analytics** - Easy cross-channel analysis

---

## 🎓 Next Steps

1. **Explore the Schema**:
   ```bash
   curl http://localhost:8000/api/v2/schema | jq
   ```

2. **Read Full Documentation**:
   - Open [MULTI_COLLECTION_ARCHITECTURE.md](MULTI_COLLECTION_ARCHITECTURE.md)

3. **Try Natural Language Queries**:
   - "Show events where all channels were delivered"
   - "Find customers with failed push notifications"
   - "Count notifications by type and channel"

4. **Build Dashboards**:
   - Use `/api/v2/dashboard` for overview
   - Use `/api/v2/stats/channel/{name}` for channel-specific metrics
   - Create visualizations from the data

5. **Integrate into Your Application**:
   - Use V2 API endpoints
   - Link events across channels
   - Track multi-channel campaigns

---

**You're all set! The multi-collection system is ready to use.** 🚀

For questions or issues, check the full documentation or API docs.
