"""
Pydantic schemas for API request/response validation.

These schemas define the structure of data flowing through the API.
"""
from typing import Any

from pydantic import BaseModel, Field


# Request Schemas

class QueryRequest(BaseModel):
    """Request schema for querying the RAG system"""
    question: str = Field(
        ...,
        min_length=1,
        max_length=1000,
        description="User question to answer",
        examples=["What is machine learning?"]
    )
    top_k: int | None = Field(
        default=None,
        ge=1,
        le=20,
        description="Number of chunks to retrieve (optional)",
        examples=[5]
    )


# Response Schemas

class SourceMetadata(BaseModel):
    """Metadata for a source document"""
    filename: str = Field(..., description="Name of the source file")
    document_id: str = Field(..., description="Unique document identifier")
    chunk_id: str = Field(..., description="Unique chunk identifier")


class Source(BaseModel):
    """A source chunk used to generate the answer"""
    text: str = Field(..., description="Source text snippet")
    score: float = Field(..., description="Similarity score (0-1)")
    metadata: SourceMetadata = Field(..., description="Source metadata")


class QueryResponse(BaseModel):
    """Response schema for query endpoint"""
    answer: str = Field(..., description="Generated answer")
    sources: list[Source] = Field(
        default_factory=list,
        description="Source chunks used"
    )
    chunks_retrieved: int = Field(..., description="Number of chunks retrieved")
    total_docs: int = Field(..., description="Total documents in system")
    question: str = Field(..., description="Original question")


class UploadResponse(BaseModel):
    """Response schema for document upload"""
    success: bool = Field(..., description="Whether upload succeeded")
    document_id: str = Field(..., description="Document identifier")
    filename: str = Field(..., description="Uploaded filename")
    chunks_indexed: int = Field(..., description="Number of chunks created")
    total_chunks_in_db: int = Field(..., description="Total chunks in database")
    message: str = Field(..., description="Status message")


class DocumentInfo(BaseModel):
    """Information about an indexed document"""
    document_id: str = Field(..., description="Document identifier")


class DocumentListResponse(BaseModel):
    """Response schema for listing documents"""
    documents: list[DocumentInfo] = Field(
        default_factory=list,
        description="List of indexed documents"
    )
    total_documents: int = Field(..., description="Total number of documents")
    total_chunks: int = Field(..., description="Total number of chunks")


class DeleteResponse(BaseModel):
    """Response schema for document deletion"""
    success: bool = Field(..., description="Whether deletion succeeded")
    document_id: str = Field(..., description="Deleted document ID")
    message: str = Field(..., description="Status message")


class HealthResponse(BaseModel):
    """Response schema for health check"""
    status: str = Field(..., description="Health status")
    qdrant_connected: bool = Field(..., description="Qdrant connection status")
    total_documents: int = Field(..., description="Number of indexed documents")
    total_chunks: int = Field(..., description="Number of chunks")
    embedding_model: str = Field(..., description="Embedding model in use")
    llm_model: str = Field(..., description="LLM model in use")
    api_provider: str = Field(..., description="API provider (openai/gemini)")


class ErrorResponse(BaseModel):
    """Response schema for errors"""
    error: str = Field(..., description="Error type")
    message: str = Field(..., description="Error message")
    detail: str | None = Field(default=None, description="Additional details")
