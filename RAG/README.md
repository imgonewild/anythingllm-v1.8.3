# 📚 Multimodal RAG System

A comprehensive Retrieval-Augmented Generation (RAG) system that can process documents containing both text and images, and respond to queries with relevant text information and visual context.

## 🌟 Features

- **Multimodal Document Processing**: Extract text and images from PDFs, DOCX, and TXT files
- **Advanced Embeddings**: Uses CLIP for multimodal embeddings and sentence transformers for text
- **Image-Aware Responses**: Includes relevant images in responses with captions and OCR text
- **Web Interface**: Beautiful Streamlit-based UI for document upload and querying
- **CLI Support**: Command-line interface for batch processing and automation
- **Flexible Search**: Text-only, image-only, or hybrid search modes
- **Source Attribution**: Tracks and cites sources with confidence scores

## 🏗️ Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Documents     │───▶│  Document        │───▶│   Embeddings    │
│ (PDF/DOCX/TXT)  │    │  Processor       │    │   (CLIP +       │
└─────────────────┘    └──────────────────┘    │ SentenceTransf) │
                                                └─────────────────┘
                                                         │
┌─────────────────┐    ┌──────────────────┐             ▼
│   User Query    │───▶│   Retrieval      │    ┌─────────────────┐
└─────────────────┘    │   Engine         │◀───│  Vector Store   │
                       └──────────────────┘    │   (ChromaDB)    │
                                │              └─────────────────┘
                                ▼
                       ┌──────────────────┐
                       │   Response       │
                       │   Generator      │
                       │   (GPT + Images) │
                       └──────────────────┘
```

## 🚀 Quick Start

### 1. Installation

```bash
# Clone the repository
git clone <repository-url>
cd rag_image

# Install dependencies
pip install -r requirements.txt

# Run setup script (recommended)
python setup.py
```

### 2. Choose Your LLM Provider

#### Option A: Ollama (Local, Free, Private) 🦙
```bash
# Install Ollama
curl -fsSL https://ollama.ai/install.sh | sh

# Start Ollama server
ollama serve

# Pull a model
ollama pull llama2

# Configure for Ollama
echo "LLM_PROVIDER=ollama" >> .env
echo "OLLAMA_MODEL=llama2" >> .env
```

#### Option B: OpenAI (Cloud-based) 🤖
```bash
# Add your API key to .env
echo "LLM_PROVIDER=openai" >> .env
echo "OPENAI_API_KEY=your_api_key_here" >> .env
```

#### Option C: Auto Mode (Best of Both) ⚡
```bash
# Try Ollama first, fallback to OpenAI
echo "LLM_PROVIDER=auto" >> .env
echo "OLLAMA_MODEL=llama2" >> .env
echo "OPENAI_API_KEY=your_api_key_here" >> .env
```

### 3. Run the Web Interface

```bash
python main.py web
```

Open your browser and go to `http://localhost:8501`

### 4. Upload Documents and Ask Questions

1. **Upload Documents**: Use the sidebar to upload PDF, DOCX, or TXT files
2. **Ask Questions**: Type your questions in the main interface
3. **Get Multimodal Answers**: Receive responses with both text and relevant images

## 💻 Usage Examples

### Web Interface
```bash
# Start the web application
python main.py web
```

### Command Line Interface
```bash
# Interactive CLI mode
python main.py cli
```

### Batch Document Ingestion
```bash
# Ingest documents from command line
python main.py ingest document1.pdf document2.docx

# Clear existing data and ingest new documents
python main.py ingest --clear manual.pdf guide.docx
```

## 📖 Example Use Cases

### User Manual RAG
Perfect for technical documentation where images provide crucial context:

**Query**: "How do I install the software?"
**Response**: 
- Text explanation of installation steps
- Screenshots showing the installation interface
- Diagrams illustrating the process

**Query**: "What does the error message mean?"
**Response**:
- Error description and solutions
- Screenshots of the actual error
- Troubleshooting flowcharts

### Educational Content
Great for textbooks and learning materials:

**Query**: "Explain the water cycle"
**Response**:
- Textual explanation of the process
- Diagrams showing evaporation, condensation, precipitation
- Charts with relevant data

## 🔧 Configuration

### LLM Provider Options

| Provider | Pros | Cons | Setup |
|----------|------|------|-------|
| **Ollama** 🦙 | Free, Private, Offline | Requires local resources | [Ollama Setup Guide](ollama_setup.md) |
| **OpenAI** 🤖 | High quality, Fast | Costs money, Requires internet | Add API key to `.env` |
| **Auto** ⚡ | Best of both worlds | More complex setup | Configure both providers |

### Environment Variables (`.env` file)

```bash
# LLM Provider (choose one)
LLM_PROVIDER=ollama          # Use Ollama (recommended)
LLM_PROVIDER=openai          # Use OpenAI
LLM_PROVIDER=auto            # Try Ollama first, fallback to OpenAI

# Ollama settings (if using Ollama)
OLLAMA_MODEL=llama2          # Model name
OLLAMA_BASE_URL=http://localhost:11434

# OpenAI settings (if using OpenAI)
OPENAI_API_KEY=your_api_key_here

# Optional
HUGGINGFACE_API_KEY=your_hf_key_here
```

### Advanced Configuration (`config.py`)

```python
# Embedding models
TEXT_EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
MULTIMODAL_MODEL = "openai/clip-vit-base-patch32"

# Retrieval settings
TOP_K_RESULTS = 5
SIMILARITY_THRESHOLD = 0.7
```

## 📁 Project Structure

```
rag_image/
├── app.py                 # Streamlit web interface
├── main.py               # Main CLI application
├── config.py             # Configuration settings
├── requirements.txt      # Python dependencies
├── document_processor.py # Document processing logic
├── embedding_system.py   # Embedding generation
├── vector_store.py       # Vector database operations
├── retrieval_engine.py   # Main retrieval logic
├── response_generator.py # Response generation
└── README.md            # This file
```

## 🛠️ Technical Details

### Document Processing
- **PDF**: Extracts text and images using PyMuPDF
- **DOCX**: Processes text and embedded images
- **OCR**: Extracts text from images using Tesseract
- **Image Preprocessing**: Resizes and optimizes images

### Embeddings
- **Text Embeddings**: Sentence Transformers for semantic similarity
- **Image Embeddings**: CLIP for multimodal understanding
- **Cross-Modal Search**: Query text can find relevant images

### Vector Storage
- **Database**: ChromaDB for efficient similarity search
- **Metadata**: Stores document names, page numbers, captions
- **Persistence**: Data persists between sessions

### Response Generation
- **LLM Integration**: Uses OpenAI GPT for natural responses
- **Context Combination**: Merges text and image information
- **Source Attribution**: Provides citations and confidence scores

## 🔍 Search Modes

1. **Hybrid Mode** (Default): Searches both text and images
2. **Text Mode**: Only searches text content
3. **Image Mode**: Only searches images and their metadata

## 📊 Performance Considerations

- **Batch Processing**: Process multiple documents efficiently
- **Embedding Caching**: Reuses embeddings for faster queries
- **Image Optimization**: Resizes images to reduce memory usage
- **Similarity Thresholds**: Filters low-relevance results

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Troubleshooting

### Common Issues

1. **Missing API Key**: Set `OPENAI_API_KEY` in your `.env` file
2. **Memory Issues**: Reduce `MAX_IMAGE_SIZE` in config.py
3. **OCR Not Working**: Install Tesseract OCR system dependency
4. **CLIP Model Loading**: Ensure you have sufficient GPU/CPU memory

### System Requirements

- Python 3.8+
- 4GB+ RAM (8GB+ recommended)
- 2GB+ disk space for models
- Optional: CUDA GPU for faster processing

## 🙏 Acknowledgments

- OpenAI for GPT and CLIP models
- Hugging Face for Sentence Transformers
- ChromaDB for vector database
- Streamlit for the web interface

---

**Happy RAG-ing! 🚀**