"""
Streamlit frontend for RAG Document Q&A system.

A user-friendly web interface for uploading documents and asking questions.
"""
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import streamlit as st
from app.config import get_settings
from app.rag import get_rag_pipeline

# Page configuration
st.set_page_config(
    page_title="RAG Document Q&A",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .stAlert {
        margin-top: 1rem;
    }
    .source-box {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
        border-left: 4px solid #1f77b4;
    }
    .chat-message {
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
    }
    .user-message {
        background-color: #e3f2fd;
        border-left: 4px solid #2196f3;
    }
    .assistant-message {
        background-color: #f5f5f5;
        border-left: 4px solid #4caf50;
    }
</style>
""", unsafe_allow_html=True)


@st.cache_resource
def get_rag():
    """Initialize RAG pipeline (cached)"""
    try:
        settings = get_settings()
        return get_rag_pipeline(settings), None
    except Exception as e:
        return None, str(e)


def init_session_state():
    """Initialize session state variables"""
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []
    if "uploaded_docs" not in st.session_state:
        st.session_state.uploaded_docs = []


def render_header():
    """Render page header"""
    st.markdown('<h1 class="main-header">📚 RAG Document Q&A Assistant</h1>', unsafe_allow_html=True)
    st.markdown("---")


def render_sidebar(rag):
    """Render sidebar with upload and document management"""
    with st.sidebar:
        st.header("📄 Document Management")
        
        # System Status
        with st.expander("⚙️ System Status", expanded=False):
            if rag:
                try:
                    stats = rag.get_stats()
                    st.success("✓ System Online")
                    st.metric("Documents Indexed", stats.get("unique_documents", 0))
                    st.metric("Total Chunks", stats.get("total_chunks", 0))
                    st.info(f"**LLM:** {stats.get('llm_model', 'N/A')}")
                    st.info(f"**Embeddings:** {stats.get('embedding_model', 'N/A')}")
                except Exception as e:
                    st.error(f"Error: {e}")
            else:
                st.error("✗ System Offline")
        
        st.markdown("---")
        
        # Document Upload
        st.subheader("📤 Upload Document")
        uploaded_file = st.file_uploader(
            "Upload a PDF",
            type=['pdf'],
            help="Upload a PDF document to index for question answering"
        )
        
        if uploaded_file and rag:
            if st.button("🚀 Index Document", use_container_width=True):
                with st.spinner("Processing document..."):
                    try:
                        # Save uploaded file temporarily
                        import tempfile
                        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
                            tmp_file.write(uploaded_file.getvalue())
                            tmp_path = Path(tmp_file.name)
                        
                        # Index document
                        result = rag.index_document(tmp_path)
                        
                        # Clean up
                        tmp_path.unlink(missing_ok=True)
                        
                        # Show success
                        st.success(f"✓ Indexed {result['chunks_indexed']} chunks!")
                        st.balloons()
                        
                        # Add to session state
                        st.session_state.uploaded_docs.append({
                            "filename": result["filename"],
                            "document_id": result["document_id"],
                            "chunks": result["chunks_indexed"]
                        })
                        
                    except Exception as e:
                        st.error(f"❌ Error: {e}")
        
        st.markdown("---")
        
        # Document List
        st.subheader("📋 Indexed Documents")
        
        if rag:
            try:
                doc_ids = rag.get_indexed_documents()
                if doc_ids:
                    for doc_id in doc_ids:
                        col1, col2 = st.columns([3, 1])
                        with col1:
                            st.text(f"📄 {doc_id[:30]}...")
                        with col2:
                            if st.button("🗑️", key=f"del_{doc_id}", help="Delete"):
                                with st.spinner("Deleting..."):
                                    rag.delete_document(doc_id)
                                    st.rerun()
                else:
                    st.info("No documents indexed yet")
            except Exception as e:
                st.error(f"Error loading documents: {e}")
        
        st.markdown("---")
        
        # Settings
        with st.expander("⚙️ Query Settings", expanded=False):
            top_k = st.slider(
                "Number of chunks to retrieve",
                min_value=1,
                max_value=10,
                value=5,
                help="How many relevant chunks to use for answering"
            )
            st.session_state.top_k = top_k


def render_chat_interface(rag):
    """Render main chat interface"""
    
    # Display chat history
    for i, message in enumerate(st.session_state.chat_history):
        if message["role"] == "user":
            with st.container():
                st.markdown(
                    f'<div class="chat-message user-message"><strong>You:</strong> {message["content"]}</div>',
                    unsafe_allow_html=True
                )
        else:
            with st.container():
                st.markdown(
                    f'<div class="chat-message assistant-message"><strong>Assistant:</strong> {message["content"]}</div>',
                    unsafe_allow_html=True
                )
                
                # Show sources if available
                if "sources" in message and message["sources"]:
                    with st.expander(f"📚 Sources ({len(message['sources'])} chunks used)"):
                        for j, source in enumerate(message["sources"], 1):
                            st.markdown(f"""
                            <div class="source-box">
                                <strong>Source {j}</strong> - {source['metadata']['filename']} 
                                (Score: {source['score']:.3f})<br>
                                <em>{source['text']}</em>
                            </div>
                            """, unsafe_allow_html=True)
    
    # Input area
    st.markdown("---")
    
    # Question input
    question = st.text_input(
        "💬 Ask a question about your documents:",
        placeholder="e.g., What is machine learning?",
        key="question_input"
    )
    
    col1, col2, col3 = st.columns([1, 1, 4])
    
    with col1:
        ask_button = st.button("🔍 Ask", use_container_width=True)
    
    with col2:
        clear_button = st.button("🗑️ Clear Chat", use_container_width=True)
    
    if clear_button:
        st.session_state.chat_history = []
        st.rerun()
    
    # Process question
    if ask_button and question:
        if not rag:
            st.error("❌ RAG system not initialized. Check your API keys.")
            return
        
        # Add user message to history
        st.session_state.chat_history.append({
            "role": "user",
            "content": question
        })
        
        # Get answer
        with st.spinner("🤔 Thinking..."):
            try:
                top_k = st.session_state.get("top_k", 5)
                response = rag.query(question, top_k=top_k)
                
                # Add assistant response to history
                st.session_state.chat_history.append({
                    "role": "assistant",
                    "content": response["answer"],
                    "sources": response.get("sources", [])
                })
                
                st.rerun()
                
            except Exception as e:
                st.error(f"❌ Error: {e}")
    
    elif ask_button and not question:
        st.warning("⚠️ Please enter a question")


def render_info_section():
    """Render information section"""
    with st.expander("ℹ️ How to Use", expanded=False):
        st.markdown("""
        ### 📖 Getting Started
        
        1. **Upload Documents** 📤
           - Click "Browse files" in the sidebar
           - Select a PDF document
           - Click "Index Document"
        
        2. **Ask Questions** 💬
           - Type your question in the input box
           - Click "Ask" to get an answer
           - View sources used to generate the answer
        
        3. **Manage Documents** 📋
           - View all indexed documents in the sidebar
           - Delete documents you no longer need
        
        ### 🎯 Tips
        
        - **Be specific**: Ask clear, focused questions
        - **Multiple documents**: Upload related documents for better answers
        - **Check sources**: Review which chunks were used
        - **Adjust settings**: Change retrieval count if needed
        
        ### 🔧 Technical Details
        
        - **Embeddings**: OpenAI text-embedding-3-small
        - **LLM**: Google Gemini 1.5 Flash
        - **Vector DB**: Qdrant Cloud
        - **Chunk Size**: 1024 characters with 200 overlap
        """)


def main():
    """Main application"""
    
    # Initialize
    init_session_state()
    
    # Get RAG pipeline
    rag, error = get_rag()
    
    # Render UI
    render_header()
    
    if error:
        st.error(f"❌ Failed to initialize RAG system: {error}")
        st.info("💡 Please check your `.env` file and ensure API keys are configured correctly.")
        
        with st.expander("🔧 Configuration Help"):
            st.markdown("""
            ### Required in `.env`:
            
            ```env
            # API Provider
            API_PROVIDER=gemini
            
            # OpenAI (for embeddings)
            OPENAI_API_KEY=sk-your-key-here
            
            # Gemini (for LLM)
            GEMINI_API_KEY=your-key-here
            
            # Qdrant Cloud
            QDRANT_URL=your-qdrant-url
            QDRANT_API_KEY=your-qdrant-key
            ```
            
            ### Troubleshooting:
            
            1. Verify API keys are valid
            2. Check OpenAI account has credits
            3. Test Qdrant connection: `python test_qdrant.py`
            4. Test configuration: `python app/config.py`
            """)
        return
    
    # Render main interface
    render_sidebar(rag)
    render_chat_interface(rag)
    render_info_section()
    
    # Footer
    st.markdown("---")
    st.markdown(
        '<p style="text-align: center; color: gray; font-size: 0.9rem;">'
        '📚 RAG Document Q&A Assistant | Built with Streamlit, LlamaIndex, Qdrant & Gemini'
        '</p>',
        unsafe_allow_html=True
    )


if __name__ == "__main__":
    main()
