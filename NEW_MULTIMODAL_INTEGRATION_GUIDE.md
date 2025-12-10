# 🎯 Multimodal RAG Integration Guide

## Overview

This guide documents the integration of the RAG system's multimodal embedding capabilities into AnythingLLM, enabling **text + image** embedding and retrieval.

## 🆕 What's New

### Current AnythingLLM (Text-Only)
- Extracts text from documents
- Generates text embeddings
- Retrieves text-only results

### Enhanced AnythingLLM (Multimodal)
- ✅ Extracts **text AND images** from documents
- ✅ Generates **text embeddings** (Ollama/HuggingFace)
- ✅ Generates **image embeddings** (CLIP ViT-B/32)
- ✅ **Two-stage enhanced retrieval** (text → contextual images)
- ✅ **OCR on images** for searchable text
- ✅ **Inline image display** in chat responses

---

## 📂 Integration Files Created

### Phase 1: Multimodal Embedding Engine
```
/server/utils/EmbeddingEngines/multimodal/
├── index.js              # Main multimodal embedder
├── clip_embedder.js      # CLIP image embedding
├── document_processor.js # Text + image extraction
└── vector_store.js       # ChromaDB dual collections
```

### Phase 2: Enhanced Collector
```
/collector/processSingleFile/convert/asPDF/
└── multimodal.js         # Enhanced PDF processor with image extraction
```

### Configuration
```
/.env.multimodal.example  # Configuration template
```

---

## 🚀 Installation Steps

### Step 1: Install Dependencies

**Server dependencies:**
```bash
cd server
npm install @xenova/transformers chromadb sharp pdf-lib pdf2pic tesseract.js canvas
```

**Collector dependencies:**
```bash
cd collector
npm install pdf2pic tesseract.js sharp canvas
```

### Step 2: Configure Environment

Copy the example configuration:
```bash
cp .env.multimodal.example .env
```

Edit `.env` and configure:
```bash
# Enable multimodal embedding
EMBEDDING_ENGINE=multimodal

# Ollama for text embeddings
EMBEDDING_BASE_PATH=http://localhost:11434
EMBEDDING_MODEL_PREF=nomic-embed-text

# Multimodal settings
MULTIMODAL_IMAGE_MODEL=clip-vit-base-patch32
MULTIMODAL_STORAGE_PATH=./storage/multimodal
MULTIMODAL_ENABLE_OCR=true

# Search settings
MULTIMODAL_SEARCH_MODE=enhanced
MULTIMODAL_TOP_K=5
MULTIMODAL_INCLUDE_IMAGES=true

# Collector settings
COLLECTOR_MULTIMODAL_ENABLED=true
COLLECTOR_EXTRACT_IMAGES=true
```

### Step 3: Integrate with Embedding Engine Selector

**File:** `/server/utils/helpers/index.js`

Add multimodal case to embedding engine selector:

```javascript
function getEmbeddingEngineSelection() {
  const engineSelection = process.env.EMBEDDING_ENGINE;

  // ... existing cases ...

  // NEW: Multimodal embedding engine
  if (engineSelection === "multimodal") {
    const { MultimodalEmbedder } = require("../EmbeddingEngines/multimodal");
    return new MultimodalEmbedder();
  }

  // ... rest of code ...
}
```

### Step 4: Update Collector to Use Multimodal Processor

**File:** `/collector/utils/constants.js`

Update PDF converter:

```javascript
const SUPPORTED_FILETYPE_CONVERTERS = {
  // ... existing converters ...

  // Replace standard PDF converter with multimodal version when enabled
  ".pdf": process.env.COLLECTOR_MULTIMODAL_ENABLED === "true"
    ? "./convert/asPDF/multimodal.js"
    : "./convert/asPDF/index.js",

  // ... rest of converters ...
};
```

### Step 5: Update Document Model for Multimodal Data

**File:** `/server/models/documents.js`

Enhance `addDocuments` function to handle multimodal data:

```javascript
async addDocuments(workspace, additions = [], userId = null) {
  // ... existing code ...

  for (const path of additions) {
    const data = await fileData(path);
    if (!data) continue;

    // NEW: Check if document has multimodal data
    const isMultimodal = data.isMultimodal && data.images;

    // Store document with multimodal flag
    const newDoc = {
      docId,
      filename: path.split("/")[1],
      docpath: path,
      workspaceId: workspace.id,
      metadata: JSON.stringify({
        ...metadata,
        isMultimodal,              // NEW
        imageCount: data.images?.length || 0  // NEW
      }),
    };

    // ... rest of code ...
  }
}
```

### Step 6: Update Chat Response to Display Images

**File:** `/server/endpoints/api/workspace/index.js`

Enhance chat endpoint to include images in responses:

```javascript
app.post("/workspace/:slug/chat", async (request, response) => {
  // ... existing chat logic ...

  // NEW: If using multimodal, include images in response
  if (process.env.EMBEDDING_ENGINE === "multimodal") {
    const embedder = getEmbeddingEngineSelection();

    // Query with image retrieval
    const queryResults = await embedder.query(message, {
      topK: 5,
      includeImages: true,
      searchMode: process.env.MULTIMODAL_SEARCH_MODE || "enhanced"
    });

    // Format response with inline images
    const responseWithImages = formatResponseWithImages(
      textResponse,
      queryResults.imageResults
    );

    return response.status(200).json({
      ...existingResponse,
      images: queryResults.imageResults,  // NEW
      hasImages: true                      // NEW
    });
  }

  // ... existing response ...
});
```

---

## 🎨 Frontend Integration

### Step 1: Update Chat Component

**File:** `/frontend/src/components/ChatContainer/ChatHistory/index.jsx`

Add image rendering support:

```jsx
function ChatMessage({ message }) {
  const { textContent, images } = message;

  return (
    <div className="chat-message">
      {/* Render text with inline image placeholders */}
      <div dangerouslySetInnerHTML={{ __html: processInlineImages(textContent, images) }} />

      {/* Render images */}
      {images && images.length > 0 && (
        <div className="message-images">
          {images.map((img, idx) => (
            <img
              key={idx}
              src={`data:image/png;base64,${img.imageData}`}
              alt={img.caption || `Image ${idx + 1}`}
              className="inline-image"
            />
          ))}
        </div>
      )}
    </div>
  );
}

function processInlineImages(text, images) {
  // Replace [IMAGE_X_PLACEHOLDER] with actual images
  let processed = text;
  images.forEach((img, idx) => {
    const placeholder = `[IMAGE_${idx + 1}_PLACEHOLDER]`;
    const imgTag = `<img src="data:image/png;base64,${img.imageData}" alt="${img.caption}" class="inline-image" />`;
    processed = processed.replace(placeholder, imgTag);
  });
  return processed;
}
```

### Step 2: Add Settings UI for Multimodal

**File:** `/frontend/src/pages/WorkspaceSettings/EmbeddingConfig/index.jsx`

Add multimodal embedding option:

```jsx
function EmbeddingConfig() {
  return (
    <div>
      {/* ... existing embedding options ... */}

      <div className="embedding-option">
        <input
          type="radio"
          name="embedding-engine"
          value="multimodal"
          checked={embeddingEngine === "multimodal"}
          onChange={handleEmbeddingChange}
        />
        <label>
          <strong>Multimodal RAG</strong> (Text + Images)
          <p>Extract and embed both text and images from documents for visual search</p>
        </label>
      </div>

      {embeddingEngine === "multimodal" && (
        <div className="multimodal-settings">
          <h4>Multimodal Settings</h4>

          <label>
            Search Mode:
            <select name="searchMode" value={searchMode} onChange={handleSearchModeChange}>
              <option value="text">Text Only</option>
              <option value="image">Image Only</option>
              <option value="hybrid">Hybrid</option>
              <option value="enhanced">Enhanced (2-Stage)</option>
            </select>
          </label>

          <label>
            <input
              type="checkbox"
              checked={includeImages}
              onChange={handleIncludeImagesChange}
            />
            Include images in responses
          </label>

          <label>
            <input
              type="checkbox"
              checked={enableOCR}
              onChange={handleEnableOCRChange}
            />
            Enable OCR on images
          </label>
        </div>
      )}
    </div>
  );
}
```

---

## 🔍 How It Works

### Document Upload Flow (Multimodal)

```
┌─────────────────────────────────────────────────────┐
│  1. User uploads PDF document                       │
└──────────────────┬──────────────────────────────────┘
                   ↓
┌─────────────────────────────────────────────────────┐
│  2. Collector Service (Enhanced)                    │
│     • Extracts text chunks                          │
│     • Extracts images from each page                │
│     • Performs OCR on images                        │
│     • Extracts context around images                │
│     • Saves JSON with text + images                 │
└──────────────────┬──────────────────────────────────┘
                   ↓
┌─────────────────────────────────────────────────────┐
│  3. Server - Multimodal Embedder                    │
│     • Reads JSON from collector                     │
│     • Generates text embeddings (Ollama 768D)       │
│     • Generates image embeddings (CLIP 512D)        │
│     • Stores in dual ChromaDB collections           │
└──────────────────┬──────────────────────────────────┘
                   ↓
┌─────────────────────────────────────────────────────┐
│  4. Vector Storage                                  │
│     • text_chunks collection (768D vectors)         │
│     • image_chunks collection (512D vectors)        │
│     • image_metadata.json (extended metadata)       │
│     • image_objects.json (base64 images)            │
└─────────────────────────────────────────────────────┘
```

### Query Flow (Enhanced Two-Stage)

```
┌─────────────────────────────────────────────────────┐
│  1. User asks: "How do I install the software?"    │
└──────────────────┬──────────────────────────────────┘
                   ↓
┌─────────────────────────────────────────────────────┐
│  2. Stage 1: Text Retrieval                         │
│     • Generate text embedding from query            │
│     • Search text_chunks collection                 │
│     • Find top 10 relevant text chunks              │
│     • Extract context: pages, sections, keywords    │
└──────────────────┬──────────────────────────────────┘
                   ↓
┌─────────────────────────────────────────────────────┐
│  3. Stage 2: Context-Aware Image Search             │
│     • Use CLIP to embed query as text               │
│     • Search images from SAME PAGES as text results │
│     • Priority: same section > same page > global   │
│     • Boost scores for contextually relevant images │
└──────────────────┬──────────────────────────────────┘
                   ↓
┌─────────────────────────────────────────────────────┐
│  4. Response Generation                             │
│     • LLM generates text response from text context │
│     • Embeds images inline with [IMAGE_X] markers   │
│     • Returns: text + images + metadata             │
└──────────────────┬──────────────────────────────────┘
                   ↓
┌─────────────────────────────────────────────────────┐
│  5. Frontend Display                                │
│     • Renders text with markdown                    │
│     • Displays images inline at markers             │
│     • Shows image captions and sources              │
└─────────────────────────────────────────────────────┘
```

---

## 📊 Benefits

### For Users
✅ **Visual Understanding**: Images embedded alongside text for better comprehension
✅ **Richer Answers**: Chat responses include relevant diagrams, screenshots, charts
✅ **Better Accuracy**: OCR makes image text searchable
✅ **Context-Aware**: Images from relevant sections, not random matches

### For Developers
✅ **Modular Design**: Works alongside existing text-only mode
✅ **Backward Compatible**: Doesn't break existing functionality
✅ **Configurable**: Easy to enable/disable via environment variables
✅ **Extensible**: Easy to add support for more image types (charts, tables, etc.)

---

## 🧪 Testing

### Test Multimodal Upload

1. Upload a PDF with images
2. Check collector logs for image extraction:
   ```
   -- Extracting images from document.pdf --
   -- Extracted 5 images --
   ```

3. Check server logs for embeddings:
   ```
   [MultimodalEmbedder] Generated 20 text embeddings and 5 image embeddings
   ```

### Test Multimodal Query

1. Ask a question about content near an image
2. Check response includes relevant images
3. Verify images display inline in chat

### Test Search Modes

```bash
# Text only
MULTIMODAL_SEARCH_MODE=text

# Image only
MULTIMODAL_SEARCH_MODE=image

# Hybrid (text + images)
MULTIMODAL_SEARCH_MODE=hybrid

# Enhanced (two-stage contextual)
MULTIMODAL_SEARCH_MODE=enhanced
```

---

## 🔧 Troubleshooting

### Images Not Extracting
- Check `COLLECTOR_MULTIMODAL_ENABLED=true` in `.env`
- Verify pdf2pic is installed: `npm list pdf2pic`
- Check collector logs for errors

### CLIP Model Loading Errors
- Ensure `@xenova/transformers` is installed
- First run downloads model (~500MB), may take time
- Check internet connection for model download

### Images Not Displaying in Chat
- Verify `MULTIMODAL_INCLUDE_IMAGES=true`
- Check frontend image rendering component
- Verify base64 image data in response

### OCR Not Working
- Ensure `tesseract.js` is installed
- Check `MULTIMODAL_ENABLE_OCR=true`
- Verify OCR language installed (`eng` by default)

---

## 📚 Next Steps

### Enhancements to Add

1. **Video Support**: Extract keyframes from videos
2. **Table Extraction**: Specialized table understanding
3. **Chart Recognition**: Understand charts and graphs
4. **Multi-language OCR**: Support more languages
5. **Image Captioning**: Auto-generate better captions
6. **Semantic Image Search**: Find similar images by content

### Performance Optimizations

1. **Caching**: Cache CLIP model in memory
2. **Batch Processing**: Process multiple images at once
3. **Async Processing**: Background image embedding
4. **CDN Storage**: Store images in CDN for faster loading

---

## 🎉 Congratulations!

You've successfully integrated multimodal RAG capabilities into AnythingLLM! Your users can now:
- Upload documents with images
- Search across both text and visual content
- Receive richer, more informative responses
- Understand complex topics through visual aids

Happy building! 🚀
