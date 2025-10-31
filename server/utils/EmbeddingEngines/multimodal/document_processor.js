const fs = require("fs");
const path = require("path");
const pdfParse = require("pdf-parse");
const { createWorker } = require("tesseract.js");
const sharp = require("sharp");

/**
 * Document Processor for Multimodal RAG
 *
 * Extracts both text and images from documents:
 * - PDF: Uses pdf-parse for text, pdf-lib for images
 * - DOCX: Uses mammoth for text and image extraction
 * - TXT: Direct text reading
 *
 * Performs OCR on extracted images
 * Extracts contextual information around images
 */
class DocumentProcessor {
  constructor() {
    this.supportedFormats = [".pdf", ".docx", ".doc", ".txt"];
    this.chunkSize = 500; // characters per text chunk
    this.ocrWorker = null;

    this.log("DocumentProcessor initialized");
  }

  log(text, ...args) {
    console.log(`\x1b[33m[DocumentProcessor]\x1b[0m ${text}`, ...args);
  }

  /**
   * Initialize Tesseract OCR worker
   */
  async #initOCR() {
    if (!this.ocrWorker) {
      this.log("Initializing Tesseract OCR...");
      this.ocrWorker = await createWorker("eng");
      this.log("Tesseract OCR initialized");
    }
  }

  /**
   * Process a document and extract text chunks + images
   * @param {string} filePath - Path to document
   * @param {Object} options - Processing options
   * @returns {Promise<Object>} - {textChunks, images}
   */
  async processDocument(filePath, options = {}) {
    const ext = path.extname(filePath).toLowerCase();

    if (!this.supportedFormats.includes(ext)) {
      throw new Error(`Unsupported file format: ${ext}`);
    }

    this.log(`Processing document: ${filePath}`);

    let textChunks = [];
    let images = [];

    if (ext === ".pdf") {
      const result = await this.processPDF(filePath, options);
      textChunks = result.textChunks;
      images = result.images;
    } else if (ext === ".docx" || ext === ".doc") {
      const result = await this.processDOCX(filePath, options);
      textChunks = result.textChunks;
      images = result.images;
    } else if (ext === ".txt") {
      textChunks = await this.processTXT(filePath, options);
      images = [];
    }

    this.log(`Extracted ${textChunks.length} text chunks and ${images.length} images`);

    return { textChunks, images };
  }

  /**
   * Process PDF document
   */
  async processPDF(filePath, options = {}) {
    const dataBuffer = fs.readFileSync(filePath);
    const data = await pdfParse(dataBuffer);

    // Extract text and create chunks
    const textChunks = this.createTextChunks(
      data.text,
      path.basename(filePath),
      options
    );

    // Extract images from PDF
    // Note: pdf-parse doesn't extract images, we need pdf-lib or similar
    // For now, return empty images array - will be enhanced via collector
    const images = [];

    // TODO: Implement image extraction from PDF
    // This will be handled by the enhanced collector service

    return { textChunks, images };
  }

  /**
   * Process DOCX document
   */
  async processDOCX(filePath, options = {}) {
    const mammoth = require("mammoth");

    // Extract text
    const result = await mammoth.extractRawText({ path: filePath });
    const text = result.value;

    const textChunks = this.createTextChunks(
      text,
      path.basename(filePath),
      options
    );

    // Extract images
    // TODO: Implement image extraction from DOCX
    // This will be handled by the enhanced collector service
    const images = [];

    return { textChunks, images };
  }

  /**
   * Process TXT document
   */
  async processTXT(filePath, options = {}) {
    const text = fs.readFileSync(filePath, "utf-8");
    return this.createTextChunks(text, path.basename(filePath), options);
  }

  /**
   * Create text chunks from document text
   */
  createTextChunks(text, documentName, options = {}) {
    const chunkSize = options.chunkSize || this.chunkSize;
    const chunks = [];

    // Split into sentences first
    const sentences = text.match(/[^.!?]+[.!?]+/g) || [text];

    let currentChunk = "";
    let chunkIndex = 0;

    for (const sentence of sentences) {
      if ((currentChunk + sentence).length <= chunkSize) {
        currentChunk += sentence;
      } else {
        if (currentChunk.trim()) {
          chunks.push({
            id: `${documentName}_chunk_${chunkIndex}`,
            text: currentChunk.trim(),
            chunkIndex,
            documentName,
            pageNumber: null, // Will be set if available
            metadata: {
              chunkType: "text",
              contentType: "text",
            },
          });
          chunkIndex++;
        }
        currentChunk = sentence;
      }
    }

    // Add last chunk
    if (currentChunk.trim()) {
      chunks.push({
        id: `${documentName}_chunk_${chunkIndex}`,
        text: currentChunk.trim(),
        chunkIndex,
        documentName,
        pageNumber: null,
        metadata: {
          chunkType: "text",
          contentType: "text",
        },
      });
    }

    return chunks;
  }

  /**
   * Perform OCR on an image
   * @param {Buffer} imageBuffer - Image buffer
   * @returns {Promise<string>} - Extracted text
   */
  async performOCR(imageBuffer) {
    try {
      await this.#initOCR();

      // Preprocess image for better OCR
      const preprocessed = await sharp(imageBuffer)
        .resize(2000, 2000, { fit: "inside", withoutEnlargement: true })
        .greyscale()
        .normalize()
        .toBuffer();

      const { data: { text } } = await this.ocrWorker.recognize(preprocessed);
      return text.trim();
    } catch (error) {
      this.log(`OCR error: ${error.message}`);
      return "";
    }
  }

  /**
   * Process image data from collector
   * @param {Object} imageData - Image data from collector
   * @returns {Promise<Object>} - Processed image data with OCR
   */
  async processImageData(imageData) {
    const {
      imageBuffer,
      pageNumber,
      caption = "",
      surroundingText = "",
      documentName,
    } = imageData;

    // Perform OCR if image buffer is provided
    let ocrText = "";
    if (imageBuffer) {
      ocrText = await this.performOCR(imageBuffer);
    }

    return {
      id: `${documentName}_page${pageNumber}_img_${Date.now()}`,
      image: imageBuffer,
      pageNumber,
      documentName,
      caption,
      ocrText,
      surroundingText,
      metadata: {
        contentType: "image",
        hasOCR: ocrText.length > 0,
        captionLength: caption.length,
      },
    };
  }

  /**
   * Cleanup OCR worker
   */
  async cleanup() {
    if (this.ocrWorker) {
      await this.ocrWorker.terminate();
      this.ocrWorker = null;
      this.log("OCR worker terminated");
    }
  }
}

module.exports = {
  DocumentProcessor,
};
