"""Configuration settings for the multimodal RAG system."""

import os
from dotenv import load_dotenv

load_dotenv()

# API Keys
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
HUGGINGFACE_API_KEY = os.getenv("HUGGINGFACE_API_KEY")

# LLM Provider Configuration
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "ollama")  # "openai", "ollama", or "auto"
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://wpjk.inteplast.com:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.1:latest")  # Default Ollama model

# Model configurations
# Options: "sentence-transformers/all-MiniLM-L6-v2", "nomic-embed-text", "mxbai-embed-large", "all-minilm"
TEXT_EMBEDDING_MODEL = os.getenv("TEXT_EMBEDDING_MODEL", "nomic-embed-text")
EMBEDDING_PROVIDER = os.getenv("EMBEDDING_PROVIDER", "ollama")  # "huggingface" or "ollama"
MULTIMODAL_MODEL = "openai/clip-vit-base-patch32"

# LLM Model selection based on provider
if LLM_PROVIDER == "openai":
    LLM_MODEL = "gpt-3.5-turbo"
elif LLM_PROVIDER == "ollama":
    LLM_MODEL = OLLAMA_MODEL
else:  # auto mode
    # Use Ollama if available, fallback to OpenAI
    LLM_MODEL = OLLAMA_MODEL if os.getenv("OLLAMA_MODEL") else "gpt-3.5-turbo"

# Vector database settings
VECTOR_DB_PATH = "./vector_db"
COLLECTION_NAME = "multimodal_rag"

# Document processing settings
SUPPORTED_FORMATS = [".pdf", ".docx", ".doc", ".txt"]
IMAGE_FORMATS = [".png", ".jpg", ".jpeg", ".gif", ".bmp"]
MAX_IMAGE_SIZE = (800, 800)  # Resize images to this max size
OCR_ENABLED = True

# Retrieval settings
TOP_K_RESULTS = 5
SIMILARITY_THRESHOLD = -0.6  # Extremely permissive to include all content
INCLUDE_IMAGES_IN_RESPONSE = True

# UI settings
STREAMLIT_PORT = 8501
UPLOAD_DIR = "./uploads"
PROCESSED_DIR = "./processed"