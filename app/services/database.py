from pymongo import MongoClient
from pymongo.database import Database
from pymongo.collection import Collection
from app.config import settings
import logging

logger = logging.getLogger(__name__)


class MongoDBService:
    _client: MongoClient = None
    _db: Database = None

    @classmethod
    def connect(cls) -> None:
        """Initialize MongoDB connection"""
        if cls._client is None:
            try:
                cls._client = MongoClient(settings.MONGODB_URI)
                cls._db = cls._client[settings.MONGODB_DATABASE]
                # Test connection
                cls._client.admin.command('ping')
                logger.info(f"Connected to MongoDB: {settings.MONGODB_DATABASE}")
            except Exception as e:
                logger.error(f"Failed to connect to MongoDB: {e}")
                raise

    @classmethod
    def get_database(cls) -> Database:
        """Get database instance"""
        if cls._db is None:
            cls.connect()
        return cls._db

    @classmethod
    def get_collection(cls, collection_name: str = None) -> Collection:
        """Get collection instance"""
        if collection_name is None:
            collection_name = settings.NOTIFICATIONS_COLLECTION
        return cls.get_database()[collection_name]

    @classmethod
    def close(cls) -> None:
        """Close MongoDB connection"""
        if cls._client:
            cls._client.close()
            cls._client = None
            cls._db = None
            logger.info("MongoDB connection closed")

    @classmethod
    def execute_find(cls, query: dict, collection_name: str = None,
                     projection: dict = None, limit: int = 100) -> list:
        """Execute a find query and return results"""
        collection = cls.get_collection(collection_name)
        cursor = collection.find(query, projection).limit(limit)
        return list(cursor)

    @classmethod
    def execute_aggregation(cls, pipeline: list, collection_name: str = None) -> list:
        """Execute an aggregation pipeline and return results"""
        collection = cls.get_collection(collection_name)
        cursor = collection.aggregate(pipeline)
        return list(cursor)

    @classmethod
    def get_count(cls, query: dict, collection_name: str = None) -> int:
        """Get count of documents matching query"""
        collection = cls.get_collection(collection_name)
        return collection.count_documents(query)

    @classmethod
    def get_distinct(cls, field: str, query: dict = None, collection_name: str = None) -> list:
        """Get distinct values for a field"""
        collection = cls.get_collection(collection_name)
        return collection.distinct(field, query or {})


# Singleton instance
db_service = MongoDBService()
