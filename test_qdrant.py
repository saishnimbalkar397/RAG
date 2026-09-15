"""
Test script for Qdrant database connection.
"""
import logging
import sys
from pathlib import Path

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

from app.config import get_settings
from app.qdrant_db import get_qdrant_client

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def main():
    try:
        print("\n" + "=" * 50)
        print("Qdrant Database Test")
        print("=" * 50)
        
        # Load settings
        print("\n1. Loading configuration...")
        settings = get_settings()
        print(f"✓ Configuration loaded")
        print(f"  Qdrant Mode: {settings.qdrant_mode}")
        print(f"  Collection: {settings.qdrant_collection_name}")
        
        # Initialize Qdrant client
        print("\n2. Initializing Qdrant client...")
        db = get_qdrant_client(settings)
        print(f"✓ Qdrant client initialized")
        
        # Health check
        print("\n3. Performing health check...")
        if db.health_check():
            print("✓ Qdrant is healthy and accessible")
        else:
            print("✗ Qdrant health check failed")
            return False
        
        # Create collection
        print(f"\n4. Creating collection '{db.collection_name}'...")
        db.create_collection(recreate=True)
        print(f"✓ Collection created successfully")
        
        # Get collection info
        print("\n5. Getting collection information...")
        info = db.get_collection_info()
        if info:
            print(f"✓ Collection info retrieved:")
            print(f"  Name: {info['name']}")
            print(f"  Points: {info['points_count']}")
            print(f"  Status: {info['status']}")
        else:
            print("✗ Failed to get collection info")
            return False
        
        # Count documents
        print("\n6. Counting documents...")
        count = db.count_documents()
        print(f"✓ Current document count: {count}")
        
        print("\n" + "=" * 50)
        print("✓ All tests passed! Qdrant is ready to use.")
        print("=" * 50)
        return True
        
    except Exception as e:
        print(f"\n✗ Test failed with error:")
        print(f"  {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
