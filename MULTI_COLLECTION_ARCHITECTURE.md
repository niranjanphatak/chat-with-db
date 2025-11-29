# Multi-Collection Notification System Architecture

## Overview

The notification system has been restructured to use a **primary collection** with **separate channel-specific collections**, all linked via `event_tracking_id`.

This architecture provides better scalability, clearer separation of concerns, and more flexible querying capabilities.

---

## Architecture Design

### Collections Structure

```
┌─────────────────────────────────────────┐
│     notification_events (PRIMARY)        │
│  ┌────────────────────────────────────┐ │
│  │ event_tracking_id: EVT-001         │ │
│  │ customer_id: C001                  │ │
│  │ notification_type: transactional   │ │
│  │ priority: 1                        │ │
│  │ channels: [email, sms, push]       │ │
│  │ status: processed                  │ │
│  │ created_at: 2024-11-28             │ │
│  └────────────────────────────────────┘ │
└─────────────────────────────────────────┘
                    │
         ┌──────────┼──────────┬──────────┐
         │          │          │          │
         ▼          ▼          ▼          ▼
┌──────────────┐ ┌──────────────┐ ┌──────────────┐ ┌──────────────┐
│ email_       │ │ sms_         │ │ push_        │ │ inapp_       │
│ notifications│ │ notifications│ │ notifications│ │ notifications│
├──────────────┤ ├──────────────┤ ├──────────────┤ ├──────────────┤
│ event_       │ │ event_       │ │ event_       │ │ event_       │
│ tracking_id  │ │ tracking_id  │ │ tracking_id  │ │ tracking_id  │
│ EVT-001      │ │ EVT-001      │ │ EVT-001      │ │ EVT-001      │
│              │ │              │ │              │ │              │
│ status:      │ │ status:      │ │ status:      │ │ status:      │
│ delivered    │ │ sent         │ │ delivered    │ │ read         │
│              │ │              │ │              │ │              │
│ sent_at:     │ │ sent_at:     │ │ sent_at:     │ │ sent_at:     │
│ 10:00 AM     │ │ 10:01 AM     │ │ 10:00 AM     │ │ 10:02 AM     │
└──────────────┘ └──────────────┘ └──────────────┘ └──────────────┘
```

---

## Collection Schemas

### 1. notification_events (PRIMARY)

**Purpose:** Track all notification events and their processing status

**Status Values:**
- `accepted` - Event received and validated
- `processed` - Event processed and sent to channels

**Key Fields:**
```javascript
{
  event_tracking_id: "EVT-20241128-001234",  // UNIQUE IDENTIFIER
  event_name: "ORDER_SHIPPED",  // Event categorization for analytics
  customer_id: "C001",
  customer_name: "John Doe",
  customer_email: "john@example.com",
  customer_phone: "+1-555-0101",

  notification_type: "transactional",  // promotional, alert, reminder, system
  priority: 1,  // 1=critical, 2=high, 3=medium, 4=low, 5=lowest

  subject: "Your order has shipped",
  message: "Order #12345 is on its way",

  channels: ["email", "sms", "push"],  // Which channels to use

  status: "processed",  // accepted | processed

  created_at: ISODate("2024-11-28T10:00:00Z"),
  processed_at: ISODate("2024-11-28T10:00:05Z"),

  metadata: {
    campaign_id: "CAMP-001",
    template_id: "TMPL-001",
    tags: ["order", "shipping"],
    source: "api"
  }
}
```

**Event Names (Examples):**
- `ORDER_PLACED` - New order notifications
- `ORDER_SHIPPED` - Shipping confirmations
- `ORDER_DELIVERED` - Delivery notifications
- `PAYMENT_RECEIVED` - Payment confirmations
- `PAYMENT_FAILED` - Payment failure alerts
- `ACCOUNT_CREATED` - Welcome messages
- `PASSWORD_RESET` - Password reset notifications
- `SUBSCRIPTION_RENEWED` - Subscription renewals
- `SECURITY_ALERT` - Security notifications
- `PROMOTIONAL_OFFER` - Marketing campaigns

**Indexes:**
- `event_tracking_id` (unique)
- `event_name` (for analytics and grouping)
- `customer_id`
- `status`
- `created_at`
- `notification_type`

---

### 2. email_notifications

**Purpose:** Track email delivery status and metrics

**Status Values:**
- `pending` - Queued for sending
- `processing` - Currently being sent
- `sent` - Successfully sent to provider
- `delivered` - Confirmed delivery
- `failed` - Failed to send
- `blacklisted` - Recipient is blacklisted
- `bounced` - Email bounced back
- `unsubscribed` - Recipient unsubscribed
- `read` - Email was opened

**Key Fields:**
```javascript
{
  event_tracking_id: "EVT-20241128-001234",  // Links to notification_events

  recipient_email: "john@example.com",
  recipient_name: "John Doe",

  subject: "Your order has shipped",
  message_body: "Order #12345 is on its way",
  html_body: "<html>...</html>",

  status: "delivered",

  sent_at: ISODate("2024-11-28T10:00:10Z"),
  delivered_at: ISODate("2024-11-28T10:00:15Z"),
  opened_at: ISODate("2024-11-28T11:30:00Z"),
  clicked_at: ISODate("2024-11-28T11:35:00Z"),

  email_provider: "sendgrid",
  message_id: "MSG-789456",

  retry_count: 0,
  error_details: null
}
```

---

### 3. sms_notifications

**Purpose:** Track SMS delivery status

**Status Values:**
- `pending`, `processing`, `sent`, `delivered`, `failed`, `blacklisted`

**Key Fields:**
```javascript
{
  event_tracking_id: "EVT-20241128-001234",

  recipient_phone: "+1-555-0101",
  recipient_name: "John Doe",

  message_body: "Order #12345 shipped",

  status: "sent",

  sent_at: ISODate("2024-11-28T10:01:00Z"),
  delivered_at: ISODate("2024-11-28T10:01:30Z"),

  sms_provider: "twilio",
  message_id: "SMS-123456",

  retry_count: 0,
  error_details: null,

  metadata: {
    country_code: "+1",
    carrier: "AT&T",
    message_parts: 1
  }
}
```

---

### 4. push_notifications

**Purpose:** Track push notification delivery

**Status Values:**
- `pending`, `processing`, `sent`, `delivered`, `failed`, `blacklisted`, `read`

**Key Fields:**
```javascript
{
  event_tracking_id: "EVT-20241128-001234",

  recipient_id: "C001",
  device_tokens: ["token_abc123"],

  title: "Your order has shipped",
  message_body: "Order #12345 is on its way",

  status: "delivered",

  sent_at: ISODate("2024-11-28T10:00:05Z"),
  delivered_at: ISODate("2024-11-28T10:00:10Z"),
  received_at: ISODate("2024-11-28T10:00:15Z"),
  clicked_at: ISODate("2024-11-28T10:15:00Z"),

  push_provider: "fcm",
  notification_id: "PUSH-654321",

  retry_count: 0,
  error_details: null,

  metadata: {
    action_url: "https://app.example.com/order/12345",
    image_url: null,
    badge_count: 1,
    sound: "default",
    platform: "android"
  }
}
```

---

### 5. inapp_notifications

**Purpose:** Track in-app notification status

**Status Values:**
- `pending`, `sent`, `delivered`, `read`, `failed`

**Key Fields:**
```javascript
{
  event_tracking_id: "EVT-20241128-001234",

  recipient_id: "C001",
  recipient_name: "John Doe",

  title: "Your order has shipped",
  message_body: "Order #12345 is on its way",

  status: "read",

  sent_at: ISODate("2024-11-28T10:02:00Z"),
  delivered_at: ISODate("2024-11-28T10:02:01Z"),
  read_at: ISODate("2024-11-28T12:00:00Z"),

  retry_count: 0,
  error_details: null,

  metadata: {
    action_url: "/orders/12345",
    icon: "shipping_icon.png",
    category: "order_update",
    expires_at: ISODate("2024-12-28T00:00:00Z")
  }
}
```

---

## Query Patterns

### 1. Simple Single-Collection Queries

**Find all accepted events:**
```javascript
db.notification_events.find({ status: "accepted" })
```

**Find failed email notifications:**
```javascript
db.email_notifications.find({ status: "failed" })
```

**Find events by event_name:**
```javascript
db.notification_events.find({ event_name: "ORDER_SHIPPED" })
```

**Count events by event_name:**
```javascript
db.notification_events.aggregate([
  { $group: { _id: "$event_name", count: { $sum: 1 } } },
  { $sort: { count: -1 } }
])
```

### 2. Cross-Collection Queries with $lookup

**Get events with email status:**
```javascript
db.notification_events.aggregate([
  {
    $lookup: {
      from: "email_notifications",
      localField: "event_tracking_id",
      foreignField: "event_tracking_id",
      as: "email_status"
    }
  },
  {
    $unwind: {
      path: "$email_status",
      preserveNullAndEmptyArrays: true
    }
  }
])
```

**Find events where email delivered but SMS failed:**
```javascript
db.notification_events.aggregate([
  {
    $lookup: {
      from: "email_notifications",
      localField: "event_tracking_id",
      foreignField: "event_tracking_id",
      as: "email"
    }
  },
  {
    $lookup: {
      from: "sms_notifications",
      localField: "event_tracking_id",
      foreignField: "event_tracking_id",
      as: "sms"
    }
  },
  {
    $match: {
      "email.0.status": "delivered",
      "sms.0.status": "failed"
    }
  }
])
```

### 3. Multi-Channel Analysis

**Count delivered notifications by channel:**
```javascript
db.notification_events.aggregate([
  // Lookup all channels
  {
    $lookup: {
      from: "email_notifications",
      localField: "event_tracking_id",
      foreignField: "event_tracking_id",
      as: "email"
    }
  },
  {
    $lookup: {
      from: "sms_notifications",
      localField: "event_tracking_id",
      foreignField: "event_tracking_id",
      as: "sms"
    }
  },
  {
    $lookup: {
      from: "push_notifications",
      localField: "event_tracking_id",
      foreignField: "event_tracking_id",
      as: "push"
    }
  },
  // Project delivered counts
  {
    $project: {
      email_delivered: {
        $cond: [
          { $eq: [{ $arrayElemAt: ["$email.status", 0] }, "delivered"] },
          1,
          0
        ]
      },
      sms_delivered: {
        $cond: [
          { $eq: [{ $arrayElemAt: ["$sms.status", 0] }, "delivered"] },
          1,
          0
        ]
      },
      push_delivered: {
        $cond: [
          { $eq: [{ $arrayElemAt: ["$push.status", 0] }, "delivered"] },
          1,
          0
        ]
      }
    }
  },
  // Aggregate totals
  {
    $group: {
      _id: null,
      total_email_delivered: { $sum: "$email_delivered" },
      total_sms_delivered: { $sum: "$sms_delivered" },
      total_push_delivered: { $sum: "$push_delivered" }
    }
  }
])
```

---

## API Endpoints

### Base URL: `/api/v2`

#### 1. Query Endpoint
```http
POST /v2/query
Content-Type: application/json

{
  "user_input": "Show events with failed email notifications",
  "execute": true
}
```

**Response:**
```json
{
  "user_input": "Show events with failed email notifications",
  "target_collection": "notification_events",
  "generated_mql": { ... },
  "explanation": "Joins events with failed emails",
  "involves_multiple_collections": true,
  "results": [ ... ],
  "count": 15,
  "execution_time_ms": 45.2
}
```

#### 2. Dashboard
```http
GET /v2/dashboard
```

Returns comprehensive stats across all collections.

#### 3. Event Details
```http
GET /v2/event/EVT-20241128-001234
```

Returns event with all channel statuses.

#### 4. Events with Channels
```http
GET /v2/events/with-channels?limit=50&skip=0
```

Returns events joined with channel statuses.

#### 5. Channel Stats
```http
GET /v2/stats/channel/email
```

Returns statistics for specific channel (email, sms, push, inapp).

#### 6. Event Name Stats
```http
GET /v2/stats/event-name
```

Returns statistics grouped by event_name (e.g., ORDER_PLACED, PAYMENT_RECEIVED).

#### 7. Event Name Channel Breakdown
```http
GET /v2/stats/event-name/{event_name}
```

Returns channel delivery breakdown for a specific event_name.

**Example:**
```http
GET /v2/stats/event-name/ORDER_SHIPPED
```

Returns:
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

#### 8. Events by Event Name
```http
GET /v2/events/by-event-name/{event_name}
```

Returns all events matching the specified event_name.

---

## Setup Instructions

### 1. Seed Sample Data

```bash
cd /Users/niranjan/python_projects/mongo-query-ai
python scripts/seed_multi_collection_notifications.py
```

This will:
- Create 2000 notification events across 20 different customers
- Generate corresponding channel notifications (~1400 emails, ~1100 SMS, ~1300 push, ~1200 in-app)
- Use 15 different event names (ORDER_PLACED, PAYMENT_RECEIVED, etc.)
- Create proper indexes for fast queries
- Link all collections via `event_tracking_id`

### 2. Test the API

```bash
# Health check
curl http://localhost:8000/api/v2/health

# Get dashboard
curl http://localhost:8000/api/v2/dashboard

# Query events
curl -X POST http://localhost:8000/api/v2/query \
  -H "Content-Type: application/json" \
  -d '{"user_input": "Show failed email notifications", "execute": true}'

# Get event details
curl http://localhost:8000/api/v2/event/EVT-20241128-000001
```

---

## Benefits of This Architecture

### 1. **Scalability**
- Each channel collection can be scaled independently
- Easier to shard by channel type
- Better query performance (smaller collections)

### 2. **Flexibility**
- Add new channels without modifying existing collections
- Channel-specific fields don't clutter primary collection
- Different retention policies per channel

### 3. **Clearer Data Model**
- Separation of concerns (event tracking vs. channel delivery)
- Easier to understand and maintain
- Better alignment with business domains

### 4. **Query Performance**
- Indexes optimized per collection
- Queries can target specific channels
- Reduced document size in primary collection

### 5. **Analytics**
- Cross-channel analysis with $lookup
- Channel-specific metrics
- Event-level vs. channel-level reporting

---

## Migration from Old Schema

If you have data in the old single-collection format:

```javascript
// Old: single collection
{
  customer_id: "C001",
  channel: "email",
  status: "delivered",
  ...all fields mixed together
}

// New: multi-collection
// notification_events
{
  event_tracking_id: "EVT-001",
  customer_id: "C001",
  channels: ["email"],
  status: "processed"
}

// email_notifications
{
  event_tracking_id: "EVT-001",
  status: "delivered",
  ...email-specific fields
}
```

---

## Files Created

1. **Schema Definition:**
   - `app/models/new_notification_schema.py`

2. **Database Service:**
   - `app/services/multi_collection_db_service.py`

3. **AI Service:**
   - `app/services/multi_collection_ai_service.py`

4. **API Routes:**
   - `app/api/multi_collection_routes.py`

5. **Seed Script:**
   - `scripts/seed_multi_collection_notifications.py`

6. **Documentation:**
   - `MULTI_COLLECTION_ARCHITECTURE.md` (this file)

---

## Next Steps

1. **Seed the database:**
   ```bash
   python scripts/seed_multi_collection_notifications.py
   ```

2. **Update main.py to include v2 routes:**
   ```python
   from app.api.multi_collection_routes import router as multi_collection_router
   app.include_router(multi_collection_router, prefix="/api")
   ```

3. **Test queries:**
   - Try natural language queries
   - Test cross-collection joins
   - Verify dashboard statistics

4. **Build dashboards:**
   - Create visualizations for multi-channel delivery rates
   - Track event-to-channel conversion
   - Monitor channel-specific performance

---

**The new multi-collection architecture is ready to use!** 🎉
