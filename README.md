# 📚 Production RAG Document Q&A System

A production-ready **Retrieval-Augmented Generation (RAG)** application for document-based question answering. Upload PDFs, ask questions, and get accurate answers with source citations.

[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.109+-green.svg)](https://fastapi.tiangolo.com/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.31+-red.svg)](https://streamlit.io/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

---

## ✨ Features

- 📤 **PDF Upload & Indexing** - Process and index PDF documents automatically
- 💬 **Natural Language Q&A** - Ask questions in plain English
- 🎯 **Semantic Search** - Find relevant information using vector similarity
- 📚 **Source Citations** - Every answer shows which documents were used
- 🔄 **Document Management** - Add, list, and delete indexed documents
- 🌐 **Web UI** - Clean Streamlit interface
- 🚀 **REST API** - FastAPI backend with auto-generated docs
- ⚡ **Cost-Optimized** - Hybrid approach (OpenAI embeddings + Gemini LLM)

---

## 🏗️ Architecture

```
User uploads PDF
        ↓
Text Extraction & Chunking (1024 chars, 200 overlap)
        ↓
OpenAI Embeddings (text-embedding-3-small)
        ↓
Qdrant Cloud Vector Storage
        ↓
User asks question → Generate embedding → Semantic search
        ↓
Retrieve top-K relevant chunks
        ↓
Gemini LLM generates grounded answer
        ↓
Display answer + source citations
```

### Tech Stack

- **Backend**: FastAPI, Python 3.12+
- **Frontend**: Streamlit
- **RAG Framework**: LlamaIndex
- **Vector Database**: Qdrant Cloud
- **Embeddings**: OpenAI text-embedding-3-small
- **LLM**: Google Gemini 1.5 Flash
- **PDF Processing**: pypdf
- **Configuration**: Pydantic Settings

---

## 🚀 Quick Start

### Prerequisites

- Python 3.12 or higher
- OpenAI API key (for embeddings)
- Google Gemini API key (for LLM)
- Qdrant Cloud account (free tier available)

### Installation

1. **Clone the repository**
```bash
git clone https://github.com/saishnimbalkar397/RAG.git
cd RAG
```

2. **Install uv (Python package manager)**
```bash
# Windows (PowerShell)
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"

# macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh
```

3. **Install dependencies**
```bash
uv sync
```

4. **Configure environment variables**

Create a `.env` file:
```bash
cp .env.example .env
```

Edit `.env` and add your API keys:
```env
# API Provider
API_PROVIDER=gemini

# OpenAI (for embeddings)
OPENAI_API_KEY=sk-your-openai-key-here

# Gemini (for LLM)
GEMINI_API_KEY=your-gemini-key-here

# Qdrant Cloud
QDRANT_URL=your-qdrant-url
QDRANT_API_KEY=your-qdrant-api-key
QDRANT_COLLECTION_NAME=documents

# RAG Configuration
CHUNK_SIZE=1024
CHUNK_OVERLAP=200
TOP_K=5
EMBEDDING_MODEL=text-embedding-3-small
LLM_MODEL=gemini-1.5-flash

# File Upload
MAX_FILE_SIZE_MB=10
```

5. **Run the application**

**Option A: Streamlit UI** (Recommended for users)
```bash
python run_streamlit.py
```
Visit: http://localhost:8501

**Option B: FastAPI Backend** (For developers)
```bash
python run_api.py
```
Visit: http://localhost:8000/docs

---

## 📖 Usage

### Using the Streamlit UI

1. **Upload Documents**
   - Click "Browse files" in the sidebar
   - Select a PDF document
   - Click "Index Document"

2. **Ask Questions**
   - Type your question in the chat input
   - Click "Ask" to get an answer
   - View source citations

3. **Manage Documents**
   - See all indexed documents in the sidebar
   - Delete documents you no longer need

### Using the API

```python
import requests

BASE_URL = "http://localhost:8000"

# Upload a document
with open("document.pdf", "rb") as f:
    response = requests.post(
        f"{BASE_URL}/api/upload",
        files={"file": f}
    )
print(response.json())

# Ask a question
response = requests.post(
    f"{BASE_URL}/api/query",
    json={"question": "What is this document about?"}
)
print(response.json()["answer"])
```

See [API_GUIDE.md](API_GUIDE.md) for complete API documentation.

---

## 🧪 Testing

```bash
# Test configuration
python app/config.py

# Test Qdrant connection
python test_qdrant.py

# Test document processing
python test_document_processor.py

# Test RAG pipeline (requires API credits)
python test_rag_pipeline.py

# Test FastAPI structure
python test_api.py
```

---

## 💰 Cost Analysis

### Development (Testing)
- **OpenAI Embeddings**: $0.02 per 1M tokens (~$0.50 for 100 documents)
- **Gemini LLM**: Free tier (1500 requests/day)
- **Qdrant Cloud**: Free tier
- **Total**: < $1 for extensive testing

### Production (1000 users/month)
- **OpenAI Embeddings**: ~$0.20
- **Gemini LLM**: Free tier or minimal cost
- **Qdrant Cloud**: ~$25/month
- **Total**: ~$25/month

**10x cheaper than using OpenAI for everything!**

---

## 📂 Project Structure

```
ragapp/
├── app/
│   ├── __init__.py
│   ├── config.py              # Configuration management
│   ├── qdrant_db.py           # Vector database operations
│   ├── document_processor.py  # PDF processing & chunking
│   ├── rag.py                 # RAG pipeline (core logic)
│   ├── main.py                # FastAPI application
│   └── schemas.py             # Pydantic models
│
├── frontend/
│   └── streamlit_app.py       # Streamlit UI
│
├── data/
│   └── documents/             # PDF storage
│
├── tests/                     # Unit tests (TODO)
│
├── test_*.py                  # Integration tests
├── run_api.py                 # FastAPI runner
├── run_streamlit.py           # Streamlit runner
│
├── .env                       # Environment variables (not in repo)
├── .env.example               # Template
├── pyproject.toml             # Dependencies
├── docker-compose.yml         # For local Qdrant (optional)
│
├── README.md                  # This file
├── SETUP_GUIDE.md             # Detailed setup instructions
├── API_GUIDE.md               # API documentation
└── PROJECT_STATUS.md          # Development status
```

---

## 🔧 Configuration

All settings are in `.env` and loaded via Pydantic for type safety and validation.

Key settings:
- `API_PROVIDER`: Choose "openai" or "gemini" for LLM
- `CHUNK_SIZE`: Size of text chunks (default: 1024)
- `CHUNK_OVERLAP`: Overlap between chunks (default: 200)
- `TOP_K`: Number of chunks to retrieve (default: 5)
- `MAX_FILE_SIZE_MB`: Max upload size (default: 10)

---

## 🎯 What Makes This Production-Ready?

✅ **Modular Architecture** - Clean separation of concerns  
✅ **Type Safety** - Pydantic validation throughout  
✅ **Error Handling** - Graceful degradation  
✅ **Configuration-Driven** - No hardcoded values  
✅ **Logging** - Comprehensive logging for debugging  
✅ **Testing** - Integration and unit tests  
✅ **Documentation** - Extensive guides and docstrings  
✅ **Scalable** - Cloud-native with Qdrant  
✅ **Cost-Optimized** - Hybrid API strategy  
✅ **Security** - Environment-based secrets  

---

## 🔒 Security Notes

- Never commit `.env` to Git (already in `.gitignore`)
- API keys are loaded from environment variables
- File upload validation (PDF only, size limits)
- For production: Add authentication, rate limiting, HTTPS

---

## 🐛 Troubleshooting

### "OpenAI API key is required"
- Add valid OpenAI API key to `.env`
- Ensure account has credits

### "Qdrant connection failed"
- Verify Qdrant URL and API key
- Test: `python test_qdrant.py`

### "Gemini API error"
- Check API key is valid
- Verify quota at https://aistudio.google.com/

### Upload fails
- Check PDF is valid (not corrupted)
- Verify file size < 10MB
- Review server logs

See [SETUP_GUIDE.md](SETUP_GUIDE.md) for detailed troubleshooting.

---

## 🚀 Deployment

### Docker (Coming Soon)
```bash
docker-compose up
```

### Cloud Deployment
- Deploy FastAPI on: Railway, Render, AWS, GCP
- Deploy Streamlit on: Streamlit Cloud, Heroku
- Vector DB: Already on Qdrant Cloud

---

## 🛣️ Roadmap

- [ ] Add Inngest workflow orchestration
- [ ] Implement hybrid search (vector + keyword)
- [ ] Add re-ranking for better results
- [ ] Streaming responses
- [ ] Multi-user support with authentication
- [ ] Conversation history persistence
- [ ] Docker containerization
- [ ] CI/CD pipeline
- [ ] Evaluation metrics
- [ ] Query rewriting

---

## 📚 Resources

- [OpenAI API](https://platform.openai.com/)
- [Google Gemini](https://aistudio.google.com/)
- [Qdrant Docs](https://qdrant.tech/documentation/)
- [LlamaIndex Docs](https://docs.llamaindex.ai/)
- [FastAPI Docs](https://fastapi.tiangolo.com/)
- [Streamlit Docs](https://docs.streamlit.io/)


---

## 🤝 Contributing

Contributions welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

---

## 👨‍💻 Author

**Saish Nimbalkar**
- GitHub: [@saishnimbalkar397](https://github.com/saishnimbalkar397)
- Email: saishnim03@gmail.com

---



## 🙏 Acknowledgments

Built with:
- [LlamaIndex](https://www.llamaindex.ai/) - RAG framework
- [FastAPI](https://fastapi.tiangolo.com/) - Web framework
- [Streamlit](https://streamlit.io/) - UI framework
- [Qdrant](https://qdrant.tech/) - Vector database
- [OpenAI](https://openai.com/) - Embeddings


---


