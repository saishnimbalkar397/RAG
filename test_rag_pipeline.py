"""
Test RAG pipeline with synthetic data (no PDF required).
"""
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from llama_index.core import Document
from app.config import get_settings
from app.rag import get_rag_pipeline

logging.basicConfig(
    level=logging.WARNING,  # Reduce noise
    format='%(levelname)s - %(message)s'
)

def test_rag_with_sample_data():
    """Test RAG pipeline with sample documents"""
    print("\n" + "=" * 70)
    print("RAG Pipeline - Full Integration Test")
    print("=" * 70)
    
    print("\n📚 This test demonstrates:")
    print("  1. Document indexing (text → embeddings → Qdrant)")
    print("  2. Semantic search (question → similar chunks)")
    print("  3. Answer generation (chunks + question → LLM → answer)")
    
    try:
        # Initialize RAG
        print("\n" + "-" * 70)
        print("Step 1: Initializing RAG Pipeline")
        print("-" * 70)
        
        settings = get_settings()
        rag = get_rag_pipeline(settings)
        
        print("✓ RAG pipeline initialized")
        print(f"  Embedding model: {settings.embedding_model}")
        print(f"  LLM model: {settings.llm_model}")
        print(f"  Qdrant URL: {settings.qdrant_url[:50]}...")
        
        # Create sample documents
        print("\n" + "-" * 70)
        print("Step 2: Creating Sample Documents")
        print("-" * 70)
        
        sample_docs = [
            {
                "text": """
                Machine Learning is a subset of artificial intelligence that enables 
                systems to learn and improve from experience without being explicitly 
                programmed. It focuses on the development of computer programs that 
                can access data and use it to learn for themselves. The primary aim 
                is to allow computers to learn automatically without human intervention.
                """,
                "metadata": {
                    "document_id": "ml_basics_001",
                    "filename": "ml_basics.pdf",
                    "chunk_id": "ml_basics_001_0",
                    "chunk_index": 0,
                }
            },
            {
                "text": """
                Deep Learning is a subset of machine learning that uses neural networks 
                with multiple layers. These networks are inspired by the structure of 
                the human brain. Deep learning has revolutionized fields like computer 
                vision, natural language processing, and speech recognition. It can 
                automatically learn representations from data.
                """,
                "metadata": {
                    "document_id": "dl_intro_001",
                    "filename": "deep_learning_intro.pdf",
                    "chunk_id": "dl_intro_001_0",
                    "chunk_index": 0,
                }
            },
            {
                "text": """
                Neural Networks are computing systems inspired by biological neural 
                networks. They consist of interconnected nodes (neurons) organized in 
                layers. Each connection has a weight that adjusts during training. 
                Neural networks can learn complex patterns and relationships in data 
                through a process called backpropagation.
                """,
                "metadata": {
                    "document_id": "nn_fundamentals_001",
                    "filename": "neural_networks.pdf",
                    "chunk_id": "nn_fundamentals_001_0",
                    "chunk_index": 0,
                }
            },
        ]
        
        print(f"✓ Created {len(sample_docs)} sample documents")
        for doc in sample_docs:
            print(f"  - {doc['metadata']['filename']}")
        
        # Index documents
        print("\n" + "-" * 70)
        print("Step 3: Indexing Documents")
        print("-" * 70)
        print("  (Generating embeddings and storing in Qdrant...)")
        
        # Convert to LlamaIndex Documents
        documents = [
            Document(
                text=doc["text"],
                metadata=doc["metadata"],
                id_=doc["metadata"]["chunk_id"],
            )
            for doc in sample_docs
        ]
        
        # Index them
        index = rag.index
        for doc in documents:
            index.insert(doc)
        
        print(f"✓ Indexed {len(documents)} documents")
        
        # Get stats
        stats = rag.get_stats()
        print(f"  Total chunks in database: {stats['total_chunks']}")
        
        # Test queries
        print("\n" + "-" * 70)
        print("Step 4: Testing Semantic Search & Answer Generation")
        print("-" * 70)
        
        test_questions = [
            "What is machine learning?",
            "Explain deep learning and neural networks",
            "How do neural networks learn?",
        ]
        
        for i, question in enumerate(test_questions, 1):
            print(f"\n💬 Query {i}: {question}")
            print("-" * 70)
            
            response = rag.query(question, top_k=2)
            
            print(f"✓ Answer generated ({response['chunks_retrieved']} chunks retrieved):")
            print(f"\n{response['answer']}\n")
            
            if response['sources']:
                print("📄 Sources:")
                for j, source in enumerate(response['sources'], 1):
                    print(f"  {j}. {source['metadata']['filename']}")
                    print(f"     Similarity: {source['score']:.3f}")
                    print(f"     Preview: {source['text'][:100]}...\n")
        
        # Explain what happened
        print("\n" + "=" * 70)
        print("What Just Happened? (Under the Hood)")
        print("=" * 70)
        print("""
1. INDEXING PHASE:
   Document Text → OpenAI API → Embeddings (1536-dim vectors)
   Embeddings → Qdrant Cloud → Stored with metadata

2. QUERY PHASE:
   User Question → OpenAI API → Question Embedding
   Question Embedding → Qdrant → Cosine Similarity Search
   Top-K Similar Chunks → Retrieved
   
3. GENERATION PHASE:
   Retrieved Chunks + Question → System Prompt
   System Prompt → OpenAI LLM (gpt-4o-mini)
   LLM → Grounded Answer (based on retrieved context)

4. WHY THIS WORKS:
   - Semantic search: "machine learning" finds "ML", "AI" without exact match
   - Cosine similarity: Measures meaning, not keywords
   - Grounded answers: LLM only uses provided context
   - Sources tracked: Know where answers come from
        """)
        
        print("=" * 70)
        print("✓ RAG Pipeline Test Complete!")
        print("=" * 70)
        
        print("\n📝 Next Steps:")
        print("  1. Add real PDFs to data/documents/")
        print("  2. Index them with: rag.index_document(pdf_path)")
        print("  3. Ask questions about your documents!")
        print("  4. Build the FastAPI backend (coming next)")
        
        return True
        
    except Exception as e:
        print(f"\n✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_rag_with_sample_data()
    sys.exit(0 if success else 1)
