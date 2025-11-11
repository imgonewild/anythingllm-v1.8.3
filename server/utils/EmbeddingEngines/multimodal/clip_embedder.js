const sharp = require("sharp");

// Polyfill for process.getBuiltinModule (Node.js 22.3.0+)
// Required by @xenova/transformers in older Node.js versions
if (typeof process !== "undefined" && !process.getBuiltinModule) {
  process.getBuiltinModule = (module) => {
    try {
      return require(module);
    } catch (error) {
      return null;
    }
  };
}

// Explicitly load canvas to ensure DOM polyfills are available
// This must happen before @xenova/transformers is loaded
try {
  const canvas = require("canvas");

  // Make canvas classes available globally for transformers.js
  if (typeof global !== "undefined") {
    // ImageData is available from node-canvas
    if (!global.ImageData && canvas.ImageData) {
      global.ImageData = canvas.ImageData;
    }

    // DOMMatrix and Path2D may not be in older node-canvas versions
    // Provide minimal polyfills if not available
    if (!global.DOMMatrix) {
      global.DOMMatrix = canvas.DOMMatrix || class DOMMatrix {
        constructor() {
          this.a = 1; this.b = 0; this.c = 0;
          this.d = 1; this.e = 0; this.f = 0;
        }
      };
    }

    if (!global.Path2D) {
      global.Path2D = canvas.Path2D || class Path2D {
        constructor() {}
        moveTo() {}
        lineTo() {}
        arc() {}
        closePath() {}
      };
    }
  }
} catch (error) {
  console.warn("[ClipEmbedder] Canvas module not available, some features may not work:", error.message);
}

// Set up environment for Transformers.js in Node.js
process.env.FORCE_NODE_CANVAS = "1";

// Dynamic import for ES Module
let transformers = null;
const loadTransformers = async () => {
  if (!transformers) {
    const tf = await import("@xenova/transformers");

    // Configure environment for Node.js
    if (tf.env) {
      tf.env.useBrowserCache = false;
      tf.env.allowLocalModels = false;
      tf.env.allowRemoteModels = true;
    }

    transformers = tf;
  }
  return transformers;
};

/**
 * CLIP Image and Text Embedder using Transformers.js
 *
 * Uses CLIP ViT-B/32 model for:
 * - Image embeddings (512D)
 * - Text embeddings aligned with image space (512D)
 *
 * This enables cross-modal search (text query → find relevant images)
 */
class ClipEmbedder {
  constructor(modelName = "Xenova/clip-vit-base-patch32") {
    this.modelName = modelName;
    this.imageProcessor = null;
    this.textProcessor = null;
    this.dimension = 512; // CLIP ViT-B/32 output dimension

    this.log(`Initializing CLIP embedder with model: ${modelName}`);
  }

  log(text, ...args) {
    console.log(`\x1b[35m[ClipEmbedder]\x1b[0m ${text}`, ...args);
  }

  /**
   * Initialize CLIP image processor
   */
  async #initImageProcessor() {
    if (!this.imageProcessor) {
      this.log("Loading CLIP image processor...");
      const { pipeline } = await loadTransformers();
      this.imageProcessor = await pipeline(
        "image-feature-extraction",
        this.modelName
      );
      this.log("CLIP image processor loaded");
    }
  }

  /**
   * Initialize CLIP text processor
   */
  async #initTextProcessor() {
    if (!this.textProcessor) {
      this.log("Loading CLIP text processor...");
      const { pipeline } = await loadTransformers();
      this.textProcessor = await pipeline(
        "feature-extraction",
        this.modelName
      );
      this.log("CLIP text processor loaded");
    }
  }

  /**
   * Preprocess image buffer to the format expected by CLIP
   * @param {Buffer} imageBuffer - Image buffer
   * @returns {Promise<Buffer>} - Preprocessed image buffer
   */
  async preprocessImage(imageBuffer) {
    try {
      // Resize image to 224x224 (CLIP input size)
      const resized = await sharp(imageBuffer)
        .resize(224, 224, { fit: "cover" })
        .toBuffer();

      return resized;
    } catch (error) {
      this.log(`Error preprocessing image: ${error.message}`);
      throw error;
    }
  }

  /**
   * Embed an image using CLIP
   * @param {Buffer|string} image - Image buffer or base64 string
   * @returns {Promise<number[]>} - 512D embedding vector
   */
  async embedImage(image) {
    await this.#initImageProcessor();

    try {
      let imageBuffer;

      // Handle different input types
      if (typeof image === "string") {
        // Base64 string
        imageBuffer = Buffer.from(image, "base64");
      } else if (Buffer.isBuffer(image)) {
        imageBuffer = image;
      } else {
        throw new Error("Unsupported image format. Expected Buffer or base64 string.");
      }

      // Preprocess image
      const preprocessed = await this.preprocessImage(imageBuffer);

      // Generate embedding
      const result = await this.imageProcessor(preprocessed);

      // Extract embedding (result is typically a tensor)
      let embedding;
      if (Array.isArray(result)) {
        embedding = result;
      } else if (result.data) {
        embedding = Array.from(result.data);
      } else if (result.tolist) {
        embedding = result.tolist();
      } else {
        throw new Error("Unexpected CLIP output format");
      }

      // Normalize embedding
      const norm = Math.sqrt(embedding.reduce((sum, val) => sum + val * val, 0));
      const normalized = embedding.map(val => val / norm);

      return normalized;
    } catch (error) {
      this.log(`Error embedding image: ${error.message}`);
      throw error;
    }
  }

  /**
   * Embed text using CLIP (for cross-modal search)
   * @param {string} text - Text to embed
   * @returns {Promise<number[]>} - 512D embedding vector aligned with image space
   */
  async embedText(text) {
    await this.#initTextProcessor();

    try {
      // Generate text embedding using CLIP
      const result = await this.textProcessor(text, {
        pooling: "mean",
        normalize: true,
      });

      // Extract embedding
      let embedding;
      if (Array.isArray(result)) {
        embedding = result;
      } else if (result.data) {
        embedding = Array.from(result.data);
      } else if (result.tolist) {
        embedding = result.tolist();
      } else {
        throw new Error("Unexpected CLIP text output format");
      }

      // Normalize embedding
      const norm = Math.sqrt(embedding.reduce((sum, val) => sum + val * val, 0));
      const normalized = embedding.map(val => val / norm);

      return normalized;
    } catch (error) {
      this.log(`Error embedding text: ${error.message}`);
      throw error;
    }
  }

  /**
   * Embed multiple images in batch
   * @param {Array<Buffer|string>} images - Array of image buffers or base64 strings
   * @returns {Promise<Array<number[]>>} - Array of 512D embedding vectors
   */
  async embedImagesBatch(images) {
    this.log(`Embedding ${images.length} images in batch`);

    const embeddings = [];
    for (const image of images) {
      const embedding = await this.embedImage(image);
      embeddings.push(embedding);
    }

    return embeddings;
  }

  /**
   * Calculate similarity between image and text embeddings
   * @param {number[]} imageEmbedding - Image embedding
   * @param {number[]} textEmbedding - Text embedding
   * @returns {number} - Cosine similarity (0-1)
   */
  calculateSimilarity(imageEmbedding, textEmbedding) {
    if (imageEmbedding.length !== textEmbedding.length) {
      throw new Error("Embedding dimensions don't match");
    }

    // Cosine similarity (embeddings are already normalized)
    const dotProduct = imageEmbedding.reduce(
      (sum, val, i) => sum + val * textEmbedding[i],
      0
    );

    // Convert from [-1, 1] to [0, 1]
    return (dotProduct + 1) / 2;
  }

  /**
   * Get embedding dimension
   */
  getDimension() {
    return this.dimension;
  }
}

module.exports = {
  ClipEmbedder,
};
