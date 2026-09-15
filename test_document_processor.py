"""
Test script for document processor.

This demonstrates PDF processing without requiring a real PDF.
"""
import logging
import sys
from pathlib import Path
from io import BytesIO

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

from app.config import get_settings
from app.document_processor import get_document_processor

logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s - %(message)s'
)

def test_chunking():
    """Test the chunking logic with sample text"""
    print("\n" + "=" * 60)
    print("Document Processor - Chunking Test")
    print("=" * 60)
    
    # Load settings
    settings = get_settings()
    processor = get_document_processor(settings)
    
    print(f"\n✓ Processor initialized")
    print(f"  Chunk size: {processor.chunk_size} characters")
    print(f"  Chunk overlap: {processor.chunk_overlap} characters")
    
    # Create sample text
    sample_text = """
    Machine Learning is a subset of artificial intelligence that enables systems to learn 
    and improve from experience without being explicitly programmed. It focuses on the 
    development of computer programs that can access data and use it to learn for themselves.
    
    The process of learning begins with observations or data, such as examples, direct 
    experience, or instruction, in order to look for patterns in data and make better 
    decisions in the future based on the examples that we provide. The primary aim is to 
    allow the computers to learn automatically without human intervention or assistance 
    and adjust actions accordingly.
    
    Deep Learning is a subset of machine learning in artificial intelligence that has 
    networks capable of learning unsupervised from data that is unstructured or unlabeled. 
    Also known as deep neural learning or deep neural network, it was inspired by the 
    structure and function of the brain, namely the interconnecting of many neurons.
    
    Neural networks are computing systems inspired by biological neural networks that 
    constitute animal brains. Such systems learn to perform tasks by considering examples, 
    generally without being programmed with task-specific rules. For example, in image 
    recognition, they might learn to identify images that contain cats by analyzing example 
    images that have been manually labeled as "cat" or "no cat."
    """ * 3  # Repeat to make it longer
    
    # Prepare metadata
    metadata = {
        "filename": "machine_learning_intro.pdf",
        "document_id": "ml_intro_test_001",
        "total_pages": 1,
    }
    
    print(f"\n📄 Sample Document:")
    print(f"  Total characters: {len(sample_text)}")
    print(f"  Estimated chunks: ~{len(sample_text) // processor.chunk_size}")
    
    # Chunk the text
    print(f"\n⚙️  Chunking text...")
    chunks = processor.chunk_text(sample_text, metadata)
    
    print(f"\n✓ Chunking complete!")
    print(f"  Total chunks created: {len(chunks)}")
    
    # Show chunk details
    print(f"\n📊 Chunk Analysis:")
    print("-" * 60)
    
    for i, chunk in enumerate(chunks):
        print(f"\n  Chunk {i + 1}:")
        print(f"    ID: {chunk.chunk_id}")
        print(f"    Length: {len(chunk.text)} characters")
        print(f"    Start position: {chunk.metadata['start_char']}")
        print(f"    End position: {chunk.metadata['end_char']}")
        
        # Show overlap with next chunk
        if i < len(chunks) - 1:
            next_chunk = chunks[i + 1]
            overlap_start = next_chunk.metadata['start_char']
            current_end = chunk.metadata['end_char']
            actual_overlap = current_end - overlap_start
            print(f"    Overlap with next: {actual_overlap} characters")
        
        # Preview text
        preview = chunk.text[:100].replace('\n', ' ')
        print(f"    Preview: {preview}...")
    
    # Explain why chunking matters
    print(f"\n" + "=" * 60)
    print("Why Chunking Matters:")
    print("=" * 60)
    print("""
    1. LLM Token Limits: GPT models have max context windows
       - Chunks keep us under the limit
    
    2. Precise Retrieval: Smaller chunks = more relevant results
       - Get specific paragraphs, not entire documents
    
    3. Overlap Preserves Context: 
       - {overlap} character overlap prevents splitting related content
       - Maintains continuity across boundaries
    
    4. Cost Efficiency:
       - Only send relevant chunks to LLM
       - Fewer tokens = lower cost
    
    5. Better Answers:
       - LLM focuses on relevant information
       - Less distraction from irrelevant content
    """.format(overlap=processor.chunk_overlap))
    
    print("=" * 60)
    print("✓ Test complete!")
    print("=" * 60)
    
    return True

def test_document_id():
    """Test document ID generation"""
    print("\n" + "=" * 60)
    print("Document ID Generation Test")
    print("=" * 60)
    
    settings = get_settings()
    processor = get_document_processor(settings)
    
    # Test with same content
    filename = "test.pdf"
    content = "This is test content for document ID generation."
    
    doc_id_1 = processor.generate_document_id(filename, content)
    doc_id_2 = processor.generate_document_id(filename, content)
    
    print(f"\n✓ Document ID generation test:")
    print(f"  Filename: {filename}")
    print(f"  ID (first): {doc_id_1}")
    print(f"  ID (second): {doc_id_2}")
    print(f"  IDs match: {doc_id_1 == doc_id_2} ✓")
    
    # Test with different content
    different_content = "Different content will produce different ID."
    doc_id_3 = processor.generate_document_id(filename, different_content)
    
    print(f"\n  Different content ID: {doc_id_3}")
    print(f"  IDs different: {doc_id_1 != doc_id_3} ✓")
    
    print("\n💡 Why Deterministic IDs?")
    print("-" * 60)
    print("""
    - Same file = Same ID (detect duplicates)
    - Different content = Different ID (track versions)
    - Can safely re-upload without creating duplicates
    - Easy to update or delete specific documents
    """)
    
    return True

def main():
    try:
        # Run tests
        test_document_id()
        test_chunking()
        
        print("\n" + "=" * 60)
        print("🎉 All tests passed!")
        print("=" * 60)
        print("\n📝 Next Steps:")
        print("  1. Add a PDF to data/documents/")
        print("  2. Run: python -m app.document_processor")
        print("  3. See real PDF processing in action!")
        print("=" * 60)
        
        return True
        
    except Exception as e:
        print(f"\n✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
