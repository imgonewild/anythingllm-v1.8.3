"""Main script to run the multimodal RAG system."""

import os
import sys
from typing import Optional
import argparse

from retrieval_engine import MultimodalRAGRetriever
from response_generator import MultimodalResponseGenerator
import config

def run_cli_demo():
    """Run a command-line demo of the RAG system."""
    print("🚀 Multimodal RAG System - CLI Demo")
    print("=" * 50)
    
    # Initialize system
    print("Initializing RAG system...")
    retriever = MultimodalRAGRetriever()
    generator = MultimodalResponseGenerator()
    
    print("✅ System initialized successfully!")
    
    # Show system stats
    stats = retriever.get_stats()
    print(f"\n📊 Current System Stats:")
    print(f"  - Text chunks: {stats['vector_store']['total_text_chunks']}")
    print(f"  - Image chunks: {stats['vector_store']['total_image_chunks']}")
    print(f"  - Documents: {stats['vector_store']['total_documents']}")
    
    # List documents
    documents = retriever.list_documents()
    if documents:
        print(f"\n📚 Available Documents:")
        for i, doc in enumerate(documents, 1):
            print(f"  {i}. {doc}")
    else:
        print("\n⚠️  No documents found. Please upload documents first using the web interface.")
        return
    
    # Interactive query loop
    print(f"\n🔍 Interactive Query Mode")
    print("Type your questions or 'quit' to exit.")
    print("-" * 30)
    
    while True:
        try:
            query = input("\n❓ Your question: ").strip()
            
            if query.lower() in ['quit', 'exit', 'q']:
                print("👋 Goodbye!")
                break
            
            if not query:
                continue
            
            print("🔎 Searching...")
            
            # Search for relevant content
            search_results = retriever.query(query, search_mode="hybrid")
            
            if search_results['total_results'] == 0:
                print("❌ No relevant information found.")
                continue
            
            # Generate response
            print("🤖 Generating response...")
            response_data = generator.generate_response(query, search_results['results'])
            
            # Display response
            print("\n" + "="*60)
            print("🤖 RESPONSE:")
            print("="*60)
            print(response_data['response'])
            
            # Show images info
            images = response_data.get('images', [])
            if images:
                print(f"\n🖼️  RELEVANT IMAGES ({len(images)}):")
                for i, img in enumerate(images, 1):
                    print(f"  {i}. {img.get('document_name', 'Unknown')} - Page {img.get('page_number', '?')}")
                    if img.get('caption'):
                        print(f"     Caption: {img['caption']}")
            
            # Show sources
            sources = response_data.get('sources', [])
            if sources:
                print(f"\n📚 SOURCES:")
                for i, source in enumerate(sources, 1):
                    print(f"  {i}. {source['document']} (Page {source['page']}) - {source['type']}")
            
            print(f"\n💯 Confidence: {response_data.get('confidence', 0):.0%}")
            print("="*60)
            
        except KeyboardInterrupt:
            print("\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"❌ Error: {e}")

def ingest_documents(file_paths: list):
    """Ingest documents from command line."""
    print("📄 Ingesting documents...")
    
    retriever = MultimodalRAGRetriever()
    
    results = []
    for file_path in file_paths:
        if not os.path.exists(file_path):
            print(f"❌ File not found: {file_path}")
            continue
        
        print(f"Processing: {file_path}")
        result = retriever.ingest_document(file_path)
        results.append(result)
        
        if result['status'] == 'success':
            print(f"✅ Success: {result['text_chunks']} text chunks, {result['images']} images")
        else:
            print(f"❌ Error: {result.get('error', 'Unknown error')}")
    
    # Show final stats
    stats = retriever.get_stats()
    print(f"\n📊 Final Stats:")
    print(f"  - Text chunks: {stats['vector_store']['total_text_chunks']}")
    print(f"  - Image chunks: {stats['vector_store']['total_image_chunks']}")
    print(f"  - Documents: {stats['vector_store']['total_documents']}")

def run_web_app():
    """Run the Streamlit web application."""
    import subprocess
    import sys
    
    print("🌐 Starting Streamlit web application...")
    print(f"📍 URL: http://localhost:8502")
    
    try:
        subprocess.run([
            sys.executable, "-m", "streamlit", "run", "app.py",
            "--server.port", "8502",
            "--server.address", "localhost"
        ])
    except KeyboardInterrupt:
        print("\n👋 Web application stopped.")

def main():
    """Main function with command-line interface."""
    parser = argparse.ArgumentParser(description="Multimodal RAG System")
    parser.add_argument(
        "command",
        choices=["web", "cli", "ingest"],
        help="Command to run: 'web' for web interface, 'cli' for command line demo, 'ingest' to add documents"
    )
    parser.add_argument(
        "files",
        nargs="*",
        help="Files to ingest (only for 'ingest' command)"
    )
    parser.add_argument(
        "--clear",
        action="store_true",
        help="Clear all data before ingesting (for 'ingest' command)"
    )
    
    args = parser.parse_args()
    
    # Check LLM provider configuration
    if args.command != "ingest":
        if config.LLM_PROVIDER == "ollama":
            from ollama_client import OllamaClient
            ollama = OllamaClient()
            if not ollama.is_available:
                print("⚠️  Warning: Ollama server not available.")
                print("   Start Ollama: ollama serve")
                print("   Or configure OpenAI: Set LLM_PROVIDER=openai in .env")
        elif config.LLM_PROVIDER == "openai" and not config.OPENAI_API_KEY:
            print("⚠️  Warning: OPENAI_API_KEY not set for OpenAI provider.")
            print("   Add your API key to .env file or use Ollama instead.")
        elif config.LLM_PROVIDER == "auto":
            print("ℹ️  Auto mode: Will try Ollama first, then OpenAI as fallback.")
    
    if args.command == "web":
        run_web_app()
    elif args.command == "cli":
        run_cli_demo()
    elif args.command == "ingest":
        if not args.files:
            print("❌ Error: No files specified for ingestion.")
            print("Usage: python main.py ingest <file1> <file2> ...")
            sys.exit(1)
        
        if args.clear:
            print("🗑️  Clearing all existing data...")
            retriever = MultimodalRAGRetriever()
            retriever.clear_all_documents()
        
        ingest_documents(args.files)
    
    print("\n✨ Thank you for using the Multimodal RAG System!")

if __name__ == "__main__":
    main()