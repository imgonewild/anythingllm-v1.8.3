"""Setup script for the multimodal RAG system."""

import os
import sys
import subprocess
from pathlib import Path

def check_python_version():
    """Check if Python version is compatible."""
    if sys.version_info < (3, 8):
        print("❌ Error: Python 3.8 or higher is required")
        print(f"   Current version: {sys.version}")
        sys.exit(1)
    else:
        print(f"✅ Python version: {sys.version_info.major}.{sys.version_info.minor}")

def install_dependencies():
    """Install required dependencies."""
    print("📦 Installing dependencies...")
    
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("✅ Dependencies installed successfully")
    except subprocess.CalledProcessError as e:
        print(f"❌ Error installing dependencies: {e}")
        print("💡 Try running: pip install -r requirements.txt manually")
        return False
    
    return True

def create_directories():
    """Create necessary directories."""
    print("📁 Creating directories...")
    
    directories = [
        "uploads",
        "processed", 
        "vector_db"
    ]
    
    for directory in directories:
        Path(directory).mkdir(exist_ok=True)
        print(f"   Created: {directory}/")
    
    print("✅ Directories created")

def setup_environment():
    """Setup environment file."""
    print("🔧 Setting up environment...")
    
    env_file = Path(".env")
    env_example = Path(".env.example")
    
    if not env_file.exists():
        if env_example.exists():
            # Copy example to .env
            with open(env_example, 'r') as f:
                content = f.read()
            
            with open(env_file, 'w') as f:
                f.write(content)
            
            print("✅ Created .env file from .env.example")
        else:
            # Create basic .env file
            with open(env_file, 'w') as f:
                f.write("# Multimodal RAG System Environment Variables\n")
                f.write("# Required for GPT-based responses\n")
                f.write("OPENAI_API_KEY=your_openai_api_key_here\n\n")
                f.write("# Optional: For additional embedding models\n")
                f.write("HUGGINGFACE_API_KEY=your_huggingface_api_key_here\n")
            
            print("✅ Created .env file")
        
        print("⚠️  Please edit .env and add your API keys")
    else:
        print("✅ .env file already exists")

def check_system_requirements():
    """Check system requirements."""
    print("🔍 Checking system requirements...")
    
    # Check available memory (rough estimate)
    try:
        import psutil
        memory_gb = psutil.virtual_memory().total / (1024**3)
        print(f"   Available memory: {memory_gb:.1f} GB")
        
        if memory_gb < 4:
            print("⚠️  Warning: Less than 4GB RAM detected. System may run slowly.")
        else:
            print("✅ Sufficient memory available")
    except ImportError:
        print("   Could not check memory (psutil not installed)")
    
    # Check disk space
    try:
        disk_usage = os.statvfs('.')
        free_gb = (disk_usage.f_bavail * disk_usage.f_frsize) / (1024**3)
        print(f"   Free disk space: {free_gb:.1f} GB")
        
        if free_gb < 2:
            print("⚠️  Warning: Less than 2GB free space. Models may not download properly.")
        else:
            print("✅ Sufficient disk space available")
    except (AttributeError, OSError):
        print("   Could not check disk space")

def test_installation():
    """Test if the installation works."""
    print("🧪 Testing installation...")
    
    try:
        # Test imports
        from document_processor import DocumentProcessor
        from embedding_system import MultimodalEmbedder
        from vector_store import MultimodalVectorStore
        from retrieval_engine import MultimodalRAGRetriever
        from response_generator import MultimodalResponseGenerator
        
        print("✅ All modules imported successfully")
        
        # Test basic initialization (without loading models)
        print("   Testing document processor...")
        doc_processor = DocumentProcessor()
        print("   ✅ Document processor OK")
        
        print("   Testing vector store...")
        vector_store = MultimodalVectorStore()
        print("   ✅ Vector store OK")
        
        print("✅ Installation test passed")
        return True
        
    except Exception as e:
        print(f"❌ Installation test failed: {e}")
        return False

def main():
    """Main setup function."""
    print("🚀 Multimodal RAG System Setup")
    print("=" * 40)
    
    # Check Python version
    check_python_version()
    
    # Install dependencies
    if not install_dependencies():
        sys.exit(1)
    
    # Create directories
    create_directories()
    
    # Setup environment
    setup_environment()
    
    # Check system requirements
    check_system_requirements()
    
    # Test installation
    if not test_installation():
        print("\n❌ Setup completed with errors")
        print("💡 Try running the installation manually or check the error messages above")
        sys.exit(1)
    
    print("\n" + "=" * 40)
    print("🎉 Setup completed successfully!")
    print("\n📋 Next steps:")
    print("1. Edit .env file and add your OpenAI API key")
    print("2. Run the web interface: python main.py web")
    print("3. Upload documents and start asking questions!")
    print("\n💡 For more information, see README.md")
    print("=" * 40)

if __name__ == "__main__":
    main()