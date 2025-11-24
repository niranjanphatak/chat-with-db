from pymongo import MongoClient
from pymongo.collection import Collection
from pymongo.database import Database
from app.config import settings
import logging
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)


class CreditCardDatabaseService:
    """Database service for credit card transactions"""

    def __init__(self):
        self.client: Optional[MongoClient] = None
        self.db: Optional[Database] = None
        self.collection: Optional[Collection] = None

    def connect(self):
        """Connect to MongoDB"""
        try:
            self.client = MongoClient(settings.MONGODB_URI)
            self.db = self.client[settings.MONGODB_DATABASE]
            self.collection = self.db["credit_card_transactions"]

            # Test connection
            self.client.admin.command('ping')
            logger.info("Successfully connected to MongoDB for credit card transactions")

            # Create indexes
            self._create_indexes()

        except Exception as e:
            logger.error(f"Failed to connect to MongoDB: {e}")
            raise

    def _create_indexes(self):
        """Create indexes for better query performance"""
        try:
            self.collection.create_index("transaction_date")
            self.collection.create_index("category")
            self.collection.create_index("merchant_name")
            self.collection.create_index("card_number")
            self.collection.create_index("status")
            self.collection.create_index([("transaction_date", -1), ("category", 1)])
            logger.info("Indexes created successfully")
        except Exception as e:
            logger.warning(f"Failed to create indexes: {e}")

    def close(self):
        """Close MongoDB connection"""
        if self.client:
            self.client.close()
            logger.info("MongoDB connection closed")

    def get_collection(self) -> Collection:
        """Get the transactions collection"""
        if not self.collection:
            self.connect()
        return self.collection

    def get_database(self) -> Database:
        """Get the database instance"""
        if not self.db:
            self.connect()
        return self.db

    def execute_find(self, query: Dict, projection: Optional[Dict] = None,
                    limit: int = 100, sort: Optional[List] = None) -> List[Dict]:
        """
        Execute a find query on credit card transactions.

        Args:
            query: MongoDB query filter
            projection: Fields to include/exclude
            limit: Maximum number of results
            sort: Sort specification

        Returns:
            List of matching documents
        """
        try:
            collection = self.get_collection()

            cursor = collection.find(query, projection).limit(limit)

            if sort:
                cursor = cursor.sort(sort)
            else:
                # Default sort by transaction_date descending
                cursor = cursor.sort("transaction_date", -1)

            results = list(cursor)
            logger.info(f"Find query returned {len(results)} results")
            return results

        except Exception as e:
            logger.error(f"Error executing find query: {e}")
            raise

    def execute_aggregation(self, pipeline: List[Dict]) -> List[Dict]:
        """
        Execute an aggregation pipeline on credit card transactions.

        Args:
            pipeline: MongoDB aggregation pipeline

        Returns:
            List of aggregation results
        """
        try:
            collection = self.get_collection()
            results = list(collection.aggregate(pipeline))
            logger.info(f"Aggregation returned {len(results)} results")
            return results

        except Exception as e:
            logger.error(f"Error executing aggregation: {e}")
            raise

    def get_statistics(self) -> Dict:
        """Get overall statistics for credit card transactions"""
        try:
            collection = self.get_collection()

            total_count = collection.count_documents({})

            # Total spending (posted transactions only)
            spending_pipeline = [
                {"$match": {"status": "posted", "transaction_type": "purchase"}},
                {"$group": {"_id": None, "total": {"$sum": "$amount"}}}
            ]
            spending_result = list(collection.aggregate(spending_pipeline))
            total_spending = spending_result[0]["total"] if spending_result else 0

            # Category breakdown
            category_pipeline = [
                {"$match": {"status": "posted"}},
                {"$group": {
                    "_id": "$category",
                    "count": {"$sum": 1},
                    "total": {"$sum": "$amount"}
                }},
                {"$sort": {"total": -1}}
            ]
            category_stats = list(collection.aggregate(category_pipeline))

            # Monthly spending
            monthly_pipeline = [
                {"$match": {"status": "posted"}},
                {"$group": {
                    "_id": {
                        "year": {"$year": "$transaction_date"},
                        "month": {"$month": "$transaction_date"}
                    },
                    "count": {"$sum": 1},
                    "total": {"$sum": "$amount"}
                }},
                {"$sort": {"_id.year": -1, "_id.month": -1}},
                {"$limit": 12}
            ]
            monthly_stats = list(collection.aggregate(monthly_pipeline))

            # Transaction type breakdown
            type_pipeline = [
                {"$group": {
                    "_id": "$transaction_type",
                    "count": {"$sum": 1},
                    "total": {"$sum": "$amount"}
                }}
            ]
            type_stats = list(collection.aggregate(type_pipeline))

            return {
                "total_transactions": total_count,
                "total_spending": round(total_spending, 2),
                "by_category": category_stats,
                "by_month": monthly_stats,
                "by_type": type_stats
            }

        except Exception as e:
            logger.error(f"Error getting statistics: {e}")
            raise

    def get_summary_data(self, query: Optional[Dict] = None) -> Dict:
        """Get aggregated summary data for transactions (no raw data)"""
        try:
            collection = self.get_collection()

            match_stage = {"$match": query or {"status": "posted"}}

            # Summary pipeline - returns only aggregated data
            pipeline = [
                match_stage,
                {
                    "$facet": {
                        "total_stats": [
                            {"$group": {
                                "_id": None,
                                "total_amount": {"$sum": "$amount"},
                                "total_count": {"$sum": 1},
                                "avg_amount": {"$avg": "$amount"},
                                "max_amount": {"$max": "$amount"},
                                "min_amount": {"$min": "$amount"}
                            }}
                        ],
                        "category_breakdown": [
                            {"$group": {
                                "_id": "$category",
                                "total": {"$sum": "$amount"},
                                "count": {"$sum": 1},
                                "average": {"$avg": "$amount"}
                            }},
                            {"$sort": {"total": -1}}
                        ],
                        "merchant_top10": [
                            {"$group": {
                                "_id": "$merchant_name",
                                "total": {"$sum": "$amount"},
                                "count": {"$sum": 1}
                            }},
                            {"$sort": {"total": -1}},
                            {"$limit": 10}
                        ],
                        "transaction_types": [
                            {"$group": {
                                "_id": "$transaction_type",
                                "count": {"$sum": 1},
                                "total": {"$sum": "$amount"}
                            }}
                        ]
                    }
                }
            ]

            result = list(collection.aggregate(pipeline))

            if result:
                return result[0]
            return {}

        except Exception as e:
            logger.error(f"Error getting summary data: {e}")
            raise


# Singleton instance
cc_db_service = CreditCardDatabaseService()
