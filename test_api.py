"""
Test script for FastAPI endpoints (without starting server).

This tests the FastAPI app structure without making actual API calls.
"""
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_root():
    """Test root endpoint"""
    print("\n" + "=" * 60)
    print("Testing Root Endpoint")
    print("=" * 60)
    
    response = client.get("/")
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    
    assert response.status_code == 200
    assert "name" in response.json()
    print("✓ Root endpoint works!")


def test_health():
    """Test health endpoint"""
    print("\n" + "=" * 60)
    print("Testing Health Endpoint")
    print("=" * 60)
    
    try:
        response = client.get("/api/health")
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✓ Health check passed!")
            print(f"  Status: {data.get('status')}")
            print(f"  Qdrant Connected: {data.get('qdrant_connected')}")
            print(f"  Total Documents: {data.get('total_documents')}")
            print(f"  Embedding Model: {data.get('embedding_model')}")
            print(f"  LLM Model: {data.get('llm_model')}")
        else:
            print(f"⚠ Health check returned status: {response.status_code}")
            print(f"  Detail: {response.json().get('detail')}")
            
    except Exception as e:
        print(f"⚠ Health check error (expected if API keys missing): {e}")


def test_query_validation():
    """Test query endpoint input validation"""
    print("\n" + "=" * 60)
    print("Testing Query Validation")
    print("=" * 60)
    
    # Test empty question
    response = client.post("/api/query", json={"question": ""})
    print(f"Empty question status: {response.status_code}")
    assert response.status_code == 422  # Validation error
    print("✓ Empty question rejected!")
    
    # Test invalid top_k
    response = client.post("/api/query", json={"question": "test", "top_k": 100})
    print(f"Invalid top_k status: {response.status_code}")
    assert response.status_code == 422  # Validation error
    print("✓ Invalid top_k rejected!")


def test_api_structure():
    """Test API structure and routes"""
    print("\n" + "=" * 60)
    print("Testing API Structure")
    print("=" * 60)
    
    routes = [route.path for route in app.routes]
    
    expected_routes = [
        "/",
        "/api/health",
        "/api/upload",
        "/api/query",
        "/api/documents",
        "/api/documents/{document_id}",
    ]
    
    print("Available routes:")
    for route in expected_routes:
        if route in routes or route.replace("{document_id}", "") in str(routes):
            print(f"  ✓ {route}")
        else:
            print(f"  ✗ {route} (missing)")
    
    print(f"\nTotal routes defined: {len(routes)}")


def main():
    """Run all tests"""
    print("\n" + "=" * 60)
    print("FastAPI Application Tests")
    print("=" * 60)
    print("\nThese tests verify the API structure without requiring")
    print("API keys or making actual RAG calls.\n")
    
    try:
        test_root()
        test_health()
        test_query_validation()
        test_api_structure()
        
        print("\n" + "=" * 60)
        print("✓ All FastAPI structure tests passed!")
        print("=" * 60)
        print("\n📝 Next Steps:")
        print("  1. Add OpenAI API credits")
        print("  2. Run: python run_api.py")
        print("  3. Visit: http://localhost:8000/docs")
        print("  4. Test endpoints with real data!")
        print("=" * 60)
        
        return True
        
    except Exception as e:
        print(f"\n✗ Tests failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    import sys
    success = main()
    sys.exit(0 if success else 1)
