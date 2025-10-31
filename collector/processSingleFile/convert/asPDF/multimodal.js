const { v4 } = require("uuid");
const {
  createdDate,
  trashFile,
  writeToServerDocuments,
} = require("../../../utils/files");
const { tokenizeString } = require("../../../utils/tokenizer");
const { default: slugify } = require("slugify");
const PDFLoader = require("./PDFLoader");
const OCRLoader = require("../../../utils/OCRLoader");
const fs = require("fs");
const path = require("path");
const { createCanvas, loadImage } = require("canvas");
const { createWorker } = require("tesseract.js");

/**
 * Enhanced PDF processor with multimodal support
 * Extracts both text AND images from PDFs for multimodal RAG
 */
async function asPdfMultimodal({ fullFilePath = "", filename = "", options = {} }) {
  const pdfLoader = new PDFLoader(fullFilePath, {
    splitPages: true,
  });

  console.log(`-- Working ${filename} (MULTIMODAL MODE) --`);
  const pageContent = [];
  let docs = await pdfLoader.load();

  // Extract text content
  if (docs.length === 0) {
    console.log(
      `[asPDF-Multimodal] No text content found for ${filename}. Will attempt OCR parse.`
    );
    docs = await new OCRLoader({
      targetLanguages: options?.ocr?.langList,
    }).ocrPDF(fullFilePath);
  }

  for (const doc of docs) {
    console.log(
      `-- Parsing content from pg ${
        doc.metadata?.loc?.pageNumber || "unknown"
      } --`
    );
    if (!doc.pageContent || !doc.pageContent.length) continue;
    pageContent.push(doc.pageContent);
  }

  if (!pageContent.length) {
    console.error(`[asPDF-Multimodal] Resulting text content was empty for ${filename}.`);
    trashFile(fullFilePath);
    return {
      success: false,
      reason: `No text content found in ${filename}.`,
      documents: [],
    };
  }

  // Extract images from PDF
  console.log(`-- Extracting images from ${filename} --`);
  const images = await extractImagesFromPDF(fullFilePath, filename, options);
  console.log(`-- Extracted ${images.length} images --`);

  const content = pageContent.join("");
  const data = {
    id: v4(),
    url: "file://" + fullFilePath,
    title: filename,
    docAuthor: docs[0]?.metadata?.pdf?.info?.Creator || "no author found",
    description: docs[0]?.metadata?.pdf?.info?.Title || "No description found.",
    docSource: "pdf file uploaded by the user.",
    chunkSource: "",
    published: createdDate(fullFilePath),
    wordCount: content.split(" ").length,
    pageContent: content,
    token_count_estimate: tokenizeString(content),

    // NEW: Multimodal data
    images: images, // Array of image objects
    isMultimodal: true,
    imageCount: images.length,
  };

  const document = writeToServerDocuments({
    data,
    filename: `${slugify(filename)}-${data.id}`,
    options: { parseOnly: options.parseOnly },
  });

  trashFile(fullFilePath);
  console.log(
    `[SUCCESS]: ${filename} converted & ready for multimodal embedding.\n` +
    `Text content: ${content.length} chars, Images: ${images.length}\n`
  );

  return { success: true, reason: null, documents: [document] };
}

/**
 * Extract images from PDF using pdf-lib
 */
async function extractImagesFromPDF(pdfPath, filename, options = {}) {
  const { PDFDocument } = require("pdf-lib");
  const images = [];

  try {
    const pdfBuffer = fs.readFileSync(pdfPath);
    const pdfDoc = await PDFDocument.load(pdfBuffer);
    const pages = pdfDoc.getPages();

    console.log(`Processing ${pages.length} pages for images...`);

    for (let pageIndex = 0; pageIndex < pages.length; pageIndex++) {
      const page = pages[pageIndex];
      const pageNumber = pageIndex + 1;

      // Get images from page
      // Note: pdf-lib doesn't provide direct image extraction
      // We'll use a different approach with pdf2pic or similar

      // For now, use pdf2pic to extract page as image
      const pageImages = await extractImagesFromPage(
        pdfPath,
        pageNumber,
        filename
      );

      images.push(...pageImages);
    }

    return images;
  } catch (error) {
    console.error(`Error extracting images from PDF: ${error.message}`);
    return [];
  }
}

/**
 * Extract images from a specific page using pdf2pic
 */
async function extractImagesFromPage(pdfPath, pageNumber, filename) {
  const { fromPath } = require("pdf2pic");
  const images = [];

  try {
    // Convert PDF page to image
    const options = {
      density: 100,
      saveFilename: `${filename}_page_${pageNumber}`,
      savePath: path.dirname(pdfPath),
      format: "png",
      width: 1200,
      height: 1600,
    };

    const convert = fromPath(pdfPath, options);
    const pageImage = await convert(pageNumber, { responseType: "buffer" });

    // Only add if the page actually has content (not blank)
    if (pageImage.buffer && pageImage.buffer.length > 10000) {
      const imageData = {
        id: `${filename}_page${pageNumber}_img_${Date.now()}`,
        pageNumber,
        imageBuffer: pageImage.buffer.toString("base64"),
        caption: `Figure from ${filename} - Page ${pageNumber}`,
        surroundingText: "", // Will be filled by context extraction
        ocrText: "", // Will be performed during embedding
        documentName: filename,
      };

      images.push(imageData);
    }

    // Clean up temporary file if created
    try {
      if (pageImage.path && fs.existsSync(pageImage.path)) {
        fs.unlinkSync(pageImage.path);
      }
    } catch {}

  } catch (error) {
    console.error(`Error extracting image from page ${pageNumber}: ${error.message}`);
  }

  return images;
}

module.exports = asPdfMultimodal;
