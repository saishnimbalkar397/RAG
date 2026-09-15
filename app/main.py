"""
FastAPI application for RAG system.

This is the main entry point for the REST API.
"""
import logging
import tempfile
from pathlib import Path
from typing import Annotated

from fastapi import FastAPI, File, HTTPException, UploadFile, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import get_settings
from app.rag import get_rag_pipeline
from app.schemas import (
    DeleteResponse,
    DocumentListResponse,
    ErrorResponse,
    HealthResponse,
    QueryRequest,
    QueryResponse,
    Source,
    SourceMetadata,
    UploadResponse,
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="RAG Document Q&A API",
    description="Production-ready RAG system for document-based question answering",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify actual origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize settings and RAG pipeline
settings = get_settings()

# Global RAG pipeline instance (initialized on first use)
_rag_pipeline = None


def get_rag() -> any:
    """
    Get or create RAG pipeline instance.
    
    Lazy initialization to avoid startup errors if API keys are missing.
    """
    global _rag_pipeline
    if _rag_pipeline is None:
        try:
            _rag_pipeline = get_rag_pipeline(settings)
            logger.info("RAG pipeline initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize RAG pipeline: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to initialize RAG system: {str(e)}"
            )
    return _rag_pipeline


@app.get("/", tags=["Root"])
async def root():
    """Root endpoint with API information"""
    return {
        "name": "RAG Document Q&A API",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs",
        "health": "/api/health",
    }


@app.get(
    "/api/health",
    response_model=HealthResponse,
    tags=["Health"],
    summary="Health check endpoint"
)
async def health_check():
    """
    Check system health and return statistics.
    
    Returns:
        HealthResponse: System health information
    """
    try:
        rag = get_rag()
        stats = rag.get_stats()
        
        return HealthResponse(
            status="healthy",
            qdrant_connected=rag.qdrant_db.health_check(),
            total_documents=stats.get("unique_documents", 0),
            total_chunks=stats.get("total_chunks", 0),
            embedding_model=stats.get("embedding_model", "unknown"),
            llm_model=stats.get("llm_model", "unknown"),
            api_provider=settings.api_provider,
        )
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"System unhealthy: {str(e)}"
        )


@app.post(
    "/api/upload",
    response_model=UploadResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Documents"],
    summary="Upload and index a PDF document"
)
async def upload_document(
    file: Annotated[UploadFile, File(description="PDF file to upload")]
):
    """
    Upload a PDF document and index it for question answering.
    
    The document will be:
    1. Validated (PDF format, size limits)
    2. Processed (text extraction, chunking)
    3. Indexed (embeddings generated, stored in Qdrant)
    
    Args:
        file: PDF file to upload
        
    Returns:
        UploadResponse: Upload results with document ID and statistics
        
    Raises:
        HTTPException: If upload fails
    """
    # Validate file type
    if not file.filename.endswith('.pdf'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only PDF files are supported"
        )
    
    # Validate file size
    max_size = settings.max_file_size_mb * 1024 * 1024
    
    try:
        rag = get_rag()
        
        # Save uploaded file to temporary location
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
            content = await file.read()
            
            # Check size
            if len(content) > max_size:
                raise HTTPException(
                    status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                    detail=f"File too large. Maximum size: {settings.max_file_size_mb}MB"
                )
            
            tmp_file.write(content)
            tmp_path = Path(tmp_file.name)
        
        try:
            # Index the document
            logger.info(f"Indexing document: {file.filename}")
            result = rag.index_document(tmp_path)
            
            return UploadResponse(
                success=True,
                document_id=result["document_id"],
                filename=result["filename"],
                chunks_indexed=result["chunks_indexed"],
                total_chunks_in_db=result["total_chunks_in_db"],
                message=f"Successfully indexed {result['chunks_indexed']} chunks"
            )
            
        finally:
            # Clean up temp file
            tmp_path.unlink(missing_ok=True)
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Upload failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process document: {str(e)}"
        )


@app.post(
    "/api/query",
    response_model=QueryResponse,
    tags=["Query"],
    summary="Ask a question about indexed documents"
)
async def query_documents(request: QueryRequest):
    """
    Ask a question and get an answer based on indexed documents.
    
    The system will:
    1. Generate an embedding for your question
    2. Search for similar document chunks
    3. Send relevant chunks to the LLM
    4. Generate a grounded answer with sources
    
    Args:
        request: Query request with question and optional top_k
        
    Returns:
        QueryResponse: Answer with source citations
        
    Raises:
        HTTPException: If query fails
    """
    try:
        rag = get_rag()
        
        logger.info(f"Processing query: {request.question[:100]}")
        response = rag.query(
            question=request.question,
            top_k=request.top_k,
        )
        
        # Convert sources to response format
        sources = [
            Source(
                text=src["text"],
                score=src["score"],
                metadata=SourceMetadata(
                    filename=src["metadata"].get("filename", "Unknown"),
                    document_id=src["metadata"].get("document_id", "Unknown"),
                    chunk_id=src["metadata"].get("chunk_id", "Unknown"),
                )
            )
            for src in response.get("sources", [])
        ]
        
        return QueryResponse(
            answer=response["answer"],
            sources=sources,
            chunks_retrieved=response["chunks_retrieved"],
            total_docs=response["total_docs"],
            question=response["question"],
        )
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Query failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process query: {str(e)}"
        )


@app.get(
    "/api/documents",
    response_model=DocumentListResponse,
    tags=["Documents"],
    summary="List all indexed documents"
)
async def list_documents():
    """
    Get a list of all indexed documents.
    
    Returns:
        DocumentListResponse: List of document IDs and statistics
    """
    try:
        rag = get_rag()
        
        document_ids = rag.get_indexed_documents()
        stats = rag.get_stats()
        
        return DocumentListResponse(
            documents=[{"document_id": doc_id} for doc_id in document_ids],
            total_documents=len(document_ids),
            total_chunks=stats.get("total_chunks", 0),
        )
        
    except Exception as e:
        logger.error(f"Failed to list documents: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list documents: {str(e)}"
        )


@app.delete(
    "/api/documents/{document_id}",
    response_model=DeleteResponse,
    tags=["Documents"],
    summary="Delete a document"
)
async def delete_document(document_id: str):
    """
    Delete a document and all its chunks from the system.
    
    Args:
        document_id: ID of document to delete
        
    Returns:
        DeleteResponse: Deletion result
        
    Raises:
        HTTPException: If deletion fails
    """
    try:
        rag = get_rag()
        
        # Check if document exists
        existing_docs = rag.get_indexed_documents()
        if document_id not in existing_docs:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Document not found: {document_id}"
            )
        
        # Delete document
        success = rag.delete_document(document_id)
        
        if success:
            return DeleteResponse(
                success=True,
                document_id=document_id,
                message=f"Successfully deleted document: {document_id}"
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to delete document: {document_id}"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Delete failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete document: {str(e)}"
        )


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler for unexpected errors"""
    logger.error(f"Unexpected error: {exc}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "InternalServerError",
            "message": "An unexpected error occurred",
            "detail": str(exc) if settings.environment == "development" else None
        }
    )


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
