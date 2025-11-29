from pymongo import MongoClient, ASCENDING, DESCENDING
from app.config import settings
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class MultiCollectionNotificationService:
    """
    Database service for multi-collection notification system.

    Collections:
    - notification_events (primary)
    - email_notifications
    - sms_notifications
    - push_notifications
    - inapp_notifications
    """

    def __init__(self):
        self.client = MongoClient(settings.MONGODB_URI)
        self.db = self.client[settings.MONGODB_DATABASE]

        # Collection references
        self.events = self.db["notification_events"]
        self.emails = self.db["email_notifications"]
        self.sms = self.db["sms_notifications"]
        self.push = self.db["push_notifications"]
        self.inapp = self.db["inapp_notifications"]

        self._create_indexes()

    def _create_indexes(self):
        """Create indexes for all collections"""
        logger.info("Creating indexes for multi-collection notification system...")

        # Primary collection indexes
        self.events.create_index([("event_tracking_id", ASCENDING)], unique=True)
        self.events.create_index([("event_name", ASCENDING)])
        self.events.create_index([("customer_id", ASCENDING)])
        self.events.create_index([("status", ASCENDING)])
        self.events.create_index([("created_at", DESCENDING)])
        self.events.create_index([("notification_type", ASCENDING)])

        # Email notifications indexes
        self.emails.create_index([("event_tracking_id", ASCENDING)])
        self.emails.create_index([("recipient_email", ASCENDING)])
        self.emails.create_index([("status", ASCENDING)])
        self.emails.create_index([("sent_at", DESCENDING)])

        # SMS notifications indexes
        self.sms.create_index([("event_tracking_id", ASCENDING)])
        self.sms.create_index([("recipient_phone", ASCENDING)])
        self.sms.create_index([("status", ASCENDING)])
        self.sms.create_index([("sent_at", DESCENDING)])

        # Push notifications indexes
        self.push.create_index([("event_tracking_id", ASCENDING)])
        self.push.create_index([("recipient_id", ASCENDING)])
        self.push.create_index([("status", ASCENDING)])
        self.push.create_index([("sent_at", DESCENDING)])

        # In-app notifications indexes
        self.inapp.create_index([("event_tracking_id", ASCENDING)])
        self.inapp.create_index([("recipient_id", ASCENDING)])
        self.inapp.create_index([("status", ASCENDING)])
        self.inapp.create_index([("sent_at", DESCENDING)])

        logger.info("✅ Indexes created successfully")

    def get_database(self):
        """Get database instance"""
        return self.db

    def get_collection(self, collection_name: str):
        """Get a specific collection by name"""
        collections = {
            "notification_events": self.events,
            "email_notifications": self.emails,
            "sms_notifications": self.sms,
            "push_notifications": self.push,
            "inapp_notifications": self.inapp
        }
        return collections.get(collection_name, self.events)

    # ========================================================================
    # Query Execution Methods
    # ========================================================================

    def execute_find(self, collection_name: str, query: dict,
                     projection: Optional[dict] = None,
                     limit: int = 100) -> List[dict]:
        """Execute find query on specified collection"""
        collection = self.get_collection(collection_name)

        if projection:
            cursor = collection.find(query, projection).limit(limit)
        else:
            cursor = collection.find(query).limit(limit)

        return list(cursor)

    def execute_aggregation(self, collection_name: str, pipeline: list) -> List[dict]:
        """Execute aggregation pipeline on specified collection"""
        collection = self.get_collection(collection_name)
        return list(collection.aggregate(pipeline))

    # ========================================================================
    # Cross-Collection Queries (Joins)
    # ========================================================================

    def get_event_with_channels(self, event_tracking_id: str) -> Dict[str, Any]:
        """
        Get complete notification event with all channel statuses.

        Returns:
            {
                "event": {...},
                "email": {...},
                "sms": {...},
                "push": {...},
                "inapp": {...}
            }
        """
        result = {
            "event": self.events.find_one({"event_tracking_id": event_tracking_id}),
            "email": self.emails.find_one({"event_tracking_id": event_tracking_id}),
            "sms": self.sms.find_one({"event_tracking_id": event_tracking_id}),
            "push": self.push.find_one({"event_tracking_id": event_tracking_id}),
            "inapp": self.inapp.find_one({"event_tracking_id": event_tracking_id})
        }
        return result

    def get_events_with_channel_status(self, query: dict = {}, limit: int = 100) -> List[Dict]:
        """
        Get events with aggregated channel status using $lookup.

        This performs MongoDB joins across collections.
        """
        pipeline = [
            {"$match": query},
            {"$limit": limit},

            # Lookup email status
            {"$lookup": {
                "from": "email_notifications",
                "localField": "event_tracking_id",
                "foreignField": "event_tracking_id",
                "as": "email_status"
            }},

            # Lookup SMS status
            {"$lookup": {
                "from": "sms_notifications",
                "localField": "event_tracking_id",
                "foreignField": "event_tracking_id",
                "as": "sms_status"
            }},

            # Lookup push status
            {"$lookup": {
                "from": "push_notifications",
                "localField": "event_tracking_id",
                "foreignField": "event_tracking_id",
                "as": "push_status"
            }},

            # Lookup in-app status
            {"$lookup": {
                "from": "inapp_notifications",
                "localField": "event_tracking_id",
                "foreignField": "event_tracking_id",
                "as": "inapp_status"
            }},

            # Unwind arrays (get first element or null)
            {"$addFields": {
                "email": {"$arrayElemAt": ["$email_status", 0]},
                "sms": {"$arrayElemAt": ["$sms_status", 0]},
                "push": {"$arrayElemAt": ["$push_status", 0]},
                "inapp": {"$arrayElemAt": ["$inapp_status", 0]}
            }},

            # Clean up
            {"$project": {
                "email_status": 0,
                "sms_status": 0,
                "push_status": 0,
                "inapp_status": 0
            }}
        ]

        return list(self.events.aggregate(pipeline))

    # ========================================================================
    # Dashboard Statistics
    # ========================================================================

    def get_dashboard_stats(self) -> Dict[str, Any]:
        """Get comprehensive dashboard statistics across all collections"""

        stats = {
            # Primary collection stats
            "events": {
                "total": self.events.count_documents({}),
                "by_status": list(self.events.aggregate([
                    {"$group": {"_id": "$status", "count": {"$sum": 1}}},
                    {"$sort": {"count": -1}}
                ])),
                "by_type": list(self.events.aggregate([
                    {"$group": {"_id": "$notification_type", "count": {"$sum": 1}}},
                    {"$sort": {"count": -1}}
                ])),
                "by_priority": list(self.events.aggregate([
                    {"$group": {"_id": "$priority", "count": {"$sum": 1}}},
                    {"$sort": {"_id": 1}}
                ])),
                "by_event_name": list(self.events.aggregate([
                    {"$group": {"_id": "$event_name", "count": {"$sum": 1}}},
                    {"$sort": {"count": -1}},
                    {"$limit": 10}
                ]))
            },

            # Email channel stats
            "email": {
                "total": self.emails.count_documents({}),
                "by_status": list(self.emails.aggregate([
                    {"$group": {"_id": "$status", "count": {"$sum": 1}}},
                    {"$sort": {"count": -1}}
                ])),
                "delivery_rate": self._calculate_delivery_rate("email_notifications")
            },

            # SMS channel stats
            "sms": {
                "total": self.sms.count_documents({}),
                "by_status": list(self.sms.aggregate([
                    {"$group": {"_id": "$status", "count": {"$sum": 1}}},
                    {"$sort": {"count": -1}}
                ])),
                "delivery_rate": self._calculate_delivery_rate("sms_notifications")
            },

            # Push channel stats
            "push": {
                "total": self.push.count_documents({}),
                "by_status": list(self.push.aggregate([
                    {"$group": {"_id": "$status", "count": {"$sum": 1}}},
                    {"$sort": {"count": -1}}
                ])),
                "delivery_rate": self._calculate_delivery_rate("push_notifications")
            },

            # In-app channel stats
            "inapp": {
                "total": self.inapp.count_documents({}),
                "by_status": list(self.inapp.aggregate([
                    {"$group": {"_id": "$status", "count": {"$sum": 1}}},
                    {"$sort": {"count": -1}}
                ])),
                "delivery_rate": self._calculate_delivery_rate("inapp_notifications")
            },

            # Cross-channel insights
            "cross_channel": {
                "events_by_channel_count": list(self.events.aggregate([
                    {"$project": {"channel_count": {"$size": "$channels"}}},
                    {"$group": {"_id": "$channel_count", "count": {"$sum": 1}}},
                    {"$sort": {"_id": 1}}
                ])),
                "multi_channel_events": self.events.count_documents({
                    "channels": {"$exists": True, "$not": {"$size": 1}}
                })
            },

            # Time-based trends
            "trends": {
                "daily_events": list(self.events.aggregate([
                    {"$group": {
                        "_id": {"$dateToString": {"format": "%Y-%m-%d", "date": "$created_at"}},
                        "count": {"$sum": 1}
                    }},
                    {"$sort": {"_id": -1}},
                    {"$limit": 7}
                ]))
            }
        }

        return stats

    def _calculate_delivery_rate(self, collection_name: str) -> Dict[str, float]:
        """Calculate delivery rate for a channel"""
        collection = self.get_collection(collection_name)

        total = collection.count_documents({})
        if total == 0:
            return {"rate": 0.0, "total": 0, "delivered": 0}

        delivered = collection.count_documents({
            "status": {"$in": ["delivered", "sent", "read"]}
        })

        return {
            "rate": round((delivered / total) * 100, 2),
            "total": total,
            "delivered": delivered
        }

    # ========================================================================
    # Data Insertion (for testing/seeding)
    # ========================================================================

    def insert_notification_event(self, event_data: dict) -> str:
        """Insert a notification event"""
        result = self.events.insert_one(event_data)
        return str(result.inserted_id)

    def insert_channel_notification(self, collection_name: str, notification_data: dict) -> str:
        """Insert a channel-specific notification"""
        collection = self.get_collection(collection_name)
        result = collection.insert_one(notification_data)
        return str(result.inserted_id)

    # ========================================================================
    # Utility Methods
    # ========================================================================

    def get_collection_names(self) -> List[str]:
        """Get all notification-related collection names"""
        return [
            "notification_events",
            "email_notifications",
            "sms_notifications",
            "push_notifications",
            "inapp_notifications"
        ]

    def drop_all_collections(self):
        """Drop all notification collections (use with caution!)"""
        logger.warning("⚠️ Dropping all notification collections...")
        for collection_name in self.get_collection_names():
            self.db[collection_name].drop()
        logger.info("✅ All collections dropped")

    # ========================================================================
    # Event Name Analytics
    # ========================================================================

    def get_events_by_event_name(self, event_name: str, limit: int = 100) -> List[Dict]:
        """Get events filtered by event_name"""
        return list(self.events.find({"event_name": event_name}).limit(limit))

    def get_event_name_stats(self) -> List[Dict]:
        """Get statistics grouped by event_name"""
        return list(self.events.aggregate([
            {"$group": {
                "_id": "$event_name",
                "count": {"$sum": 1},
                "by_status": {"$push": "$status"},
                "by_channel": {"$push": "$channels"}
            }},
            {"$project": {
                "event_name": "$_id",
                "count": 1,
                "accepted": {
                    "$size": {
                        "$filter": {
                            "input": "$by_status",
                            "cond": {"$eq": ["$$this", "accepted"]}
                        }
                    }
                },
                "processed": {
                    "$size": {
                        "$filter": {
                            "input": "$by_status",
                            "cond": {"$eq": ["$$this", "processed"]}
                        }
                    }
                }
            }},
            {"$sort": {"count": -1}}
        ]))

    def get_event_name_channel_breakdown(self, event_name: str) -> Dict[str, Any]:
        """Get channel delivery breakdown for a specific event_name"""
        pipeline = [
            {"$match": {"event_name": event_name}},

            # Lookup all channels
            {"$lookup": {
                "from": "email_notifications",
                "localField": "event_tracking_id",
                "foreignField": "event_tracking_id",
                "as": "email"
            }},
            {"$lookup": {
                "from": "sms_notifications",
                "localField": "event_tracking_id",
                "foreignField": "event_tracking_id",
                "as": "sms"
            }},
            {"$lookup": {
                "from": "push_notifications",
                "localField": "event_tracking_id",
                "foreignField": "event_tracking_id",
                "as": "push"
            }},
            {"$lookup": {
                "from": "inapp_notifications",
                "localField": "event_tracking_id",
                "foreignField": "event_tracking_id",
                "as": "inapp"
            }},

            # Unwind arrays
            {"$addFields": {
                "email": {"$arrayElemAt": ["$email", 0]},
                "sms": {"$arrayElemAt": ["$sms", 0]},
                "push": {"$arrayElemAt": ["$push", 0]},
                "inapp": {"$arrayElemAt": ["$inapp", 0]}
            }},

            # Group by statuses
            {"$group": {
                "_id": "$event_name",
                "total_events": {"$sum": 1},
                "email_total": {
                    "$sum": {"$cond": [{"$ne": ["$email", None]}, 1, 0]}
                },
                "email_statuses": {"$push": "$email.status"},
                "sms_total": {
                    "$sum": {"$cond": [{"$ne": ["$sms", None]}, 1, 0]}
                },
                "sms_statuses": {"$push": "$sms.status"},
                "push_total": {
                    "$sum": {"$cond": [{"$ne": ["$push", None]}, 1, 0]}
                },
                "push_statuses": {"$push": "$push.status"},
                "inapp_total": {
                    "$sum": {"$cond": [{"$ne": ["$inapp", None]}, 1, 0]}
                },
                "inapp_statuses": {"$push": "$inapp.status"}
            }}
        ]

        results = list(self.events.aggregate(pipeline))
        if not results:
            return {}

        raw_data = results[0]

        # Transform to frontend-expected format
        def get_status_breakdown(statuses):
            """Convert status list to breakdown with counts"""
            status_counts = {}
            for status in statuses:
                if status:  # Skip None values
                    status_counts[status] = status_counts.get(status, 0) + 1
            return [{"_id": status, "count": count} for status, count in status_counts.items()]

        def calculate_delivery_rate(statuses):
            """Calculate delivery rate from status list"""
            if not statuses:
                return {"rate": 0, "delivered": 0, "total": 0}

            total = sum(1 for s in statuses if s)  # Count non-None statuses
            delivered = sum(1 for s in statuses if s in ['delivered', 'read'])
            rate = (delivered / total * 100) if total > 0 else 0

            return {
                "rate": round(rate, 2),
                "delivered": delivered,
                "total": total
            }

        return {
            "total_events": raw_data.get("total_events", 0),
            "email": {
                "total": raw_data.get("email_total", 0),
                "by_status": get_status_breakdown(raw_data.get("email_statuses", [])),
                "delivery_rate": calculate_delivery_rate(raw_data.get("email_statuses", []))
            },
            "sms": {
                "total": raw_data.get("sms_total", 0),
                "by_status": get_status_breakdown(raw_data.get("sms_statuses", [])),
                "delivery_rate": calculate_delivery_rate(raw_data.get("sms_statuses", []))
            },
            "push": {
                "total": raw_data.get("push_total", 0),
                "by_status": get_status_breakdown(raw_data.get("push_statuses", [])),
                "delivery_rate": calculate_delivery_rate(raw_data.get("push_statuses", []))
            },
            "inapp": {
                "total": raw_data.get("inapp_total", 0),
                "by_status": get_status_breakdown(raw_data.get("inapp_statuses", [])),
                "delivery_rate": calculate_delivery_rate(raw_data.get("inapp_statuses", []))
            }
        }


# Singleton instance
multi_collection_db_service = MultiCollectionNotificationService()
