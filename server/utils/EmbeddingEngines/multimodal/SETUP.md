# Multimodal RAG Setup Guide

## Quick Start

Run the installation script to set up PyMuPDF for image extraction:

```bash
cd /mnt/c/Git-Projects/anything-llm-v1.8.3/anything-llm/server/utils/EmbeddingEngines/multimodal
./install-pymupdf.sh
```

## Manual Installation

If the script doesn't work, follow these steps:

### 1. Install System Dependencies
```bash
sudo apt-get update
sudo apt-get install python3.12-venv python3-pip
```

### 2. Create Virtual Environment
```bash
cd /mnt/c/Git-Projects/anything-llm-v1.8.3/anything-llm/server/utils/EmbeddingEngines/multimodal
python3 -m venv venv
```

### 3. Install Python Packages
```bash
source venv/bin/activate
pip install PyMuPDF==1.23.14 Pillow==10.1.0
```

### 4. Verify Installation
```bash
python3 -c "import fitz; print('PyMuPDF version:', fitz.version)"
python3 -c "import PIL; print('Pillow version:', PIL.__version__)"
```

## How It Works

### Image Extraction Process

1. **PDF Upload**: User uploads a PDF document
2. **Text Extraction**: Text is extracted and chunked (pdf-parse)
3. **Image Extraction**: Images are extracted using PyMuPDF
   - Embedded images are extracted directly from PDF
   - Each image gets OCR text extraction
   - Surrounding text context is captured
4. **Embedding**:
   - Text chunks → Ollama `nomic-embed-text`
   - Images → CLIP `clip-vit-base-patch32`
5. **Storage**: Both stored in ChromaDB
   - Text collection: `multimodal_text_chunks`
   - Image collection: `multimodal_image_chunks`

### Query Process

1. **User Query**: "Show me the network diagram"
2. **Embedding**: Query embedded with `nomic-embed-text`
3. **Search**:
   - Text chunks searched
   - Image chunks searched (same vector space)
4. **Context Building**:
   ```
   [Image 1] From document.pdf, Page 2 (Relevance: 0.85)
   Caption: Network topology diagram
   Text in image: XF Network Layout
   Image Context: This section describes the network architecture...
   ```
5. **LLM Response**:
   ```
   "The network diagram [Image 1] shows the XF network structure
   with multiple servers connected..."
   ```

### Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    Document Upload                      │
└────────────────────┬────────────────────────────────────┘
                     │
         ┌───────────┴───────────┐
         │                       │
    ┌────▼────┐           ┌─────▼─────┐
    │  Text   │           │  Images   │
    │ Chunks  │           │(PyMuPDF)  │
    └────┬────┘           └─────┬─────┘
         │                      │
    ┌────▼────┐           ┌─────▼─────┐
    │ nomic-  │           │   CLIP    │
    │ embed   │           │   ViT     │
    └────┬────┘           └─────┬─────┘
         │                      │
         └──────────┬───────────┘
                    │
            ┌───────▼────────┐
            │   ChromaDB     │
            │  Collections   │
            └───────┬────────┘
                    │
         ┌──────────┴───────────┐
         │                      │
    ┌────▼────┐           ┌─────▼─────┐
    │  Text   │           │  Image    │
    │Collection│          │Collection │
    └─────────┘           └───────────┘
```

## Configuration

Ensure these settings in `/mnt/c/Git-Projects/anything-llm-v1.8.3/anything-llm/server/.env`:

```env
# Embedding Engine
EMBEDDING_ENGINE=multimodal
EMBEDDING_BASE_PATH=http://wpjk.inteplast.com:11434
EMBEDDING_MODEL_PREF=nomic-embed-text

# Vector Database
VECTOR_DB=chroma
CHROMA_ENDPOINT=http://localhost:8000

# LLM Provider
LLM_PROVIDER=ollama
```

## Troubleshooting

### PyMuPDF Not Found
```bash
# Check if installed
./venv/bin/python3 -c "import fitz; print('OK')"

# If not, reinstall
./venv/bin/pip install --force-reinstall PyMuPDF
```

### ChromaDB Connection Error
```bash
# Check if ChromaDB is running
curl http://localhost:8000/api/v1/heartbeat

# If not, start it
chroma run --path ./server/storage/chroma --port 8000
```

### No Images Extracted
```bash
# Check logs for errors
tail -f server-logs.txt | grep -i "multimodal\|image"

# Verify Python script works
./venv/bin/python3 ./extract_images.py /path/to/your.pdf
```

## Testing

After installation, test the system:

1. **Upload a PDF with images**
2. **Check logs for**:
   ```
   [DocumentProcessor] Extracting images from PDF using PyMuPDF...
   [DocumentProcessor] Successfully extracted N images from PDF
   [MultimodalEmbedder] Embedding N images with CLIP
   ```
3. **Query for visual content**:
   - "Show me the diagrams"
   - "What images are in the document?"
   - "Describe the network layout"

## Files

- `extract_images.py` - Python script for image extraction
- `document_processor.js` - Node.js document processor
- `clip_embedder.js` - CLIP model for image embeddings
- `vector_store.js` - ChromaDB interface
- `index.js` - Main multimodal embedder

## Performance Notes

- **Image Extraction**: ~1-2 seconds per page
- **Image Embedding**: ~0.5 seconds per image
- **Storage**: ~50KB per embedded image
- **Max Pages**: Limited to 50 pages per PDF (configurable)
