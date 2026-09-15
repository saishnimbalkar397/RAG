"""
Verification script to check if the environment is set up correctly.
"""
import sys
from pathlib import Path

def check_python_version():
    """Check if Python version is >= 3.12"""
    version = sys.version_info
    print(f"✓ Python version: {version.major}.{version.minor}.{version.micro}")
    if version.major >= 3 and version.minor >= 12:
        return True
    print("✗ Python 3.12+ required")
    return False

def check_dependencies():
    """Check if all required packages are installed"""
    required_packages = [
        "fastapi",
        "uvicorn",
        "llama_index",
        "qdrant_client",
        "openai",
        "inngest",
        "streamlit",
        "pypdf",
        "dotenv"
    ]
    
    missing = []
    for package in required_packages:
        try:
            __import__(package)
            print(f"✓ {package} installed")
        except ImportError:
            print(f"✗ {package} missing")
            missing.append(package)
    
    return len(missing) == 0

def check_project_structure():
    """Check if project structure is correct"""
    required_dirs = [
        "app",
        "data/documents",
        "frontend",
        "tests"
    ]
    
    all_exist = True
    for dir_path in required_dirs:
        path = Path(dir_path)
        if path.exists():
            print(f"✓ Directory exists: {dir_path}")
        else:
            print(f"✗ Directory missing: {dir_path}")
            all_exist = False
    
    return all_exist

def check_env_file():
    """Check if .env.example exists"""
    if Path(".env.example").exists():
        print("✓ .env.example exists")
        return True
    print("✗ .env.example missing")
    return False

def main():
    print("=" * 50)
    print("RAG Application Setup Verification")
    print("=" * 50)
    print()
    
    checks = [
        ("Python Version", check_python_version),
        ("Dependencies", check_dependencies),
        ("Project Structure", check_project_structure),
        ("Environment Template", check_env_file),
    ]
    
    results = []
    for name, check_func in checks:
        print(f"\nChecking {name}:")
        print("-" * 50)
        results.append(check_func())
    
    print("\n" + "=" * 50)
    if all(results):
        print("✓ All checks passed! You're ready to proceed.")
    else:
        print("✗ Some checks failed. Please fix the issues above.")
    print("=" * 50)

if __name__ == "__main__":
    main()
