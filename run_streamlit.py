"""
Script to run the Streamlit frontend.

Usage:
    python run_streamlit.py
    
Then visit:
    http://localhost:8501
"""
import subprocess
import sys

if __name__ == "__main__":
    print("=" * 70)
    print("Starting RAG Streamlit Frontend")
    print("=" * 70)
    print("\n🌐 The app will open in your browser at:")
    print("   http://localhost:8501")
    print("\n✨ Features:")
    print("   - 📤 Upload PDF documents")
    print("   - 💬 Ask questions in chat interface")
    print("   - 📚 View source citations")
    print("   - 📋 Manage indexed documents")
    print("\n" + "=" * 70)
    print("Press CTRL+C to stop\n")
    
    subprocess.run([
        sys.executable, "-m", "streamlit", "run",
        "frontend/streamlit_app.py",
        "--server.port=8501",
        "--server.address=localhost",
        "--server.headless=true"
    ])
