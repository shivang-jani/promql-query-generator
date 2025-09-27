from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, PyMongoError
from config import Config
import uuid
from datetime import datetime
from typing import Optional, Dict, Any
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MongoDBClient:
    def __init__(self):
        self.client = None
        self.db = None
        self.collection = None
        self._connect()
    
    def _connect(self):
        """Establish connection to MongoDB"""
        try:
            self.client = MongoClient(Config.MONGODB_URI)
            # Test the connection
            self.client.admin.command('ping')
            self.db = self.client[Config.MONGODB_DATABASE_NAME]
            self.collection = self.db['conversations']
            logger.info(f"Successfully connected to MongoDB database: {Config.MONGODB_DATABASE_NAME}")
        except ConnectionFailure as e:
            logger.error(f"Failed to connect to MongoDB: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error connecting to MongoDB: {e}")
            raise
    
    def generate_conversation_id(self) -> str:
        """Generate a new UUID for conversation ID"""
        return str(uuid.uuid4())
    
    def store_conversation(self, 
                          conversation_id: str,
                          natural_language_query: str,
                          generated_payload: Dict[Any, Any],
                          prometheus_data: Dict[Any, Any],
                          success_status: int) -> bool:
        """
        Store conversation data in MongoDB
        
        Args:
            conversation_id: UUID string for the conversation
            natural_language_query: Original user query
            generated_payload: OpenAI generated payload
            prometheus_data: Prometheus response data
            success_status: HTTP status code (200, 404, 500, etc.)
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            document = {
                "conversationId": conversation_id,
                "naturalLanguageQuery": natural_language_query,
                "generatedPayload": generated_payload,
                "prometheusData": prometheus_data,
                "timestamp": datetime.utcnow().isoformat(),
                "success": success_status
            }
            
            result = self.collection.insert_one(document)
            logger.info(f"Successfully stored conversation {conversation_id}")
            return True
            
        except PyMongoError as e:
            logger.error(f"Failed to store conversation {conversation_id}: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error storing conversation {conversation_id}: {e}")
            return False
    
    def get_conversation(self, conversation_id: str) -> Optional[Dict[Any, Any]]:
        """
        Retrieve conversation data by conversation ID
        
        Args:
            conversation_id: UUID string for the conversation
        
        Returns:
            Dict containing conversation data or None if not found
        """
        try:
            document = self.collection.find_one(
                {"conversationId": conversation_id},
                {"_id": 0}  # Exclude MongoDB's internal _id field
            )
            
            if document:
                logger.info(f"Successfully retrieved conversation {conversation_id}")
                return document
            else:
                logger.warning(f"Conversation {conversation_id} not found")
                return None
                
        except PyMongoError as e:
            logger.error(f"Failed to retrieve conversation {conversation_id}: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error retrieving conversation {conversation_id}: {e}")
            return None
    
    def close_connection(self):
        """Close MongoDB connection"""
        if self.client:
            self.client.close()
            logger.info("MongoDB connection closed")

# Global MongoDB client instance
mongo_client = MongoDBClient()
