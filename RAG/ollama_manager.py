"""Ollama model management utility."""

import argparse
import sys
from ollama_client import OllamaClient

def list_models():
    """List available Ollama models."""
    client = OllamaClient()
    
    if not client.is_available:
        print("❌ Ollama server not available. Make sure it's running: ollama serve")
        return False
    
    models = client.list_models()
    
    if not models:
        print("📭 No models installed")
        print("\n💡 Install a model with: python ollama_manager.py pull llama2")
        return True
    
    print("📋 Installed Models:")
    print("-" * 50)
    
    for model in models:
        name = model.get('name', 'Unknown')
        size = model.get('size', 0)
        modified = model.get('modified_at', 'Unknown')
        
        # Convert size to human readable
        size_gb = size / (1024**3) if size else 0
        
        print(f"🦙 {name}")
        print(f"   Size: {size_gb:.1f} GB")
        print(f"   Modified: {modified}")
        print()
    
    return True

def pull_model(model_name: str):
    """Pull/download a model."""
    client = OllamaClient()
    
    if not client.is_available:
        print("❌ Ollama server not available. Make sure it's running: ollama serve")
        return False
    
    print(f"📥 Pulling model: {model_name}")
    print("⏳ This may take a few minutes...")
    
    success = client.pull_model(model_name)
    
    if success:
        print(f"✅ Successfully pulled {model_name}")
        return True
    else:
        print(f"❌ Failed to pull {model_name}")
        return False

def test_model(model_name: str = None):
    """Test a model with a simple query."""
    client = OllamaClient()
    
    if not client.is_available:
        print("❌ Ollama server not available. Make sure it's running: ollama serve")
        return False
    
    model_name = model_name or client.model
    
    if not client.is_model_available(model_name):
        print(f"❌ Model {model_name} not available")
        print("📋 Available models:")
        list_models()
        return False
    
    print(f"🧪 Testing model: {model_name}")
    
    test_prompt = "Hello! Please introduce yourself in one sentence."
    print(f"📝 Prompt: {test_prompt}")
    print("⏳ Generating response...")
    
    response = client.generate(test_prompt, model=model_name)
    
    if response:
        print(f"🤖 Response: {response}")
        return True
    else:
        print("❌ Failed to generate response")
        return False

def show_status():
    """Show Ollama server status."""
    client = OllamaClient()
    status = client.get_status()
    
    print("🦙 Ollama Status")
    print("=" * 30)
    
    if status['available']:
        print("✅ Server: Connected")
        print(f"🌐 URL: {status['base_url']}")
        print(f"🎯 Default model: {status['default_model']}")
        
        models = status['models']
        print(f"📦 Installed models: {len(models)}")
        
        if models:
            print("\n📋 Models:")
            for model in models[:5]:  # Show first 5
                name = model.get('name', 'Unknown')
                print(f"  • {name}")
            
            if len(models) > 5:
                print(f"  ... and {len(models) - 5} more")
    else:
        print("❌ Server: Not connected")
        print(f"🌐 Trying: {status['base_url']}")
        print("\n💡 To start Ollama server: ollama serve")

def recommend_models():
    """Show recommended models for different use cases."""
    recommendations = {
        "🚀 Getting Started": [
            ("llama2", "3.8GB", "General purpose, good balance of quality and speed"),
            ("phi", "1.1GB", "Fast and lightweight, good for testing")
        ],
        "📚 Document Q&A": [
            ("llama2", "3.8GB", "Excellent for understanding and explaining content"),
            ("llama2:13b", "7.3GB", "Higher quality responses (needs 16GB+ RAM)")
        ],
        "💻 Code & Technical": [
            ("codellama", "3.8GB", "Specialized for code understanding"),
            ("codellama:13b", "7.3GB", "Better code generation and explanation")
        ],
        "⚡ Speed Optimized": [
            ("tinyllama", "637MB", "Very fast, basic tasks only"),
            ("phi", "1.1GB", "Good balance of speed and capability")
        ]
    }
    
    print("💡 Recommended Models")
    print("=" * 40)
    
    for category, models in recommendations.items():
        print(f"\n{category}:")
        for name, size, description in models:
            print(f"  🦙 {name} ({size})")
            print(f"     {description}")
            print(f"     Install: ollama pull {name}")

def main():
    """Main CLI function."""
    parser = argparse.ArgumentParser(description="Ollama Model Manager")
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # List command
    subparsers.add_parser('list', help='List installed models')
    
    # Pull command
    pull_parser = subparsers.add_parser('pull', help='Pull/download a model')
    pull_parser.add_argument('model', help='Model name to pull (e.g., llama2)')
    
    # Test command
    test_parser = subparsers.add_parser('test', help='Test a model')
    test_parser.add_argument('model', nargs='?', help='Model name to test (optional)')
    
    # Status command
    subparsers.add_parser('status', help='Show Ollama server status')
    
    # Recommend command
    subparsers.add_parser('recommend', help='Show recommended models')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    success = True
    
    if args.command == 'list':
        success = list_models()
    elif args.command == 'pull':
        success = pull_model(args.model)
    elif args.command == 'test':
        success = test_model(args.model)
    elif args.command == 'status':
        show_status()
    elif args.command == 'recommend':
        recommend_models()
    
    if not success:
        sys.exit(1)

if __name__ == "__main__":
    main()