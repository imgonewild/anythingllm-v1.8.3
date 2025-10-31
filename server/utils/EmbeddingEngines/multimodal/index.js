const { maximumChunkLength } = require("../../helpers");
const { ClipEmbedder } = require("./clip_embedder");
const { MultimodalVectorStore } = require("./vector_store");
const { DocumentProcessor } = require("./document_processor");
const path = require("path");

/**
 * Multimodal Embedding Engine for AnythingLLM
 *
 * Integrates the RAG system's multimodal capabilities:
 * - Text embeddings (Ollama/HuggingFace)
 * - Image embeddings (CLIP ViT-B/32)
 * - Dual-collection ChromaDB storage
 * - Two-stage enhanced retrieval
 *
 * Based on the RAG system from /RAG folder
 */
class MultimodalEmbedder {
  constructor() {
    if (!process.env.EMBEDDING_BASE_PATH)
      throw new Error("No embedding base path was set.");
    if (!process.env.EMBEDDING_MODEL_PREF)
      throw new Error("No embedding model was set.");

    this.basePath = process.env.EMBEDDING_BASE_PATH;
    this.textModel = process.env.EMBEDDING_MODEL_PREF;
    this.imageModel = process.env.MULTIMODAL_IMAGE_MODEL || "clip-vit-base-patch32";

    // Storage paths
    this.storagePath = process.env.MULTIMODAL_STORAGE_PATH ||
                      path.join(process.env.STORAGE_DIR || "./storage", "multimodal");

    // Initialize components
    this.maxConcurrentChunks = 1;
    this.embeddingMaxChunkLength = maximumChunkLength();

    // Initialize CLIP for image embeddings
    this.clipEmbedder = new ClipEmbedder(this.imageModel);

    // Initialize document processor
    this.documentProcessor = new DocumentProcessor();

    // Initialize vector store (dual collections)
    this.vectorStore = new MultimodalVectorStore(this.storagePath);

    this.log(
      `Initialized MultimodalEmbedder with text model: ${this.textModel}, image model: ${this.imageModel}`
    );
  }

  log(text, ...args) {
    console.log(`\x1b[36m[${this.constructor.name}]\x1b[0m ${text}`, ...args);
  }

  /**
   * Check if service is alive
   */
  async #isAlive() {
    try {
      const response = await fetch(this.basePath);
      return response.ok;
    } catch (e) {
      this.log(`Connection check failed: ${e.message}`);
      return false;
    }
  }

  /**
   * Embed a single text input
   * @param {string|string[]} textInput - Text or array of texts to embed
   * @returns {Promise<number[]>} - Embedding vector
   */
  async embedTextInput(textInput) {
    const result = await this.embedChunks(
      Array.isArray(textInput) ? textInput : [textInput]
    );
    return result?.[0] || [];
  }

  /**
   * Embed multiple text chunks using Ollama
   * @param {string[]} textChunks - Array of text chunks
   * @returns {Promise<Array<number[]>>} - Array of embedding vectors
   */
  async embedChunks(textChunks = []) {
    if (!(await this.#isAlive())) {
      throw new Error(`Ollama service could not be reached. Is Ollama running?`);
    }

    this.log(`Embedding ${textChunks.length} text chunks with ${this.textModel}`);

    const data = [];
    let error = null;

    for (const chunk of textChunks) {
      try {
        const response = await fetch(`${this.basePath}/api/embeddings`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            model: this.textModel,
            prompt: chunk,
            options: {
              num_ctx: this.embeddingMaxChunkLength,
            },
          }),
        });

        const result = await response.json();
        const { embedding } = result;

        if (!Array.isArray(embedding) || embedding.length === 0) {
          throw new Error("Ollama returned an empty embedding!");
        }

        // Normalize embedding
        const norm = Math.sqrt(embedding.reduce((sum, val) => sum + val * val, 0));
        const normalizedEmbedding = embedding.map(val => val / norm);

        data.push(normalizedEmbedding);
      } catch (err) {
        this.log(`Error embedding chunk: ${err.message}`);
        error = err.message;
        break;
      }
    }

    if (error) throw new Error(`Failed to embed: ${error}`);
    return data.length > 0 ? data : null;
  }

  /**
   * Process and embed a document with images
   * @param {string} filePath - Path to document
   * @param {Object} options - Processing options
   * @returns {Promise<Object>} - Processing results
   */
  async processDocument(filePath, options = {}) {
    this.log(`Processing multimodal document: ${filePath}`);

    try {
      // Extract text chunks and images
      const { textChunks, images } = await this.documentProcessor.processDocument(
        filePath,
        options
      );

      this.log(`Extracted ${textChunks.length} text chunks and ${images.length} images`);

      // Embed text chunks
      const textEmbeddings = [];
      if (textChunks.length > 0) {
        const texts = textChunks.map(chunk => chunk.text);
        textEmbeddings.push(...await this.embedChunks(texts));
      }

      // Embed images with CLIP
      const imageEmbeddings = [];
      if (images.length > 0) {
        for (const imageData of images) {
          const embedding = await this.clipEmbedder.embedImage(imageData.image);
          imageEmbeddings.push(embedding);
        }
      }

      this.log(`Generated ${textEmbeddings.length} text embeddings and ${imageEmbeddings.length} image embeddings`);

      // Store in dual collections
      const documentName = path.basename(filePath);
      await this.vectorStore.addTextChunks(textChunks, textEmbeddings, documentName);
      await this.vectorStore.addImageChunks(images, imageEmbeddings, documentName);

      return {
        success: true,
        textChunks: textChunks.length,
        images: images.length,
        documentName,
      };
    } catch (error) {
      this.log(`Error processing document: ${error.message}`);
      throw error;
    }
  }

  /**
   * Query the multimodal system (two-stage retrieval)
   * @param {string} queryText - User query
   * @param {Object} options - Query options
   * @returns {Promise<Object>} - Query results with text and images
   */
  async query(queryText, options = {}) {
    const {
      topK = 5,
      includeImages = true,
      searchMode = "enhanced", // "text", "image", "hybrid", "enhanced"
    } = options;

    this.log(`Querying: "${queryText}" (mode: ${searchMode})`);

    try {
      // Generate query embeddings
      const textEmbedding = await this.embedTextInput(queryText);

      if (searchMode === "enhanced" && includeImages) {
        // Two-stage enhanced retrieval
        return await this.vectorStore.enhancedQuery(
          queryText,
          textEmbedding,
          topK
        );
      } else if (searchMode === "hybrid") {
        // Hybrid search (text + images)
        const textResults = await this.vectorStore.searchText(textEmbedding, topK);

        let imageResults = [];
        if (includeImages) {
          const imageEmbedding = await this.clipEmbedder.embedText(queryText);
          imageResults = await this.vectorStore.searchImages(imageEmbedding, topK);
        }

        return {
          textResults,
          imageResults,
          totalResults: textResults.length + imageResults.length,
        };
      } else if (searchMode === "text") {
        // Text-only search
        const textResults = await this.vectorStore.searchText(textEmbedding, topK);
        return { textResults, imageResults: [], totalResults: textResults.length };
      } else {
        // Image-only search
        const imageEmbedding = await this.clipEmbedder.embedText(queryText);
        const imageResults = await this.vectorStore.searchImages(imageEmbedding, topK);
        return { textResults: [], imageResults, totalResults: imageResults.length };
      }
    } catch (error) {
      this.log(`Query error: ${error.message}`);
      throw error;
    }
  }

  /**
   * Get embedding dimension for text
   */
  getTextDimension() {
    // Ollama nomic-embed-text: 768D
    // HuggingFace all-MiniLM-L6-v2: 384D
    return this.textModel.includes("nomic") ? 768 : 384;
  }

  /**
   * Get embedding dimension for images
   */
  getImageDimension() {
    // CLIP ViT-B/32: 512D
    return 512;
  }
}

module.exports = {
  MultimodalEmbedder,
};
