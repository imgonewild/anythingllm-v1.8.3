"""Example usage of the multimodal RAG system."""

import os
from retrieval_engine import MultimodalRAGRetriever
from response_generator import MultimodalResponseGenerator

def example_basic_usage():
    """Basic example of using the RAG system."""
    print("🚀 Basic RAG System Example")
    print("=" * 40)
    
    # Initialize the system
    retriever = MultimodalRAGRetriever()
    generator = MultimodalResponseGenerator()
    
    # Example document ingestion (you would replace with your actual documents)
    print("📄 Document ingestion example:")
    print("  retriever.ingest_document('user_manual.pdf')")
    print("  retriever.ingest_document('installation_guide.docx')")
    
    # Example queries
    example_queries = [
        "How do I install the software?",
        "What are the system requirements?", 
        "Show me the network diagram",
        "How do I troubleshoot connection issues?",
        "What does the main interface look like?"
    ]
    
    print("\n🔍 Example queries:")
    for i, query in enumerate(example_queries, 1):
        print(f"  {i}. {query}")
    
    # Example search and response generation
    print("\n🤖 Example search and response:")
    example_query = "How do I install the software?"
    
    print(f"Query: {example_query}")
    
    # This would normally return actual results
    print("Search results would include:")
    print("  - Text chunks about installation steps")
    print("  - Screenshots of installation dialogs")
    print("  - System requirement diagrams")
    
    print("\nGenerated response would combine:")
    print("  - Step-by-step installation instructions")
    print("  - Relevant screenshots and diagrams")
    print("  - Source citations with confidence scores")

def example_advanced_usage():
    """Advanced example showing different search modes."""
    print("\n🔬 Advanced Usage Example")
    print("=" * 40)
    
    retriever = MultimodalRAGRetriever()
    generator = MultimodalResponseGenerator()
    
    query = "What does the system architecture look like?"
    
    # Different search modes
    print("🔍 Different search modes:")
    
    print("\n1. Hybrid Search (text + images):")
    print("   results = retriever.query(query, search_mode='hybrid')")
    print("   → Finds both textual descriptions AND architectural diagrams")
    
    print("\n2. Image-only Search:")
    print("   results = retriever.query(query, search_mode='image')")
    print("   → Finds only diagrams, charts, and visual content")
    
    print("\n3. Text-only Search:")
    print("   results = retriever.query(query, search_mode='text')")
    print("   → Finds only textual descriptions")
    
    print("\n4. Document-specific Search:")
    print("   results = retriever.query(query, document_filter='architecture_guide.pdf')")
    print("   → Searches only within a specific document")

def example_response_types():
    """Example of different types of responses."""
    print("\n📝 Response Types Example")
    print("=" * 40)
    
    examples = [
        {
            "query": "How do I reset my password?",
            "response_type": "Step-by-step with screenshots",
            "includes": ["Text instructions", "Login screen screenshot", "Reset form image"]
        },
        {
            "query": "What does error code 404 mean?",
            "response_type": "Error explanation with visual examples", 
            "includes": ["Error description", "Screenshot of error", "Troubleshooting flowchart"]
        },
        {
            "query": "Show me the network topology",
            "response_type": "Visual-heavy response",
            "includes": ["Brief description", "Network diagram", "Connection details"]
        },
        {
            "query": "What are the system requirements?",
            "response_type": "Structured information",
            "includes": ["Requirements table", "Compatibility chart", "Performance graphs"]
        }
    ]
    
    for i, example in enumerate(examples, 1):
        print(f"\n{i}. Query: '{example['query']}'")
        print(f"   Response Type: {example['response_type']}")
        print(f"   Includes: {', '.join(example['includes'])}")

def example_batch_processing():
    """Example of batch processing multiple documents."""
    print("\n📦 Batch Processing Example")
    print("=" * 40)
    
    # Example file list
    documents = [
        "user_manual.pdf",
        "installation_guide.docx", 
        "troubleshooting_guide.pdf",
        "api_documentation.pdf",
        "architecture_overview.docx"
    ]
    
    print("📄 Batch document ingestion:")
    print("documents = [")
    for doc in documents:
        print(f"    '{doc}',")
    print("]")
    
    print("\nretriever = MultimodalRAGRetriever()")
    print("results = retriever.batch_ingest(documents)")
    
    print("\n📊 Expected results:")
    print("✅ user_manual.pdf: 45 text chunks, 12 images")
    print("✅ installation_guide.docx: 23 text chunks, 8 images")
    print("✅ troubleshooting_guide.pdf: 67 text chunks, 15 images")
    print("✅ api_documentation.pdf: 89 text chunks, 3 images")
    print("✅ architecture_overview.docx: 34 text chunks, 7 images")
    
    print("\n🔍 Cross-document queries:")
    cross_doc_queries = [
        "How do I install and then troubleshoot the software?",
        "What's the relationship between the API and system architecture?",
        "Show me all error handling procedures across documents"
    ]
    
    for query in cross_doc_queries:
        print(f"  • {query}")

def example_use_cases():
    """Real-world use case examples."""
    print("\n🌍 Real-World Use Cases")
    print("=" * 40)
    
    use_cases = [
        {
            "title": "Technical Support Bot",
            "description": "Customer support with visual troubleshooting",
            "documents": ["User manual", "FAQ", "Error screenshots"],
            "queries": ["How do I fix this error?", "Show me the settings menu"]
        },
        {
            "title": "Educational Assistant", 
            "description": "Learning with textbooks and diagrams",
            "documents": ["Textbooks", "Lecture slides", "Diagrams"],
            "queries": ["Explain photosynthesis", "Show me the cell structure"]
        },
        {
            "title": "Product Documentation",
            "description": "Feature explanations with UI screenshots", 
            "documents": ["Feature docs", "UI screenshots", "Workflows"],
            "queries": ["How does the dashboard work?", "Show me the reporting features"]
        },
        {
            "title": "Medical Reference",
            "description": "Medical information with anatomical images",
            "documents": ["Medical texts", "Anatomical diagrams", "X-rays"],
            "queries": ["What are the symptoms?", "Show me the affected area"]
        }
    ]
    
    for i, use_case in enumerate(use_cases, 1):
        print(f"\n{i}. {use_case['title']}")
        print(f"   Description: {use_case['description']}")
        print(f"   Documents: {', '.join(use_case['documents'])}")
        print(f"   Example queries:")
        for query in use_case['queries']:
            print(f"     • {query}")

def main():
    """Run all examples."""
    print("📚 Multimodal RAG System - Usage Examples")
    print("=" * 50)
    
    example_basic_usage()
    example_advanced_usage() 
    example_response_types()
    example_batch_processing()
    example_use_cases()
    
    print("\n" + "=" * 50)
    print("✨ To try these examples with real documents:")
    print("1. Run: python main.py web")
    print("2. Upload your documents")
    print("3. Ask questions and see multimodal responses!")
    print("=" * 50)

if __name__ == "__main__":
    main()