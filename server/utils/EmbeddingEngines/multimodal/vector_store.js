const { ChromaClient } = require("chromadb");
const fs = require("fs");
const path = require("path");

/**
 * Multimodal Vector Store using ChromaDB
 *
 * Implements dual-collection storage:
 * - text_chunks: Text embeddings (768D/384D)
 * - image_chunks: Image embeddings (512D CLIP)
 *
 * Supports:
 * - Two-stage enhanced retrieval
 * - Section-priority image matching
 * - Context-aware scoring
 */
class MultimodalVectorStore {
  constructor(storagePath) {
    this.storagePath = storagePath;
    this.client = null;
    this.textCollection = null;
    this.imageCollection = null;
    this.initialized = false;
    this.initPromise = null;

    // External storage for image metadata and objects
    this.imageMetadataPath = path.join(storagePath, "image_metadata.json");
    this.imageObjectsPath = path.join(storagePath, "image_objects.json");

    this.imageMetadata = {};
    this.imageObjects = {};

    this.log("Initializing MultimodalVectorStore");
  }

  /**
   * Ensure store is initialized before operations
   */
  async #ensureInitialized() {
    if (this.initialized) return;
    if (this.initPromise) return this.initPromise;
    this.initPromise = this.#init();
    await this.initPromise;
  }

  log(text, ...args) {
    console.log(`\x1b[34m[MultimodalVectorStore]\x1b[0m ${text}`, ...args);
  }

  /**
   * Initialize ChromaDB client and collections
   */
  async #init() {
    try {
      // Ensure storage directory exists (for metadata files)
      if (!fs.existsSync(this.storagePath)) {
        fs.mkdirSync(this.storagePath, { recursive: true });
      }

      // Initialize ChromaDB client - use same endpoint as main ChromaDB provider
      // ChromaDB requires an HTTP endpoint, not a file path
      const chromaEndpoint = process.env.CHROMA_ENDPOINT || "http://localhost:8000";

      // Parse authentication header if provided
      const parseAuthHeader = (headerValue) => {
        const [type, value] = headerValue.split(" ");
        if (type === "Authorization") return { Authorization: value };
        return { [type]: value };
      };

      const clientConfig = {
        path: chromaEndpoint,
      };

      // Add authentication if configured
      if (process.env.CHROMA_API_HEADER && process.env.CHROMA_API_KEY) {
        clientConfig.fetchOptions = {
          headers: parseAuthHeader(
            `${process.env.CHROMA_API_HEADER} ${process.env.CHROMA_API_KEY}`
          ),
        };
      }

      this.client = new ChromaClient(clientConfig);

      this.log(`Connecting to ChromaDB at ${chromaEndpoint}`);

      // Get or create collections with unique names for multimodal system
      const textCollectionName = "multimodal_text_chunks";
      const imageCollectionName = "multimodal_image_chunks";

      // List existing collections to check if they exist
      const existingCollections = await this.client.listCollections();
      const existingNames = existingCollections.map(c => c.name);

      this.log(`Existing collections: [${existingNames.join(', ')}]`);

      // Get or create text collection - use getOrCreateCollection to avoid race conditions
      try {
        this.textCollection = await this.client.getOrCreateCollection({
          name: textCollectionName,
          metadata: { "hnsw:space": "cosine" },
        });
        this.log(`Ready: ${textCollectionName}`);
      } catch (error) {
        this.log(`Error with text collection: ${error.message}`);
        // Try to just get it if creation failed
        this.textCollection = await this.client.getCollection({
          name: textCollectionName,
        });
        this.log(`Retrieved existing: ${textCollectionName}`);
      }

      // Get or create image collection
      try {
        this.imageCollection = await this.client.getOrCreateCollection({
          name: imageCollectionName,
          metadata: { "hnsw:space": "cosine" },
        });
        this.log(`Ready: ${imageCollectionName}`);
      } catch (error) {
        this.log(`Error with image collection: ${error.message}`);
        // Try to just get it if creation failed
        this.imageCollection = await this.client.getCollection({
          name: imageCollectionName,
        });
        this.log(`Retrieved existing: ${imageCollectionName}`);
      }

      // Load external metadata
      this.#loadMetadata();

      this.initialized = true;
      this.log("ChromaDB initialized with dual collections");
    } catch (error) {
      this.log(`Initialization error: ${error.message}`);
      this.log(`Stack trace: ${error.stack}`);
      this.initialized = false;
      this.initPromise = null;
      throw error;
    }
  }

  /**
   * Load image metadata from file
   */
  #loadMetadata() {
    if (fs.existsSync(this.imageMetadataPath)) {
      this.imageMetadata = JSON.parse(
        fs.readFileSync(this.imageMetadataPath, "utf-8")
      );
    }

    if (fs.existsSync(this.imageObjectsPath)) {
      this.imageObjects = JSON.parse(
        fs.readFileSync(this.imageObjectsPath, "utf-8")
      );
    }
  }

  /**
   * Save image metadata to file
   */
  #saveMetadata() {
    fs.writeFileSync(
      this.imageMetadataPath,
      JSON.stringify(this.imageMetadata, null, 2)
    );

    fs.writeFileSync(
      this.imageObjectsPath,
      JSON.stringify(this.imageObjects, null, 2)
    );
  }

  /**
   * Add text chunks to vector store
   */
  async addTextChunks(textChunks, embeddings, documentName) {
    await this.#ensureInitialized();
    if (textChunks.length === 0) return;

    const ids = textChunks.map(chunk => chunk.id);
    const documents = textChunks.map(chunk => chunk.text);
    const metadatas = textChunks.map(chunk => ({
      documentName,
      pageNumber: chunk.pageNumber || 0,
      chunkIndex: chunk.chunkIndex,
      chunkType: "text",
      contentType: "text",
    }));

    await this.textCollection.add({
      ids,
      embeddings,
      documents,
      metadatas,
    });

    this.log(`Added ${textChunks.length} text chunks`);
  }

  /**
   * Add image chunks to vector store
   */
  async addImageChunks(images, embeddings, documentName) {
    await this.#ensureInitialized();
    if (images.length === 0) return;

    const ids = images.map(img => img.id);
    const documents = images.map(
      img => `${img.caption} ${img.ocrText} ${img.surroundingText}`.trim()
    );
    const metadatas = images.map(img => ({
      documentName,
      pageNumber: img.pageNumber || 0,
      caption: img.caption || "",
      ocrText: img.ocrText || "",
      contentType: "image",
    }));

    await this.imageCollection.add({
      ids,
      embeddings,
      documents,
      metadatas,
    });

    // Store additional metadata and image objects
    for (const img of images) {
      this.imageMetadata[img.id] = {
        documentName,
        pageNumber: img.pageNumber,
        caption: img.caption,
        ocrText: img.ocrText,
        surroundingText: img.surroundingText,
      };

      // Store image as base64 string
      if (img.image && Buffer.isBuffer(img.image)) {
        this.imageObjects[img.id] = img.image.toString("base64");
      }
    }

    this.#saveMetadata();
    this.log(`Added ${images.length} image chunks`);
  }

  /**
   * Search text chunks
   */
  async searchText(queryEmbedding, topK = 5, filter = {}) {
    await this.#ensureInitialized();
    const results = await this.textCollection.query({
      queryEmbeddings: [queryEmbedding],
      nResults: topK,
      where: Object.keys(filter).length > 0 ? filter : undefined,
    });

    return this.#formatResults(results, "text");
  }

  /**
   * Search image chunks
   */
  async searchImages(queryEmbedding, topK = 5, filter = {}) {
    await this.#ensureInitialized();
    const results = await this.imageCollection.query({
      queryEmbeddings: [queryEmbedding],
      nResults: topK,
      where: Object.keys(filter).length > 0 ? filter : undefined,
    });

    const formatted = this.#formatResults(results, "image");

    // Add extended metadata and image objects
    for (const result of formatted) {
      if (this.imageMetadata[result.id]) {
        Object.assign(result, this.imageMetadata[result.id]);
      }

      if (this.imageObjects[result.id]) {
        result.imageData = this.imageObjects[result.id];
      }
    }

    return formatted;
  }

  /**
   * Enhanced two-stage query
   * Stage 1: Text search for context
   * Stage 2: Context-aware image search
   */
  async enhancedQuery(queryText, textEmbedding, topK = 5) {
    await this.#ensureInitialized();
    this.log(`Enhanced query: "${queryText}"`);

    // Stage 1: Text retrieval for context
    const textResults = await this.searchText(textEmbedding, topK * 2);

    if (textResults.length === 0) {
      return {
        textResults: [],
        imageResults: [],
        totalResults: 0,
        mode: "enhanced",
      };
    }

    // Extract context from text results
    const contextPages = [...new Set(textResults.map(r => r.metadata.pageNumber))];
    const contextDocs = [...new Set(textResults.map(r => r.metadata.documentName))];

    this.log(`Context: ${contextPages.length} pages, ${contextDocs.length} documents`);

    // Stage 2: Context-aware image search
    // Search images from same pages
    const imageResults = [];
    for (const page of contextPages) {
      const pageImages = await this.searchImages(
        textEmbedding, // Use text embedding for cross-modal search
        Math.ceil(topK / contextPages.length),
        { pageNumber: page }
      );

      // Boost images from relevant pages
      pageImages.forEach(img => {
        img.similarityScore = (img.similarityScore || 0) + 0.2; // Page match bonus
        img.contextBoost = 0.2;
      });

      imageResults.push(...pageImages);
    }

    // Sort by boosted similarity
    imageResults.sort((a, b) => b.similarityScore - a.similarityScore);

    return {
      textResults: textResults.slice(0, topK),
      imageResults: imageResults.slice(0, topK),
      totalResults: textResults.length + imageResults.length,
      mode: "enhanced",
      context: {
        pages: contextPages,
        documents: contextDocs,
      },
    };
  }

  /**
   * Format ChromaDB results
   */
  #formatResults(results, contentType) {
    const formatted = [];

    if (!results.ids || results.ids.length === 0) return formatted;

    const ids = results.ids[0];
    const documents = results.documents[0];
    const metadatas = results.metadatas[0];
    const distances = results.distances[0];

    for (let i = 0; i < ids.length; i++) {
      formatted.push({
        id: ids[i],
        text: documents[i],
        metadata: metadatas[i],
        distance: distances[i],
        similarityScore: Math.max(0, 1 - distances[i]),
        contentType,
      });
    }

    return formatted;
  }

  /**
   * Delete document from both collections
   */
  async deleteDocument(documentName) {
    await this.#ensureInitialized();
    // Delete from text collection
    const textResults = await this.textCollection.get({
      where: { documentName },
    });
    if (textResults.ids.length > 0) {
      await this.textCollection.delete({
        ids: textResults.ids,
      });
    }

    // Delete from image collection
    const imageResults = await this.imageCollection.get({
      where: { documentName },
    });
    if (imageResults.ids.length > 0) {
      await this.imageCollection.delete({
        ids: imageResults.ids,
      });

      // Remove from external storage
      for (const id of imageResults.ids) {
        delete this.imageMetadata[id];
        delete this.imageObjects[id];
      }
      this.#saveMetadata();
    }

    this.log(`Deleted document: ${documentName}`);
  }

  /**
   * Get statistics
   */
  async getStats() {
    await this.#ensureInitialized();
    const textCount = await this.textCollection.count();
    const imageCount = await this.imageCollection.count();

    return {
      textChunks: textCount,
      imageChunks: imageCount,
      totalChunks: textCount + imageCount,
      storagePath: this.storagePath,
    };
  }
}

module.exports = {
  MultimodalVectorStore,
};
