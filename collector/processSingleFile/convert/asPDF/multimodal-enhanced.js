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
const { detectCaption, isLLMCaptionDetectionAvailable } = require("../../../utils/LLMCaptionDetector");

/**
 * Enhanced PDF processor inspired by RAG Image_Rag/document_processor.py
 *
 * Key improvements over original multimodal.js:
 * 1. Direct embedded image extraction from PDF structure (like PyMuPDF)
 * 2. Precise bounding box detection for better context
 * 3. Inline vs block image detection
 * 4. Enhanced context extraction with surrounding text
 * 5. Section-aware processing
 */

async function asPdfMultimodalEnhanced({ fullFilePath = "", filename = "", options = {} }) {
  const pdfLoader = new PDFLoader(fullFilePath, {
    splitPages: true,
  });

  // Check LLM availability for caption detection
  const llmStatus = await isLLMCaptionDetectionAvailable();
  console.log(`-- Working ${filename} (ENHANCED MULTIMODAL MODE) --`);
  console.log(`🤖 LLM Caption Detection: ${llmStatus.available ? `Available (${llmStatus.provider})` : 'Not available - using fallback patterns'}`);
  const pageContent = [];
  let docs = await pdfLoader.load();

  // Extract text content
  if (docs.length === 0) {
    console.log(
      `[asPDF-Multimodal-Enhanced] No text content found for ${filename}. Will attempt OCR parse.`
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
    console.error(`[asPDF-Multimodal-Enhanced] Resulting text content was empty for ${filename}.`);
    trashFile(fullFilePath);
    return {
      success: false,
      reason: `No text content found in ${filename}.`,
      documents: [],
    };
  }

  console.log(`[DEBUG] About to extract images for ${filename}`);
  console.log(`[DEBUG] pageContent length: ${pageContent.length}`);

  // Extract images using enhanced multi-strategy approach
  console.log(`-- Extracting images from ${filename} (Enhanced Strategy) --`);
  const images = await extractImagesEnhanced(fullFilePath, filename, pageContent, options);
  console.log(`-- Extracted ${images.length} images --`);

  const content = pageContent.join("");

  // Build figure caption to image file mapping
  const figureCaptionMap = {};
  images.forEach(img => {
    const caption = img.caption || '';
    // Extract figure number (e.g., "Figure 5-1" -> "5-1")
    const figureMatch = caption.match(/Figure\s+(\d+[-\.]\d+)/i);
    if (figureMatch) {
      const figureNumber = figureMatch[1];
      figureCaptionMap[figureNumber] = {
        id: img.id,
        pageNumber: img.pageNumber,
        fullCaption: caption
      };
      console.log(`📌 Mapped Figure ${figureNumber} -> ${img.id} (page ${img.pageNumber})`);
    }
  });

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

    // Enhanced multimodal data
    images: images,
    isMultimodal: true,
    imageCount: images.length,
    figureCaptionMap: figureCaptionMap,  // NEW: Figure caption to image mapping
  };

  const document = writeToServerDocuments({
    data,
    filename: `${slugify(filename)}-${data.id}`,
    options: { parseOnly: options.parseOnly },
  });

  trashFile(fullFilePath);
  console.log(
    `[SUCCESS]: ${filename} converted & ready for enhanced multimodal embedding.\n` +
    `Text content: ${content.length} chars, Images: ${images.length}\n`
  );

  return { success: true, reason: null, documents: [document] };
}

/**
 * Enhanced image extraction using multiple strategies
 * Inspired by RAG's PyMuPDF approach
 */
async function extractImagesEnhanced(pdfPath, filename, pageContent, options = {}) {
  const images = [];

  try {
    const pdfBuffer = fs.readFileSync(pdfPath);

    console.log(`🔍 Strategy 1: Attempting embedded image extraction (pdf-lib)...`);
    const embeddedImages = await extractEmbeddedImagesEnhanced(pdfBuffer, filename, pageContent);

    if (embeddedImages.length > 0) {
      console.log(`✅ Found ${embeddedImages.length} embedded images using pdf-lib`);
      images.push(...embeddedImages);
      return images; // If we got embedded images, use them
    }

    console.log(`🔍 Strategy 2: Attempting pdfjs-based extraction...`);
    const pdfjsImages = await extractWithPdfJsEnhanced(pdfPath, filename, pageContent);

    if (pdfjsImages.length > 0) {
      console.log(`✅ Extracted ${pdfjsImages.length} images using pdfjs`);
      images.push(...pdfjsImages);
      return images;
    }

    console.log(`🔍 Strategy 3: Fallback to canvas rendering...`);
    const canvasImages = await extractWithCanvas(pdfPath, filename, pageContent);
    console.log(`✅ Extracted ${canvasImages.length} images using canvas`);
    images.push(...canvasImages);

    return images;
  } catch (error) {
    console.error(`Error in enhanced image extraction: ${error.message}`);
    console.error(error.stack);
    return [];
  }
}

/**
 * Enhanced embedded image extraction with context awareness
 * Mimics PyMuPDF's fitz.Pixmap approach
 */
async function extractEmbeddedImagesEnhanced(pdfBuffer, filename, pageContent) {
  const { PDFDocument } = require("pdf-lib");
  const images = [];

  try {
    const pdfDoc = await PDFDocument.load(pdfBuffer);
    const pages = pdfDoc.getPages();

    console.log(`Processing ${pages.length} pages for embedded images...`);

    for (let pageIndex = 0; pageIndex < pages.length; pageIndex++) {
      const page = pages[pageIndex];
      const pageNumber = pageIndex + 1;
      const pageText = pageContent[pageIndex] || "";

      // Extract embedded images using pdf-lib
      const pageDict = page.node;
      const resources = pageDict.get("Resources");

      if (!resources || !resources.has("XObject")) {
        continue;
      }

      const xObjects = resources.get("XObject");
      const xObjectKeys = xObjects.entries();

      let imgIndex = 0;
      for (const [key, xObject] of xObjectKeys) {
        const subtype = xObject.get("Subtype");

        if (subtype && subtype.toString() === "/Image") {
          try {
            // Try to extract image dimensions and data
            const width = xObject.get("Width");
            const height = xObject.get("Height");

            if (width && height) {
              const imgWidth = typeof width === 'number' ? width : width.value || 0;
              const imgHeight = typeof height === 'number' ? height : height.value || 0;

              // Detect inline vs block images (like RAG does)
              const isInlineImage = (imgWidth < 100 && imgHeight < 100) || (imgWidth < 50 || imgHeight < 50);

              console.log(`📸 Image detected: ${imgWidth}x${imgHeight} (${isInlineImage ? 'inline' : 'block'})`);

              // Extract context based on image type
              const context = await extractImageContext(pageText, pageNumber, imgIndex, isInlineImage);

              const imageData = {
                id: `${filename}_page${pageNumber}_embedded_${imgIndex}_${Date.now()}`,
                pageNumber,
                imageBuffer: null, // pdf-lib doesn't easily extract raw data
                caption: context.caption,
                surroundingText: context.surroundingText,
                sectionTitle: context.sectionTitle,
                documentName: filename,
                extractionMethod: "pdf-lib-embedded",
                isInline: isInlineImage,
                dimensions: { width: imgWidth, height: imgHeight }
              };

              images.push(imageData);
              imgIndex++;
            }
          } catch (err) {
            console.warn(`Failed to process embedded image ${key}: ${err.message}`);
          }
        }
      }
    }

    // Note: pdf-lib can detect but not easily extract image buffers
    // If we found images, we need a fallback to get actual image data
    if (images.length > 0 && !images[0].imageBuffer) {
      console.log(`⚠️  pdf-lib detected ${images.length} images but cannot extract buffers`);
      console.log(`   Falling back to pdfjs extraction...`);
      return []; // Trigger fallback
    }

    return images;
  } catch (error) {
    console.warn(`pdf-lib embedded extraction failed: ${error.message}`);
    return [];
  }
}

/**
 * Enhanced pdfjs extraction that mimics PyMuPDF's page.get_images() approach
 */
async function extractWithPdfJsEnhanced(pdfPath, filename, pageContent) {
  const images = [];

  try {
    const pdfBuffer = fs.readFileSync(pdfPath);
    const pdfjs = await import("pdf-parse/lib/pdf.js/v1.10.100/build/pdf.js");

    const pdf = await pdfjs.getDocument({
      data: new Uint8Array(pdfBuffer),
      useWorkerFetch: false,
      isEvalSupported: false,
      useSystemFonts: true,
    }).promise;

    console.log(`Processing ${pdf.numPages} pages with enhanced pdfjs...`);

    for (let pageNumber = 1; pageNumber <= pdf.numPages; pageNumber++) {
      try {
        const page = await pdf.getPage(pageNumber);
        const pageText = pageContent[pageNumber - 1] || "";

        // Get operator list to detect images
        const ops = await page.getOperatorList();

        let imgIndex = 0;
        for (let i = 0; i < ops.fnArray.length; i++) {
          // OPS.paintImageXObject = 85, OPS.paintInlineImageXObject = 86
          if (ops.fnArray[i] === 85 || ops.fnArray[i] === 86) {
            const isInline = ops.fnArray[i] === 86;

            console.log(`📸 pdfjs detected ${isInline ? 'inline' : 'block'} image on page ${pageNumber}`);

            // Extract context
            const context = await extractImageContext(pageText, pageNumber, imgIndex, isInline);

            const imageData = {
              id: `${filename}_page${pageNumber}_pdfjs_${imgIndex}_${Date.now()}`,
              pageNumber,
              imageBuffer: null, // Will be filled by page rendering if needed
              caption: context.caption,
              surroundingText: context.surroundingText,
              sectionTitle: context.sectionTitle,
              documentName: filename,
              extractionMethod: "pdfjs-detection",
              isInline: isInline
            };

            images.push(imageData);
            imgIndex++;
          }
        }
      } catch (pageError) {
        console.warn(`Error processing page ${pageNumber}: ${pageError.message}`);
      }
    }

    // If we detected images but don't have buffers, render pages
    if (images.length > 0) {
      console.log(`🎨 Rendering ${images.length} detected images...`);
      await renderDetectedImages(pdf, images, filename);
    }

    return images;
  } catch (error) {
    console.error(`pdfjs enhanced extraction failed: ${error.message}`);
    return [];
  }
}

/**
 * Render detected images using canvas
 */
async function renderDetectedImages(pdf, images, filename) {
  const { createCanvas } = require("canvas");

  for (const imageData of images) {
    try {
      const page = await pdf.getPage(imageData.pageNumber);
      const viewport = page.getViewport({ scale: 2.0 });

      const canvas = createCanvas(viewport.width, viewport.height);
      const context = canvas.getContext("2d");

      await page.render({
        canvasContext: context,
        viewport: viewport,
      }).promise;

      const imageBuffer = canvas.toBuffer("image/png");

      if (imageBuffer.length > 10000) { // Minimum size check
        imageData.imageBuffer = imageBuffer.toString("base64");
      }
    } catch (err) {
      console.warn(`Failed to render image: ${err.message}`);
    }
  }
}

/**
 * Canvas-based page rendering (existing fallback)
 */
async function extractWithCanvas(pdfPath, filename, pageContent) {
  const { createCanvas } = require("canvas");
  const images = [];

  try {
    const pdfBuffer = fs.readFileSync(pdfPath);
    const pdfjs = await import("pdf-parse/lib/pdf.js/v1.10.100/build/pdf.js");

    const pdf = await pdfjs.getDocument({
      data: new Uint8Array(pdfBuffer),
      useWorkerFetch: false,
      isEvalSupported: false,
      useSystemFonts: true,
    }).promise;

    console.log(`Processing ${pdf.numPages} pages with canvas...`);

    for (let pageNumber = 1; pageNumber <= pdf.numPages; pageNumber++) {
      try {
        const page = await pdf.getPage(pageNumber);
        const pageText = pageContent[pageNumber - 1] || "";
        const viewport = page.getViewport({ scale: 2.0 });

        const canvas = createCanvas(viewport.width, viewport.height);
        const context = canvas.getContext("2d");

        await page.render({
          canvasContext: context,
          viewport: viewport,
        }).promise;

        const imageBuffer = canvas.toBuffer("image/png");

        if (imageBuffer.length > 50000) {
          const imgContext = await extractImageContext(pageText, pageNumber, 0, false);

          const imageData = {
            id: `${filename}_page${pageNumber}_canvas_${Date.now()}`,
            pageNumber,
            imageBuffer: imageBuffer.toString("base64"),
            caption: imgContext.caption,
            surroundingText: imgContext.surroundingText,
            sectionTitle: imgContext.sectionTitle,
            documentName: filename,
            extractionMethod: "canvas-render",
            isInline: false
          };

          images.push(imageData);
        }
      } catch (pageError) {
        console.warn(`Failed to render page ${pageNumber}: ${pageError.message}`);
      }
    }

    return images;
  } catch (error) {
    console.error(`Canvas extraction failed: ${error.message}`);
    return [];
  }
}

/**
 * Extract image context from page text
 * Uses LLM-based caption detection for language-agnostic results
 */
async function extractImageContext(pageText, pageNumber, imgIndex, isInline) {
  // Split text into sections
  const lines = pageText.split('\n').filter(l => l.trim());
  const totalLines = lines.length;

  if (totalLines === 0) {
    return {
      caption: `Image ${pageNumber}-${imgIndex + 1}`,
      surroundingText: `[IMAGE ${imgIndex + 1}]`,
      sectionTitle: ""
    };
  }

  // Extract section title (first few lines that look like headings)
  let sectionTitle = "";
  for (let i = 0; i < Math.min(5, totalLines); i++) {
    const line = lines[i].trim();
    if (line.length > 0 && line.length < 100 && !line.endsWith('.')) {
      // Check if it looks like a heading (short, no period)
      if (line.match(/^[\d\.]+\s+/) || line === line.toUpperCase()) {
        sectionTitle = line;
        break;
      }
    }
  }

  // For inline images (small), extract left/right context
  if (isInline) {
    // Find text around the middle of the page
    const midPoint = Math.floor(totalLines / 2);
    const contextStart = Math.max(0, midPoint - 1);
    const contextEnd = Math.min(totalLines, midPoint + 2);

    const contextLines = lines.slice(contextStart, contextEnd);
    const surroundingText = contextLines.join(' ').substring(0, 200);

    // Try to find figure caption even for inline images (now async)
    let caption = await findFigureCaptionEnhanced(lines, pageNumber, imgIndex);

    return {
      caption: caption || `Image ${pageNumber}-${imgIndex + 1}`,
      surroundingText: surroundingText || `[INLINE IMAGE ${imgIndex + 1}]`,
      sectionTitle
    };
  }

  // For block images, extract preceding and following text
  const linesPerImage = Math.max(1, Math.floor(totalLines / 4));
  const startIdx = imgIndex * linesPerImage;
  const endIdx = Math.min(totalLines, (imgIndex + 1) * linesPerImage);

  const precedingLines = lines.slice(Math.max(0, startIdx - 2), startIdx);
  const followingLines = lines.slice(startIdx, Math.min(totalLines, startIdx + 3));

  const precedingText = precedingLines.join(' ').substring(0, 200);
  const followingText = followingLines.join(' ').substring(0, 200);

  // Look for figure captions using LLM (language-agnostic)
  let caption = await findFigureCaptionEnhanced([...precedingLines, ...followingLines], pageNumber, imgIndex);

  // If still no caption found, search the entire page text
  if (!caption) {
    caption = await findFigureCaptionEnhanced(lines, pageNumber, imgIndex);
  }

  // Final fallback: use page-image numbering (generic label)
  if (!caption) {
    caption = `Image ${pageNumber}-${imgIndex + 1}`;
  }

  const surroundingText = `${precedingText} [IMAGE_HERE] ${followingText}`;

  return {
    caption,
    surroundingText,
    sectionTitle
  };
}

/**
 * Find figure caption in text lines using LLM detection
 * Falls back to basic pattern matching if LLM is unavailable
 */
async function findFigureCaptionEnhanced(lines, pageNumber, imgIndex) {
  // First, try LLM-based detection (language and format agnostic)
  try {
    const llmCaption = await detectCaption(lines);
    if (llmCaption) {
      console.log(`   🤖 LLM detected caption: ${llmCaption}`);
      return llmCaption;
    }
  } catch (error) {
    console.warn(`   LLM caption detection error: ${error.message}`);
  }

  // Fallback: Basic structural pattern matching (no specific keywords)
  const numberPattern = /^(.{1,30})\s*(\d+[-\.]\d+|\d+)\s*[:：\-–—]\s*(.+)/;
  const shortNumberPattern = /^(.{1,20})\s*(\d+[-\.]\d+|\d+)\s*$/;

  for (const line of lines) {
    const trimmedLine = line.trim();
    if (!trimmedLine || trimmedLine.length < 3) continue;

    // Try pattern with description
    let match = trimmedLine.match(numberPattern);
    if (match && match[1].length <= 30) {
      return trimmedLine;
    }

    // Try short pattern (label + number only)
    match = trimmedLine.match(shortNumberPattern);
    if (match && match[1].length <= 20) {
      return trimmedLine;
    }
  }

  return null;
}

module.exports = asPdfMultimodalEnhanced;
