"""
RAG (Retrieval-Augmented Generation) pipeline.

This module orchestrates:
- Document indexing with embeddings
- Semantic search/retrieval
- Context-aware answer generation
"""
import logging
import uuid
from pathlib import Path
from typing import Any

from llama_index.core import Document, Settings, VectorStoreIndex
from llama_index.core.node_parser import SentenceSplitter
from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.llms.openai import OpenAI
from llama_index.vector_stores.qdrant import QdrantVectorStore
from qdrant_client import QdrantClient

from app.config import Settings as AppSettings
from app.document_processor import DocumentChunk, get_document_processor
from app.qdrant_db import get_qdrant_client

logger = logging.getLogger(__name__)


class RAGPipeline:
    """
    Complete RAG pipeline for document indexing and question answering.
    
    This class handles:
    1. Document ingestion (PDF → chunks → embeddings → Qdrant)
    2. Semantic retrieval (question → embedding → similar chunks)
    3. Answer generation (chunks + question → LLM → answer)
    """
    
    def __init__(self, settings: AppSettings):
        """
        Initialize RAG pipeline.
        
        Args:
            settings: Application settings
        """
        self.settings = settings
        
        # Initialize LlamaIndex global settings
        logger.info("Initializing RAG pipeline...")
        
        # Configure embedding model
        self.embed_model = OpenAIEmbedding(
            model=settings.embedding_model,
            api_key=settings.openai_api_key,
        )
        
        # Configure LLM
        self.llm = OpenAI(
            model=settings.llm_model,
            api_key=settings.openai_api_key,
            temperature=0.1,  # Low temperature for factual answers
        )
        
        # Set LlamaIndex global configuration
        Settings.embed_model = self.embed_model
        Settings.llm = self.llm
        Settings.chunk_size = settings.chunk_size
        Settings.chunk_overlap = settings.chunk_overlap
        
        # Initialize Qdrant
        self.qdrant_db = get_qdrant_client(settings)
        
        # Ensure collection exists
        if not self.qdrant_db.collection_exists():
            logger.info("Creating Qdrant collection...")
            self.qdrant_db.create_collection()
        
        # Initialize Qdrant vector store
        self.qdrant_client = QdrantClient(
            url=settings.qdrant_url,
            api_key=settings.qdrant_api_key,
        )
        
        self.vector_store = QdrantVectorStore(
            client=self.qdrant_client,
            collection_name=settings.qdrant_collection_name,
        )
        
        # Initialize document processor
        self.doc_processor = get_document_processor(settings)
        
        # Index (will be created when needed)
        self._index = None
        
        logger.info("✓ RAG pipeline initialized successfully")
    
    @property
    def index(self) -> VectorStoreIndex:
        """
        Get or create the vector store index.
        
        Returns:
            VectorStoreIndex: LlamaIndex vector store index
        """
        if self._index is None:
            self._index = VectorStoreIndex.from_vector_store(
                vector_store=self.vector_store,
            )
        return self._index
    
    def index_document(self, pdf_path: Path) -> dict[str, Any]:
        """
        Index a PDF document into the vector store.
        
        Complete pipeline:
        1. Validate PDF
        2. Extract text and chunk
        3. Generate embeddings
        4. Store in Qdrant
        
        Args:
            pdf_path: Path to PDF file
            
        Returns:
            dict: Indexing results with document_id, chunks_count, etc.
            
        Raises:
            ValueError: If PDF is invalid
            Exception: If indexing fails
        """
        logger.info(f"Indexing document: {pdf_path.name}")
        
        try:
            # Step 1: Validate PDF
            self.doc_processor.validate_pdf(pdf_path)
            
            # Step 2: Process PDF (extract + chunk)
            document_id, chunks = self.doc_processor.process_pdf(pdf_path)
            
            if not chunks:
                raise ValueError("No chunks generated from PDF")
            
            # Step 3: Check if document already exists
            existing_docs = self.qdrant_db.get_unique_documents()
            if document_id in existing_docs:
                logger.warning(f"Document {document_id} already indexed, deleting old version")
                self.qdrant_db.delete_document(document_id)
            
            # Step 4: Convert chunks to LlamaIndex Documents
            documents = []
            for chunk in chunks:
                doc = Document(
                    text=chunk.text,
                    metadata={
                        "document_id": chunk.metadata["document_id"],
                        "filename": chunk.metadata["filename"],
                        "chunk_id": chunk.chunk_id,
                        "chunk_index": chunk.metadata["chunk_index"],
                        "total_pages": chunk.metadata.get("total_pages", 0),
                    },
                    id_=chunk.chunk_id,
                )
                documents.append(doc)
            
            logger.info(f"Generated {len(documents)} LlamaIndex documents")
            
            # Step 5: Index documents (generates embeddings + stores in Qdrant)
            logger.info("Generating embeddings and storing in Qdrant...")
            
            # Get or create index
            index = self.index
            
            # Insert documents
            for doc in documents:
                index.insert(doc)
            
            logger.info(f"✓ Successfully indexed {len(documents)} chunks")
            
            # Get collection stats
            total_docs = self.qdrant_db.count_documents()
            
            return {
                "success": True,
                "document_id": document_id,
                "filename": pdf_path.name,
                "chunks_indexed": len(chunks),
                "total_chunks_in_db": total_docs,
            }
            
        except Exception as e:
            logger.error(f"Failed to index document: {e}")
            raise
    
    def query(
        self,
        question: str,
        top_k: int | None = None,
    ) -> dict[str, Any]:
        """
        Query the RAG system with a question.
        
        Pipeline:
        1. Generate question embedding
        2. Search Qdrant for similar chunks
        3. Send chunks + question to LLM
        4. Return answer with sources
        
        Args:
            question: User question
            top_k: Number of chunks to retrieve (uses config if None)
            
        Returns:
            dict: Answer, sources, and metadata
        """
        if not question or not question.strip():
            raise ValueError("Question cannot be empty")
        
        top_k = top_k or self.settings.top_k
        
        logger.info(f"Processing query: {question[:100]}...")
        logger.info(f"Retrieving top {top_k} chunks")
        
        try:
            # Check if we have any documents
            doc_count = self.qdrant_db.count_documents()
            if doc_count == 0:
                return {
                    "answer": "I don't have any documents indexed yet. Please upload some documents first.",
                    "sources": [],
                    "chunks_retrieved": 0,
                    "total_docs": 0,
                }
            
            # Create query engine
            query_engine = self.index.as_query_engine(
                similarity_top_k=top_k,
                response_mode="compact",  # Concatenate chunks efficiently
            )
            
            # Query
            logger.info("Querying vector store and generating answer...")
            response = query_engine.query(question)
            
            # Extract sources
            sources = []
            if hasattr(response, 'source_nodes'):
                for node in response.source_nodes:
                    source = {
                        "text": node.node.text[:200] + "..." if len(node.node.text) > 200 else node.node.text,
                        "score": float(node.score) if hasattr(node, 'score') else 0.0,
                        "metadata": node.node.metadata,
                    }
                    sources.append(source)
            
            logger.info(f"✓ Retrieved {len(sources)} source chunks")
            
            return {
                "answer": str(response),
                "sources": sources,
                "chunks_retrieved": len(sources),
                "total_docs": doc_count,
                "question": question,
            }
            
        except Exception as e:
            logger.error(f"Query failed: {e}")
            raise
    
    def delete_document(self, document_id: str) -> bool:
        """
        Delete a document from the vector store.
        
        Args:
            document_id: Document ID to delete
            
        Returns:
            bool: True if successful
        """
        logger.info(f"Deleting document: {document_id}")
        return self.qdrant_db.delete_document(document_id)
    
    def get_indexed_documents(self) -> list[str]:
        """
        Get list of indexed document IDs.
        
        Returns:
            list[str]: Document IDs
        """
        return self.qdrant_db.get_unique_documents()
    
    def get_stats(self) -> dict[str, Any]:
        """
        Get RAG system statistics.
        
        Returns:
            dict: System statistics
        """
        return {
            "total_chunks": self.qdrant_db.count_documents(),
            "unique_documents": len(self.qdrant_db.get_unique_documents()),
            "collection_info": self.qdrant_db.get_collection_info(),
            "embedding_model": self.settings.embedding_model,
            "llm_model": self.settings.llm_model,
            "chunk_size": self.settings.chunk_size,
            "chunk_overlap": self.settings.chunk_overlap,
            "top_k": self.settings.top_k,
        }


def get_rag_pipeline(settings: AppSettings) -> RAGPipeline:
    """
    Factory function to create RAG pipeline.
    
    Args:
        settings: Application settings
        
    Returns:
        RAGPipeline: Configured RAG pipeline
    """
    return RAGPipeline(settings)


if __name__ == "__main__":
    # Test RAG pipeline
    import sys
    from app.config import get_settings
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    print("\n" + "=" * 60)
    print("RAG Pipeline Test")
    print("=" * 60)
    
    try:
        # Initialize
        print("\n1. Initializing RAG pipeline...")
        settings = get_settings()
        rag = get_rag_pipeline(settings)
        print("✓ RAG pipeline initialized")
        
        # Get stats
        print("\n2. Getting system statistics...")
        stats = rag.get_stats()
        print("✓ Statistics retrieved:")
        print(f"  Total chunks: {stats['total_chunks']}")
        print(f"  Unique documents: {stats['unique_documents']}")
        print(f"  Embedding model: {stats['embedding_model']}")
        print(f"  LLM model: {stats['llm_model']}")
        
        # Check for PDFs
        print("\n3. Checking for PDFs to index...")
        docs_dir = Path("data/documents")
        pdf_files = list(docs_dir.glob("*.pdf"))
        
        if pdf_files:
            print(f"✓ Found {len(pdf_files)} PDF(s)")
            
            # Index first PDF
            test_pdf = pdf_files[0]
            print(f"\n4. Indexing: {test_pdf.name}")
            result = rag.index_document(test_pdf)
            
            print("✓ Indexing complete:")
            print(f"  Document ID: {result['document_id']}")
            print(f"  Chunks indexed: {result['chunks_indexed']}")
            print(f"  Total chunks in DB: {result['total_chunks_in_db']}")
            
            # Test query
            print("\n5. Testing query...")
            test_question = "What is this document about?"
            response = rag.query(test_question)
            
            print("✓ Query complete:")
            print(f"  Question: {test_question}")
            print(f"  Answer: {response['answer'][:200]}...")
            print(f"  Sources: {response['chunks_retrieved']}")
            
        else:
            print("⚠ No PDFs found in data/documents/")
            print("  Add a PDF to test indexing and querying")
        
        print("\n" + "=" * 60)
        print("✓ RAG pipeline test complete!")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
