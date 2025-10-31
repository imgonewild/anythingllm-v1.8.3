# ⚡ Quick Start: Multimodal RAG Integration

## 🎯 Goal
Replace AnythingLLM's text-only embedding with the RAG system's multimodal (text + image) embedding.

---

## ✅ What's Been Created

### New Files (No Changes Needed)
```
✅ /server/utils/EmbeddingEngines/multimodal/index.js
✅ /server/utils/EmbeddingEngines/multimodal/clip_embedder.js
✅ /server/utils/EmbeddingEngines/multimodal/document_processor.js
✅ /server/utils/EmbeddingEngines/multimodal/vector_store.js
✅ /collector/processSingleFile/convert/asPDF/multimodal.js
✅ /.env.multimodal.example
✅ /install-multimodal.sh
```

### Files to Modify (5 Manual Updates Required)
```
📝 /server/utils/helpers/index.js (add multimodal case)
📝 /collector/utils/constants.js (switch to multimodal.js)
📝 /server/models/documents.js (optional: add metadata)
📝 /server/endpoints/api/workspace/index.js (optional: add images to response)
📝 /frontend/src/components/ChatContainer/ChatHistory/index.jsx (optional: display images)
```

---

## 🚀 Installation (3 Minutes)

### Step 1: Run Installer
```bash
cd /mnt/c/Git-Projects/anything-llm-v1.8.3/anything-llm
chmod +x install-multimodal.sh
./install-multimodal.sh
```

This installs:
- `@xenova/transformers` (CLIP embeddings)
- `chromadb` (dual-collection storage)
- `sharp` (image processing)
- `pdf2pic` (PDF image extraction)
- `tesseract.js` (OCR)
- `canvas` (image manipulation)

### Step 2: Configure Environment
```bash
# Edit .env
nano .env

# Add/Update these lines:
EMBEDDING_ENGINE=multimodal
EMBEDDING_BASE_PATH=http://localhost:11434
EMBEDDING_MODEL_PREF=nomic-embed-text
MULTIMODAL_IMAGE_MODEL=clip-vit-base-patch32
MULTIMODAL_STORAGE_PATH=./storage/multimodal
MULTIMODAL_SEARCH_MODE=enhanced
MULTIMODAL_ENABLE_OCR=true
COLLECTOR_MULTIMODAL_ENABLED=true
COLLECTOR_EXTRACT_IMAGES=true
```

### Step 3: Apply Manual Updates

#### Update 1: Enable Multimodal Engine Selection
**File:** `/server/utils/helpers/index.js`

Find the `getEmbeddingEngineSelection()` function and add:

```javascript
if (engineSelection === "multimodal") {
  const { MultimodalEmbedder } = require("../EmbeddingEngines/multimodal");
  return new MultimodalEmbedder();
}
```

#### Update 2: Switch PDF Processor
**File:** `/collector/utils/constants.js`

Change:
```javascript
const SUPPORTED_FILETYPE_CONVERTERS = {
  ".pdf": "./convert/asPDF/index.js",  // OLD
```

To:
```javascript
const SUPPORTED_FILETYPE_CONVERTERS = {
  ".pdf": process.env.COLLECTOR_MULTIMODAL_ENABLED === "true"
    ? "./convert/asPDF/multimodal.js"   // NEW
    : "./convert/asPDF/index.js",       // FALLBACK
```

### Step 4: Restart Services
```bash
# Stop services
# Restart server and collector
```

---

## ✅ Verification (Test It Works)

### Test 1: Upload PDF with Images
```bash
# Upload any PDF containing images
# Check collector logs:
# ✅ Should see: "-- Extracting images from document.pdf --"
# ✅ Should see: "-- Extracted N images --"
```

### Test 2: Verify Embeddings
```bash
# Check server logs after upload:
# ✅ Should see: "[MultimodalEmbedder] Generated X text embeddings and Y image embeddings"
```

### Test 3: Query with Images
```bash
# In chat, ask about content
# Example: "Show me the installation steps"
# ✅ Response should include relevant text
# ✅ (If frontend updated) Should display inline images
```

---

## 🔧 Troubleshooting

### Problem: "No embedding base path was set"
**Solution:** Add `EMBEDDING_BASE_PATH=http://localhost:11434` to `.env`

### Problem: "Ollama service could not be reached"
**Solution:** Start Ollama: `ollama serve`

### Problem: "Cannot find module @xenova/transformers"
**Solution:** Run `npm install @xenova/transformers` in `/server`

### Problem: Images not extracting
**Solution:** Set `COLLECTOR_MULTIMODAL_ENABLED=true` in `.env`

### Problem: CLIP model download timeout
**Solution:** First run downloads ~500MB. Check internet connection. Wait for download.

---

## 📊 How It Works

### Before (Text-Only)
```
PDF → Extract Text → Text Embedding → Store in Vector DB → Query → Text Results
```

### After (Multimodal)
```
PDF → Extract Text + Images → Text Embedding (Ollama) + Image Embedding (CLIP)
    → Store in Dual ChromaDB Collections
    → Query → Two-Stage Search (Text Context → Contextual Images)
    → Text + Images Results
```

---

## 🎯 Key Features Enabled

✅ **Dual Embedding**: Text (768D) + Images (512D CLIP)
✅ **Image Extraction**: Automatic from PDFs
✅ **OCR**: Searchable text from images
✅ **Smart Search**: Two-stage context-aware retrieval
✅ **Section Matching**: Images from relevant document sections

---

## 📚 More Information

- **Full Guide**: `MULTIMODAL_INTEGRATION_GUIDE.md`
- **Implementation Details**: `IMPLEMENTATION_SUMMARY.md`
- **Configuration Options**: `.env.multimodal.example`

---

## 🎉 You're Done!

Your AnythingLLM now supports multimodal embedding!

**Try it:**
1. Upload a PDF with diagrams or screenshots
2. Ask questions about the visual content
3. Get richer, more informative answers!

**Next:** Consider optional frontend updates to display images inline (see `MULTIMODAL_INTEGRATION_GUIDE.md`)
