"""Ollama client for local LLM integration."""

import requests
import json
from typing import Dict, Any, List, Optional, Generator
import config

class OllamaClient:
    """Client for interacting with Ollama local LLM server."""
    
    def __init__(self, base_url: str = None, model: str = None):
        """
        Initialize Ollama client.
        
        Args:
            base_url: Ollama server URL
            model: Default model to use
        """
        self.base_url = base_url or config.OLLAMA_BASE_URL
        self.model = model or config.OLLAMA_MODEL
        self.session = requests.Session()
        
        # Test connection
        self.is_available = self._test_connection()
        
    def _test_connection(self) -> bool:
        """Test if Ollama server is available."""
        try:
            response = self.session.get(f"{self.base_url}/api/tags", timeout=5)
            return response.status_code == 200
        except Exception as e:
            print(f"Ollama server not available at {self.base_url}: {e}")
            return False
    
    def list_models(self) -> List[Dict[str, Any]]:
        """List available models."""
        if not self.is_available:
            return []
        
        try:
            response = self.session.get(f"{self.base_url}/api/tags")
            response.raise_for_status()
            return response.json().get('models', [])
        except Exception as e:
            print(f"Error listing models: {e}")
            return []
    
    def pull_model(self, model_name: str) -> bool:
        """
        Pull/download a model.
        
        Args:
            model_name: Name of the model to pull
            
        Returns:
            True if successful, False otherwise
        """
        if not self.is_available:
            return False
        
        try:
            data = {"name": model_name}
            response = self.session.post(
                f"{self.base_url}/api/pull",
                json=data,
                timeout=300  # 5 minutes timeout for model download
            )
            return response.status_code == 200
        except Exception as e:
            print(f"Error pulling model {model_name}: {e}")
            return False
    
    def generate(self, prompt: str, model: str = None, **kwargs) -> Optional[str]:
        """
        Generate text using Ollama.
        
        Args:
            prompt: Input prompt
            model: Model to use (defaults to self.model)
            **kwargs: Additional parameters
            
        Returns:
            Generated text or None if failed
        """
        if not self.is_available:
            return None
        
        model = model or self.model
        
        try:
            data = {
                "model": model,
                "prompt": prompt,
                "stream": False,
                **kwargs
            }
            
            response = self.session.post(
                f"{self.base_url}/api/generate",
                json=data,
                timeout=300  # 5 minutes timeout for complex queries
            )
            response.raise_for_status()
            
            result = response.json()
            return result.get('response', '')
            
        except Exception as e:
            print(f"Error generating with Ollama: {e}")
            return None
    
    def chat(self, messages: List[Dict[str, str]], model: str = None, **kwargs) -> Optional[str]:
        """
        Chat completion using Ollama.
        
        Args:
            messages: List of message dictionaries with 'role' and 'content'
            model: Model to use (defaults to self.model)
            **kwargs: Additional parameters
            
        Returns:
            Response text or None if failed
        """
        if not self.is_available:
            return None
        
        model = model or self.model
        
        try:
            data = {
                "model": model,
                "messages": messages,
                "stream": False,
                **kwargs
            }
            
            response = self.session.post(
                f"{self.base_url}/api/chat",
                json=data,
                timeout=120  # 2 minutes timeout
            )
            response.raise_for_status()
            
            result = response.json()
            return result.get('message', {}).get('content', '')
            
        except Exception as e:
            print(f"Error with Ollama chat: {e}")
            return None
    
    def embeddings(self, text: str, model: str = None) -> Optional[List[float]]:
        """
        Generate embeddings using Ollama.
        
        Args:
            text: Input text
            model: Model to use for embeddings
            
        Returns:
            Embedding vector or None if failed
        """
        if not self.is_available:
            return None
        
        # Use embedding model if available, otherwise use main model
        embedding_model = model or "nomic-embed-text" if "nomic-embed-text" in [m.get('name', '') for m in self.list_models()] else self.model
        
        try:
            data = {
                "model": embedding_model,
                "prompt": text
            }
            
            response = self.session.post(
                f"{self.base_url}/api/embeddings",
                json=data,
                timeout=60
            )
            response.raise_for_status()
            
            result = response.json()
            return result.get('embedding', [])
            
        except Exception as e:
            print(f"Error generating embeddings with Ollama: {e}")
            return None
    
    def is_model_available(self, model_name: str) -> bool:
        """Check if a specific model is available."""
        models = self.list_models()
        return any(model.get('name', '') == model_name for model in models)
    
    def get_model_info(self, model_name: str = None) -> Optional[Dict[str, Any]]:
        """Get information about a model."""
        model_name = model_name or self.model
        
        try:
            data = {"name": model_name}
            response = self.session.post(f"{self.base_url}/api/show", json=data)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Error getting model info: {e}")
            return None
    
    def ensure_model_available(self, model_name: str = None) -> bool:
        """Ensure a model is available, download if necessary."""
        model_name = model_name or self.model
        
        if self.is_model_available(model_name):
            return True
        
        print(f"Model {model_name} not found, attempting to pull...")
        return self.pull_model(model_name)
    
    def get_recommended_models(self) -> Dict[str, str]:
        """Get recommended models for different tasks."""
        return {
            "general": "llama2",
            "code": "codellama",
            "chat": "llama2-chat", 
            "small": "tinyllama",
            "embeddings": "nomic-embed-text",
            "large": "llama2:13b",
            "fast": "phi"
        }
    
    def get_status(self) -> Dict[str, Any]:
        """Get Ollama server status and available models."""
        status = {
            "available": self.is_available,
            "base_url": self.base_url,
            "default_model": self.model,
            "models": []
        }
        
        if self.is_available:
            status["models"] = self.list_models()
        
        return status