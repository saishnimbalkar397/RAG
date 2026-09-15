"""
Qdrant vector database operations.

This module provides a clean interface to Qdrant for:
- Creating collections
- Storing document embeddings
- Searching for similar vectors
- Managing document metadata
"""
import logging
from typing import Any

from qdrant_client import QdrantClient
from qdrant_client.http import models
from qdrant_client.http.exceptions import UnexpectedResponse

from app.config import Settings

logger = logging.getLogger(__name__)


class QdrantDB:
    """
    Qdrant vector database client.
    
    Handles all vector storage and retrieval operations.
    Supports both in-memory and server modes.
    """
    
    def __init__(self, settings: Settings):
        """
        Initialize Qdrant client.
        
        Args:
            settings: Application settings
        """
        self.settings = settings
        self.collection_name = settings.qdrant_collection_name
        
        # Initialize client based on mode
        if settings.qdrant_mode == "memory":
            logger.info("Initializing Qdrant in-memory mode")
            self.client = QdrantClient(":memory:")
        else:
            logger.info(f"Connecting to Qdrant server at {settings.qdrant_url}")
            self.client = QdrantClient(
                url=settings.qdrant_url,
                api_key=settings.qdrant_api_key,
            )
        
        self.vector_size = self._get_embedding_dimension()
        logger.info(f"Using vector dimension: {self.vector_size}")
    
    def _get_embedding_dimension(self) -> int:
        """
        Get the dimension of the embedding model.
        
        OpenAI embedding dimensions:
        - text-embedding-3-small: 1536
        - text-embedding-3-large: 3072
        - text-embedding-ada-002: 1536
        
        Returns:
            int: Embedding dimension
        """
        model_dimensions = {
            "text-embedding-3-small": 1536,
            "text-embedding-3-large": 3072,
            "text-embedding-ada-002": 1536,
        }
        
        model = self.settings.embedding_model
        if model not in model_dimensions:
            logger.warning(
                f"Unknown embedding model: {model}. "
                f"Defaulting to 1536 dimensions."
            )
            return 1536
        
        return model_dimensions[model]
    
    def collection_exists(self) -> bool:
        """
        Check if the collection exists.
        
        Returns:
            bool: True if collection exists
        """
        try:
            collections = self.client.get_collections().collections
            return any(col.name == self.collection_name for col in collections)
        except Exception as e:
            logger.error(f"Error checking collection existence: {e}")
            return False
    
    def create_collection(self, recreate: bool = False) -> None:
        """
        Create a new collection for document embeddings.
        
        The collection stores:
        - Vector embeddings (for semantic search)
        - Document metadata (filename, page, chunk_id, etc.)
        - Original text content
        
        Args:
            recreate: If True, delete existing collection first
            
        Raises:
            Exception: If collection creation fails
        """
        try:
            # Delete existing collection if recreate=True
            if recreate and self.collection_exists():
                logger.info(f"Deleting existing collection: {self.collection_name}")
                self.client.delete_collection(self.collection_name)
            
            # Check if collection already exists
            if self.collection_exists():
                logger.info(f"Collection '{self.collection_name}' already exists")
                return
            
            # Create new collection
            logger.info(f"Creating collection: {self.collection_name}")
            self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config=models.VectorParams(
                    size=self.vector_size,
                    distance=models.Distance.COSINE,  # Cosine similarity
                ),
            )
            
            # Create payload index for efficient filtering
            # This allows fast filtering by document_id, filename, etc.
            self.client.create_payload_index(
                collection_name=self.collection_name,
                field_name="document_id",
                field_schema=models.PayloadSchemaType.KEYWORD,
            )
            
            self.client.create_payload_index(
                collection_name=self.collection_name,
                field_name="filename",
                field_schema=models.PayloadSchemaType.KEYWORD,
            )
            
            logger.info(f"Collection '{self.collection_name}' created successfully")
            
        except Exception as e:
            logger.error(f"Failed to create collection: {e}")
            raise
    
    def get_collection_info(self) -> dict[str, Any] | None:
        """
        Get information about the collection.
        
        Returns:
            dict: Collection information or None if doesn't exist
        """
        try:
            if not self.collection_exists():
                return None
            
            info = self.client.get_collection(self.collection_name)
            return {
                "name": self.collection_name,
                "points_count": info.points_count,
                "status": info.status,
            }
        except Exception as e:
            logger.error(f"Error getting collection info: {e}")
            return None
    
    def count_documents(self) -> int:
        """
        Count total number of chunks in the collection.
        
        Returns:
            int: Number of document chunks
        """
        try:
            if not self.collection_exists():
                return 0
            
            info = self.client.get_collection(self.collection_name)
            return info.points_count or 0
        except Exception as e:
            logger.error(f"Error counting documents: {e}")
            return 0
    
    def get_unique_documents(self) -> list[str]:
        """
        Get list of unique document IDs in the collection.
        
        Returns:
            list[str]: List of unique document IDs
        """
        try:
            if not self.collection_exists():
                return []
            
            # Scroll through all points and collect unique document_ids
            document_ids = set()
            offset = None
            
            while True:
                records, offset = self.client.scroll(
                    collection_name=self.collection_name,
                    limit=100,
                    offset=offset,
                    with_payload=True,
                    with_vectors=False,
                )
                
                for record in records:
                    if record.payload and "document_id" in record.payload:
                        document_ids.add(record.payload["document_id"])
                
                if offset is None:
                    break
            
            return sorted(list(document_ids))
            
        except Exception as e:
            logger.error(f"Error getting unique documents: {e}")
            return []
    
    def delete_document(self, document_id: str) -> bool:
        """
        Delete all chunks for a specific document.
        
        Args:
            document_id: Document ID to delete
            
        Returns:
            bool: True if successful
        """
        try:
            if not self.collection_exists():
                logger.warning("Collection doesn't exist")
                return False
            
            logger.info(f"Deleting document: {document_id}")
            
            # Delete all points with matching document_id
            self.client.delete(
                collection_name=self.collection_name,
                points_selector=models.FilterSelector(
                    filter=models.Filter(
                        must=[
                            models.FieldCondition(
                                key="document_id",
                                match=models.MatchValue(value=document_id),
                            )
                        ]
                    )
                ),
            )
            
            logger.info(f"Deleted document: {document_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting document {document_id}: {e}")
            return False
    
    def health_check(self) -> bool:
        """
        Check if Qdrant is accessible and healthy.
        
        Returns:
            bool: True if healthy
        """
        try:
            # Try to get collections
            self.client.get_collections()
            return True
        except Exception as e:
            logger.error(f"Qdrant health check failed: {e}")
            return False


def get_qdrant_client(settings: Settings) -> QdrantDB:
    """
    Factory function to create QdrantDB instance.
    
    Args:
        settings: Application settings
        
    Returns:
        QdrantDB: Configured Qdrant client
    """
    return QdrantDB(settings)


if __name__ == "__main__":
    # Test Qdrant connection
    from app.config import get_settings
    
    logging.basicConfig(level=logging.INFO)
    
    try:
        settings = get_settings()
        db = get_qdrant_client(settings)
        
        print("\n" + "=" * 50)
        print("Qdrant Database Test")
        print("=" * 50)
        
        # Health check
        if db.health_check():
            print("✓ Qdrant is healthy")
        else:
            print("✗ Qdrant health check failed")
            exit(1)
        
        # Create collection
        print(f"\nCreating collection: {db.collection_name}")
        db.create_collection(recreate=True)
        
        # Get collection info
        info = db.get_collection_info()
        if info:
            print(f"✓ Collection created successfully")
            print(f"  Name: {info['name']}")
            print(f"  Points: {info['points_count']}")
            print(f"  Status: {info['status']}")
        else:
            print("✗ Failed to get collection info")
        
        print("\n" + "=" * 50)
        print("✓ All tests passed!")
        print("=" * 50)
        
    except Exception as e:
        print(f"\n✗ Test failed: {e}")
        exit(1)
