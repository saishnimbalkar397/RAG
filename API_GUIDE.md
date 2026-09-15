# RAG API - Usage Guide

## 🚀 Starting the API Server

```bash
python run_api.py
```

The server will start on: **http://localhost:8000**

## 📚 API Documentation

Once running, visit:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## 🔧 API Endpoints

### 1. Health Check
**GET** `/api/health`

Check system health and get statistics.

**Response:**
```json
{
  "status": "healthy",
  "qdrant_connected": true,
  "total_documents": 5,
  "total_chunks": 127,
  "embedding_model": "text-embedding-3-small",
  "llm_model": "gemini-1.5-flash",
  "api_provider": "gemini"
}
```

### 2. Upload Document
**POST** `/api/upload`

Upload and index a PDF document.

**Request:**
- Content-Type: `multipart/form-data`
- Body: `file` (PDF file)

**Example (curl):**
```bash
curl -X POST "http://localhost:8000/api/upload" \
  -F "file=@document.pdf"
```

**Example (Python):**
```python
import requests

with open("document.pdf", "rb") as f:
    response = requests.post(
        "http://localhost:8000/api/upload",
        files={"file": f}
    )
print(response.json())
```

**Response:**
```json
{
  "success": true,
  "document_id": "document_a1b2c3d4",
  "filename": "document.pdf",
  "chunks_indexed": 25,
  "total_chunks_in_db": 127,
  "message": "Successfully indexed 25 chunks"
}
```

### 3. Query Documents
**POST** `/api/query`

Ask a question about indexed documents.

**Request:**
```json
{
  "question": "What is machine learning?",
  "top_k": 5
}
```

**Example (curl):**
```bash
curl -X POST "http://localhost:8000/api/query" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What is machine learning?",
    "top_k": 5
  }'
```

**Example (Python):**
```python
import requests

response = requests.post(
    "http://localhost:8000/api/query",
    json={
        "question": "What is machine learning?",
        "top_k": 5
    }
)
print(response.json())
```

**Response:**
```json
{
  "answer": "Machine learning is a subset of artificial intelligence...",
  "sources": [
    {
      "text": "Machine learning enables systems to learn...",
      "score": 0.92,
      "metadata": {
        "filename": "ml_basics.pdf",
        "document_id": "ml_basics_001",
        "chunk_id": "ml_basics_001_3"
      }
    }
  ],
  "chunks_retrieved": 5,
  "total_docs": 3,
  "question": "What is machine learning?"
}
```

### 4. List Documents
**GET** `/api/documents`

Get list of all indexed documents.

**Example:**
```bash
curl http://localhost:8000/api/documents
```

**Response:**
```json
{
  "documents": [
    {"document_id": "ml_basics_001"},
    {"document_id": "deep_learning_002"},
    {"document_id": "neural_networks_003"}
  ],
  "total_documents": 3,
  "total_chunks": 127
}
```

### 5. Delete Document
**DELETE** `/api/documents/{document_id}`

Delete a document and all its chunks.

**Example:**
```bash
curl -X DELETE "http://localhost:8000/api/documents/ml_basics_001"
```

**Response:**
```json
{
  "success": true,
  "document_id": "ml_basics_001",
  "message": "Successfully deleted document: ml_basics_001"
}
```

## 🧪 Testing the API

### Using the Interactive Docs

1. Start the server: `python run_api.py`
2. Visit: http://localhost:8000/docs
3. Click on any endpoint
4. Click "Try it out"
5. Fill in parameters
6. Click "Execute"

### Using Python Requests

```python
import requests

BASE_URL = "http://localhost:8000"

# 1. Check health
health = requests.get(f"{BASE_URL}/api/health")
print("Health:", health.json())

# 2. Upload a document
with open("document.pdf", "rb") as f:
    upload = requests.post(
        f"{BASE_URL}/api/upload",
        files={"file": f}
    )
print("Upload:", upload.json())

# 3. Ask a question
query = requests.post(
    f"{BASE_URL}/api/query",
    json={"question": "What is this document about?"}
)
print("Answer:", query.json()["answer"])
print("Sources:", len(query.json()["sources"]))

# 4. List documents
docs = requests.get(f"{BASE_URL}/api/documents")
print("Documents:", docs.json())
```

## ⚙️ Configuration

The API uses settings from `.env`:

```env
# API Provider (gemini or openai)
API_PROVIDER=gemini

# API Keys
OPENAI_API_KEY=sk-...      # For embeddings
GEMINI_API_KEY=AIza...     # For LLM

# RAG Settings
CHUNK_SIZE=1024
CHUNK_OVERLAP=200
TOP_K=5

# File Upload
MAX_FILE_SIZE_MB=10
```

## 🔒 Security Notes

### For Production:

1. **CORS**: Update allowed origins in `app/main.py`:
```python
allow_origins=["https://yourdomain.com"]  # Not "*"
```

2. **API Keys**: Use environment variables, never commit to Git

3. **Rate Limiting**: Add rate limiting middleware

4. **Authentication**: Add API key or JWT authentication

5. **HTTPS**: Use HTTPS in production

6. **File Validation**: Already implemented (PDF only, size limits)

## 🐛 Troubleshooting

### Server won't start
```bash
# Check if port 8000 is in use
netstat -ano | findstr :8000

# Use different port
uvicorn app.main:app --port 8001
```

### "OpenAI API key is required"
- Add valid OpenAI API key to `.env`
- Required for embeddings even when using Gemini for LLM

### "Qdrant connection failed"
- Check Qdrant URL and API key in `.env`
- Test connection: `python test_qdrant.py`

### Upload fails
- Check file is valid PDF
- Check file size (default max: 10MB)
- Check server logs for details

## 📊 Performance Tips

### Batch Operations
Upload multiple documents before querying for better efficiency.

### Caching
The RAG pipeline is cached globally for performance.

### Async Operations
FastAPI endpoints are async-ready.

### Connection Pooling
Qdrant client handles connection pooling automatically.

## 🎯 Next Steps

1. **Test with real PDFs**: Upload documents and query them
2. **Build frontend**: Use Streamlit UI (next step)
3. **Add authentication**: Protect endpoints
4. **Deploy**: Use Docker + cloud hosting
5. **Monitor**: Add logging and metrics

## 📞 Support

- Check `/api/health` for system status
- View logs in console
- Test individual endpoints in Swagger UI
- Review error responses for details
