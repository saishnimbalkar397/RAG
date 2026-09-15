"""
Document processing module for PDF ingestion and chunking.

This module handles:
- PDF text extraction
- Text chunking with overlap
- Metadata preservation
- Document ID generation
"""
import hashlib
import logging
from pathlib import Path
from typing import Any

from pypdf import PdfReader

from app.config import Settings

logger = logging.getLogger(__name__)


class DocumentChunk:
    """
    Represents a single chunk of text from a document.
    
    Attributes:
        text: The chunk text content
        metadata: Dictionary containing document metadata
        chunk_id: Unique identifier for this chunk
    """
    
    def __init__(self, text: str, metadata: dict[str, Any], chunk_id: str):
        self.text = text
        self.metadata = metadata
        self.chunk_id = chunk_id
    
    def __repr__(self) -> str:
        return f"DocumentChunk(chunk_id={self.chunk_id}, length={len(self.text)})"


class DocumentProcessor:
    """
    Processes PDF documents for RAG ingestion.
    
    Handles PDF reading, text extraction, chunking, and metadata management.
    """
    
    def __init__(self, settings: Settings):
        """
        Initialize document processor.
        
        Args:
            settings: Application settings
        """
        self.settings = settings
        self.chunk_size = settings.chunk_size
        self.chunk_overlap = settings.chunk_overlap
        
        logger.info(
            f"DocumentProcessor initialized: "
            f"chunk_size={self.chunk_size}, "
            f"chunk_overlap={self.chunk_overlap}"
        )
    
    def generate_document_id(self, filename: str, content: str) -> str:
        """
        Generate a deterministic document ID based on filename and content.
        
        This allows us to:
        - Detect duplicate uploads
        - Replace old versions of documents
        - Track documents across sessions
        
        Args:
            filename: Original filename
            content: Document text content
            
        Returns:
            str: Hex string document ID
        """
        # Combine filename and content hash for uniqueness
        content_hash = hashlib.sha256(content.encode()).hexdigest()[:16]
        filename_clean = Path(filename).stem  # Remove extension
        
        # Create a short, readable ID
        doc_id = f"{filename_clean}_{content_hash}"
        return doc_id
    
    def extract_text_from_pdf(self, pdf_path: Path) -> tuple[str, dict[str, Any]]:
        """
        Extract text from a PDF file.
        
        Args:
            pdf_path: Path to PDF file
            
        Returns:
            tuple: (full_text, metadata_dict)
            
        Raises:
            ValueError: If PDF is invalid or empty
            Exception: If PDF reading fails
        """
        try:
            logger.info(f"Extracting text from PDF: {pdf_path.name}")
            
            reader = PdfReader(pdf_path)
            
            # Validate PDF
            if len(reader.pages) == 0:
                raise ValueError("PDF has no pages")
            
            # Extract text from all pages
            full_text = ""
            page_texts = []
            
            for page_num, page in enumerate(reader.pages, start=1):
                text = page.extract_text()
                page_texts.append((page_num, text))
                full_text += text + "\n\n"
            
            # Extract metadata
            metadata = reader.metadata or {}
            pdf_metadata = {
                "filename": pdf_path.name,
                "total_pages": len(reader.pages),
                "title": metadata.get("/Title", ""),
                "author": metadata.get("/Author", ""),
                "subject": metadata.get("/Subject", ""),
            }
            
            if not full_text.strip():
                raise ValueError("PDF contains no extractable text")
            
            logger.info(
                f"Extracted {len(full_text)} characters from "
                f"{len(reader.pages)} pages"
            )
            
            return full_text, pdf_metadata
            
        except Exception as e:
            logger.error(f"Failed to extract text from PDF: {e}")
            raise
    
    def chunk_text(
        self,
        text: str,
        metadata: dict[str, Any],
    ) -> list[DocumentChunk]:
        """
        Split text into overlapping chunks.
        
        Why chunking?
        - LLMs have token limits
        - Smaller chunks = more precise retrieval
        - Overlap preserves context across boundaries
        
        Why overlap?
        - Prevents splitting related sentences
        - Maintains context continuity
        - Improves retrieval quality
        
        Args:
            text: Full document text
            metadata: Document metadata
            
        Returns:
            list[DocumentChunk]: List of text chunks with metadata
        """
        logger.info("Chunking document...")
        
        # Clean text
        text = text.strip()
        
        if not text:
            logger.warning("Empty text provided for chunking")
            return []
        
        chunks = []
        start = 0
        chunk_num = 0
        
        while start < len(text):
            # Extract chunk
            end = start + self.chunk_size
            chunk_text = text[start:end]
            
            # If not the last chunk, try to break at sentence/word boundary
            if end < len(text):
                # Look for sentence endings
                last_period = chunk_text.rfind('. ')
                last_newline = chunk_text.rfind('\n')
                last_space = chunk_text.rfind(' ')
                
                # Use the best boundary found
                boundary = max(last_period, last_newline, last_space)
                if boundary > self.chunk_size * 0.5:  # At least 50% of chunk
                    end = start + boundary + 1
                    chunk_text = text[start:end]
            
            # Create chunk with metadata
            chunk_metadata = {
                **metadata,
                "chunk_index": chunk_num,
                "start_char": start,
                "end_char": end,
            }
            
            # Generate chunk ID
            chunk_id = f"{metadata.get('document_id', 'unknown')}_{chunk_num}"
            
            chunk = DocumentChunk(
                text=chunk_text.strip(),
                metadata=chunk_metadata,
                chunk_id=chunk_id,
            )
            
            chunks.append(chunk)
            
            # Move start forward with overlap
            if end >= len(text):
                break
            
            start = end - self.chunk_overlap
            chunk_num += 1
        
        logger.info(f"Created {len(chunks)} chunks")
        return chunks
    
    def process_pdf(self, pdf_path: Path) -> tuple[str, list[DocumentChunk]]:
        """
        Complete PDF processing pipeline.
        
        Steps:
        1. Extract text and metadata from PDF
        2. Generate document ID
        3. Chunk text with overlap
        4. Return document ID and chunks
        
        Args:
            pdf_path: Path to PDF file
            
        Returns:
            tuple: (document_id, list of chunks)
            
        Raises:
            ValueError: If PDF is invalid
            Exception: If processing fails
        """
        logger.info(f"Processing PDF: {pdf_path.name}")
        
        # Step 1: Extract text
        full_text, pdf_metadata = self.extract_text_from_pdf(pdf_path)
        
        # Step 2: Generate document ID
        document_id = self.generate_document_id(pdf_path.name, full_text)
        logger.info(f"Generated document ID: {document_id}")
        
        # Step 3: Add document ID to metadata
        pdf_metadata["document_id"] = document_id
        
        # Step 4: Chunk text
        chunks = self.chunk_text(full_text, pdf_metadata)
        
        logger.info(f"Successfully processed PDF: {pdf_path.name}")
        logger.info(f"  Document ID: {document_id}")
        logger.info(f"  Total chunks: {len(chunks)}")
        logger.info(f"  Total characters: {len(full_text)}")
        
        return document_id, chunks
    
    def validate_pdf(self, file_path: Path, max_size_mb: int | None = None) -> None:
        """
        Validate PDF file before processing.
        
        Args:
            file_path: Path to PDF file
            max_size_mb: Maximum file size in MB (uses config if None)
            
        Raises:
            ValueError: If validation fails
        """
        max_size = max_size_mb or self.settings.max_file_size_mb
        
        # Check file exists
        if not file_path.exists():
            raise ValueError(f"File not found: {file_path}")
        
        # Check file extension
        if file_path.suffix.lower() != '.pdf':
            raise ValueError(f"Not a PDF file: {file_path.suffix}")
        
        # Check file size
        file_size_mb = file_path.stat().st_size / (1024 * 1024)
        if file_size_mb > max_size:
            raise ValueError(
                f"PDF too large: {file_size_mb:.1f}MB "
                f"(max: {max_size}MB)"
            )
        
        # Check if it's actually a PDF (magic bytes)
        with open(file_path, 'rb') as f:
            magic_bytes = f.read(4)
            if magic_bytes != b'%PDF':
                raise ValueError("File is not a valid PDF")
        
        logger.info(f"PDF validation passed: {file_path.name} ({file_size_mb:.1f}MB)")


def get_document_processor(settings: Settings) -> DocumentProcessor:
    """
    Factory function to create DocumentProcessor instance.
    
    Args:
        settings: Application settings
        
    Returns:
        DocumentProcessor: Configured processor
    """
    return DocumentProcessor(settings)


if __name__ == "__main__":
    # Test document processor
    import sys
    from app.config import get_settings
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    print("\n" + "=" * 50)
    print("Document Processor Test")
    print("=" * 50)
    print("\nNote: Place a test PDF in data/documents/ to test")
    print("=" * 50)
    
    try:
        settings = get_settings()
        processor = get_document_processor(settings)
        
        print(f"\n✓ Processor initialized")
        print(f"  Chunk size: {processor.chunk_size}")
        print(f"  Chunk overlap: {processor.chunk_overlap}")
        
        # Look for test PDFs
        docs_dir = Path("data/documents")
        pdf_files = list(docs_dir.glob("*.pdf"))
        
        if not pdf_files:
            print(f"\n⚠ No PDF files found in {docs_dir}")
            print("  Add a PDF file to test processing")
            sys.exit(0)
        
        # Process first PDF found
        test_pdf = pdf_files[0]
        print(f"\nProcessing: {test_pdf.name}")
        print("-" * 50)
        
        # Validate
        processor.validate_pdf(test_pdf)
        print("✓ Validation passed")
        
        # Process
        doc_id, chunks = processor.process_pdf(test_pdf)
        
        print(f"\n✓ Processing complete!")
        print(f"  Document ID: {doc_id}")
        print(f"  Total chunks: {len(chunks)}")
        
        if chunks:
            print(f"\n  First chunk preview:")
            print(f"    Chunk ID: {chunks[0].chunk_id}")
            print(f"    Length: {len(chunks[0].text)} chars")
            print(f"    Text preview: {chunks[0].text[:200]}...")
        
        print("\n" + "=" * 50)
        print("✓ Test complete!")
        print("=" * 50)
        
    except Exception as e:
        print(f"\n✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
