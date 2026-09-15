"""
Script to run the FastAPI server.

Usage:
    python run_api.py
    
Then visit:
    - API docs: http://localhost:8000/docs
    - Alternative docs: http://localhost:8000/redoc
    - Root: http://localhost:8000/
"""
import uvicorn

if __name__ == "__main__":
    print("=" * 70)
    print("Starting RAG API Server")
    print("=" * 70)
    print("\n📚 Access points:")
    print("  - API Root:      http://localhost:8000/")
    print("  - Swagger UI:    http://localhost:8000/docs")
    print("  - ReDoc:         http://localhost:8000/redoc")
    print("  - Health Check:  http://localhost:8000/api/health")
    print("\n🔧 Endpoints:")
    print("  POST /api/upload       - Upload PDF")
    print("  POST /api/query        - Ask question")
    print("  GET  /api/documents    - List documents")
    print("  DELETE /api/documents/{id} - Delete document")
    print("\n" + "=" * 70)
    print("Press CTRL+C to stop\n")
    
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
