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
const { PDFDocument } = require("pdf-lib");
const sharp = require("sharp");
const { detectCaption, isLLMCaptionDetectionAvailable } = require("../../../utils/LLMCaptionDetector");

/**
 * PDF processor with pdf-lib image extraction
 * Extracts images using pdf-lib and saves them to disk
 */

async function asPdfMultimodal({ fullFilePath = "", filename = "", options = {} }) {
  const pdfLoader = new PDFLoader(fullFilePath, {
    splitPages: true,
  });

  // Check LLM availability for caption detection
  const llmStatus = await isLLMCaptionDetectionAvailable();
  console.log(`-- Working ${filename} (MULTIMODAL MODE - pdf-lib) --`);
  console.log(`🤖 LLM Caption Detection: ${llmStatus.available ? `Available (${llmStatus.provider})` : 'Not available - using fallback patterns'}`);
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

  console.log(`[DEBUG] About to extract images for ${filename}`);
  console.log(`[DEBUG] pageContent length: ${pageContent.length}`);

  // Extract images using pdf-lib only
  console.log(`-- Extracting images from ${filename} (pdf-lib) --`);
  const images = await extractImagesWithPdfLib(fullFilePath, filename, pageContent);
  console.log(`-- Extracted ${images.length} images --`);

  // Build content with inline image references using markdown format
  let contentWithImages = "";
  for (let i = 0; i < pageContent.length; i++) {
    contentWithImages += pageContent[i];

    // Find images for this page (i+1 because pageNumber starts at 1)
    const pageImages = images.filter(img => img.pageNumber === (i + 1));

    // Insert markdown image tags after each page's content
    if (pageImages.length > 0) {
      contentWithImages += "\n\n";
      pageImages.forEach((img, idx) => {
        // Create markdown format: ![{CAPTION} from page {PAGE}](src/extract-images/{FILENAME_DIR}/{IMAGE_FILE} "{CAPTION}")
        // Caption already contains "Figure X-X: Description" format from extractImageContext
        const caption = img.caption || `Image ${idx + 1}`;
        // Extract directory name and filename from the image metadata
        const imagePath = path.relative(
          path.join(process.env.STORAGE_DIR || path.resolve(__dirname, '../../../../frontend/src'), 'extract-images'),
          img.filePath
        );
        // Convert Windows backslashes to forward slashes for URLs
        const normalizedImagePath = imagePath.replace(/\\/g, '/');
        const markdownImg = `![${caption} from page ${img.pageNumber}](src/extract-images/${normalizedImagePath} "${caption}")\n`;
        contentWithImages += markdownImg;
      });
      contentWithImages += "\n";
    }
  }

  // Build figure caption to image file mapping
  const figureCaptionMap = {};
  images.forEach(img => {
    const caption = img.caption || '';
    // Extract figure number (e.g., "Figure 5-1" -> "5-1")
    const figureMatch = caption.match(/Figure\s+(\d+[-\.]\d+)/i);
    if (figureMatch) {
      const figureNumber = figureMatch[1];
      figureCaptionMap[figureNumber] = {
        fileName: img.fileName,
        filePath: img.filePath,
        pageNumber: img.pageNumber,
        fullCaption: caption
      };
      console.log(`📌 Mapped Figure ${figureNumber} -> ${img.fileName} (page ${img.pageNumber})`);
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
    wordCount: contentWithImages.split(" ").length,
    pageContent: contentWithImages,
    token_count_estimate: tokenizeString(contentWithImages),

    // Multimodal data - no imageBuffer stored
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

  // Generate markdown file alongside the document
  await generateMarkdownFile(filename, docs, contentWithImages, images, data);

  trashFile(fullFilePath);
  console.log(
    `[SUCCESS]: ${filename} converted & ready for multimodal embedding.\n` +
    `Text content: ${contentWithImages.length} chars, Images: ${images.length}\n`
  );

  return { success: true, reason: null, documents: [document] };
}

/**
 * Determine image file extension based on PDF filter type
 */
function getImageExtension(filterStr, colorSpaceStr) {
  // Extract filter name from PDFName string (e.g., "/DCTDecode" -> "DCTDecode")
  const filterName = filterStr.replace(/^\//, '').split(' ')[0];

  switch (filterName) {
    case 'DCTDecode':
      // DCT = Discrete Cosine Transform = JPEG (can save directly)
      return 'jpg';

    case 'JPXDecode':
      // JPX = JPEG2000 (can save directly)
      return 'jp2';

    case 'CCITTFaxDecode':
    case 'JBIG2Decode':
    case 'FlateDecode':
    case 'LZWDecode':
    case 'RunLengthDecode':
      // These formats need decoding - save as .dat for raw data
      // (conversion to standard formats would require complex decoding)
      return 'dat';

    case 'none':
      // No compression - raw image data
      return 'raw';

    default:
      // Unknown filter - save as .dat
      console.warn(`   Unknown filter type: ${filterName}, saving as .dat`);
      return 'dat';
  }
}

/**
 * Check if image data can be saved directly without decoding
 */
function canSaveDirectly(filterStr) {
  const filterName = filterStr.replace(/^\//, '').split(' ')[0];

  // These formats contain complete, standard image file data that can be saved directly
  return ['DCTDecode', 'JPXDecode'].includes(filterName);
}

/**
 * Attempt to convert raw/compressed image data to standard format using sharp
 * For images that can be saved directly (JPEG, JP2), this returns the original data
 * For others, attempts conversion to PNG
 */
async function convertImageIfNeeded(imageBytes, filterStr, imgWidth, imgHeight, colorSpaceStr, bitsPerComp) {
  const filterName = filterStr.replace(/^\//, '').split(' ')[0];

  // If it's already a standard format (JPEG, JPEG2000), return as-is
  if (canSaveDirectly(filterStr)) {
    return {
      buffer: imageBytes,
      ext: getImageExtension(filterStr, colorSpaceStr),
      converted: false
    };
  }

  // Special handling for FlateDecode (zlib-compressed raw pixel data)
  if (filterName === 'FlateDecode') {
    try {
      const zlib = require('zlib');
      const buffer = Buffer.isBuffer(imageBytes) ? imageBytes : Buffer.from(imageBytes);

      // Decompress the FlateDecode data
      const decompressed = zlib.inflateSync(buffer);

      // Determine channels based on colorspace
      const colorSpace = colorSpaceStr.replace(/^\//, '').split(' ')[0];
      let channels = 1; // Default to grayscale

      if (colorSpace === 'DeviceRGB' || colorSpace === 'RGB') {
        channels = 3;
      } else if (colorSpace === 'DeviceCMYK' || colorSpace === 'CMYK') {
        channels = 4;
      } else if (colorSpace === 'DeviceGray' || colorSpace === 'Gray') {
        channels = 1;
      }

      // Create image from raw pixel data using sharp
      const sharpInstance = sharp(decompressed, {
        raw: {
          width: imgWidth,
          height: imgHeight,
          channels: channels
        }
      });

      // Convert CMYK to RGB if needed
      if (channels === 4) {
        // For CMYK, we need to convert to RGB
        const convertedBuffer = await sharpInstance
          .toColorspace('srgb')
          .png()
          .toBuffer();
        console.log(`   ✅ Converted FlateDecode CMYK image to PNG`);
        return { buffer: convertedBuffer, ext: 'png', converted: true };
      } else {
        // For RGB or grayscale, just convert to PNG
        const convertedBuffer = await sharpInstance
          .png()
          .toBuffer();
        console.log(`   ✅ Converted FlateDecode image to PNG`);
        return { buffer: convertedBuffer, ext: 'png', converted: true };
      }
    } catch (error) {
      console.log(`   ⚠️  FlateDecode conversion failed: ${error.message}, saving as .dat`);
      const buffer = Buffer.isBuffer(imageBytes) ? imageBytes : Buffer.from(imageBytes);
      return { buffer, ext: 'dat', converted: false };
    }
  }

  // For other formats, try to use sharp to auto-detect and convert
  try {
    const buffer = Buffer.isBuffer(imageBytes) ? imageBytes : Buffer.from(imageBytes);

    // Attempt to let sharp auto-detect the format and convert to PNG
    const convertedBuffer = await sharp(buffer)
      .png()
      .toBuffer()
      .catch(() => null);

    if (convertedBuffer) {
      console.log(`   ✅ Converted ${filterName} to PNG using sharp`);
      return { buffer: convertedBuffer, ext: 'png', converted: true };
    }

    // If sharp couldn't handle it, save as .dat with the raw data
    console.log(`   ⚠️  Could not convert ${filterName}, saving as .dat`);
    return { buffer, ext: 'dat', converted: false };

  } catch (error) {
    // If conversion fails, return original data as .dat
    console.log(`   ⚠️  Conversion failed for ${filterName}: ${error.message}, saving as .dat`);
    const buffer = Buffer.isBuffer(imageBytes) ? imageBytes : Buffer.from(imageBytes);
    return { buffer, ext: 'dat', converted: false };
  }
}

/**
 * Extract images using pdf-lib and save to disk
 */
async function extractImagesWithPdfLib(pdfPath, filename, pageContent) {
  const images = [];

  try {
    // Determine base storage path
    const baseStoragePath = process.env.STORAGE_DIR
      ? path.resolve(process.env.STORAGE_DIR, 'extract-images')
      : path.resolve(__dirname, '../../../../frontend/src/extract-images');

    // Create filename-specific subdirectory
    const baseFilename = filename.replace(/\.pdf$/i, '');
    const filenameSlug = slugify(baseFilename);
    const storagePath = path.join(baseStoragePath, filenameSlug);

    // Create directory if it doesn't exist
    if (!fs.existsSync(storagePath)) {
      fs.mkdirSync(storagePath, { recursive: true });
      console.log(`📁 Created image storage directory: ${storagePath}`);
    }

    const pdfBuffer = fs.readFileSync(pdfPath);
    const pdfDoc = await PDFDocument.load(pdfBuffer);
    const pages = pdfDoc.getPages();

    console.log(`Processing ${pages.length} pages for image extraction...`);

    // Get the context for creating PDF names
    const context = pdfDoc.context;

    for (let pageIndex = 0; pageIndex < pages.length; pageIndex++) {
      const page = pages[pageIndex];
      const pageNumber = pageIndex + 1;
      const pageText = pageContent[pageIndex] || "";

      try {
        // Access the page dictionary directly
        const pageDict = page.node;

        // Create PDFName objects for the keys we need
        const { PDFName, asNumber } = require('pdf-lib');
        const resourcesKey = PDFName.of('Resources');
        const xobjectKey = PDFName.of('XObject');
        const subtypeKey = PDFName.of('Subtype');
        const imageType = PDFName.of('Image');

        // Get Resources dictionary
        const resourcesRef = pageDict.get(resourcesKey);
        if (!resourcesRef) {
          console.log(`No resources found on page ${pageNumber}`);
          continue;
        }

        // Lookup the resources dictionary
        const resources = context.lookup(resourcesRef);
        if (!resources) {
          console.log(`Could not resolve resources on page ${pageNumber}`);
          continue;
        }

        // Get XObject dictionary
        const xObjectRef = resources.get(xobjectKey);
        if (!xObjectRef) {
          console.log(`No XObjects found on page ${pageNumber}`);
          continue;
        }

        // Lookup the XObject dictionary
        const xObjects = context.lookup(xObjectRef);
        if (!xObjects) {
          console.log(`Could not resolve XObjects on page ${pageNumber}`);
          continue;
        }

        // Get all keys in the XObject dictionary
        const xObjectKeys = xObjects.entries();
        console.log(`Found ${xObjectKeys.length} XObjects on page ${pageNumber}`);

        let imgIndex = 0;
        for (const [name, xObjRef] of xObjectKeys) {
          try {
            const xObj = context.lookup(xObjRef);

            if (!xObj) {
              continue;
            }

            // XObject is likely a PDFStream, which has a dict property
            const xObjDict = xObj.dict || xObj;

            // Check if this is an image
            const subtype = xObjDict.get(subtypeKey);

            if (subtype && subtype.toString() === imageType.toString()) {
              console.log(`   Found image XObject: ${name}`);

              // Extract image properties
              const widthKey = PDFName.of('Width');
              const heightKey = PDFName.of('Height');
              const colorSpaceKey = PDFName.of('ColorSpace');
              const bitsPerComponentKey = PDFName.of('BitsPerComponent');
              const filterKey = PDFName.of('Filter');

              const width = xObjDict.get(widthKey);
              const height = xObjDict.get(heightKey);
              const colorSpace = xObjDict.get(colorSpaceKey);
              const bitsPerComponent = xObjDict.get(bitsPerComponentKey);
              const filter = xObjDict.get(filterKey);

              // Get numeric values using asNumber() helper
              const imgWidth = width ? asNumber(width) : 0;
              const imgHeight = height ? asNumber(height) : 0;

              console.log(`   Image dimensions: ${imgWidth}x${imgHeight}`);

              if (imgWidth > 0 && imgHeight > 0) {
                // Get filter info first to determine extension
                const filterStr = filter ? filter.toString() : 'none';
                const colorSpaceStr = colorSpace ? colorSpace.toString() : 'unknown';
                const bitsPerComp = bitsPerComponent ? asNumber(bitsPerComponent) : 8;

                console.log(`   Filter: ${filterStr}, ColorSpace: ${colorSpaceStr}, BitsPerComponent: ${bitsPerComp}`);

                // Detect inline vs block images
                const isInlineImage = (imgWidth < 100 && imgHeight < 100) || (imgWidth < 50 || imgHeight < 50);

                try {
                  // Extract the image stream data - xObj should be a PDFStream
                  let imageBytes;

                  // Try different methods to get the contents
                  if (typeof xObj.getContents === 'function') {
                    console.log(`   Using getContents() method`);
                    imageBytes = xObj.getContents();
                  } else if (xObj.contents) {
                    console.log(`   Using contents property`);
                    imageBytes = xObj.contents;
                  } else if (xObj.dict && xObj.dict.context) {
                    // Try to get stream contents directly
                    console.log(`   Trying to extract stream contents`);
                    const streamKey = PDFName.of('Length');
                    const length = xObjDict.get(streamKey);
                    console.log(`   Stream length: ${length}`);

                    // For PDFStream objects, we need to access the internal contents
                    if (xObj.contents !== undefined) {
                      imageBytes = xObj.contents;
                    } else {
                      throw new Error('Could not access stream contents');
                    }
                  } else {
                    throw new Error('Could not extract image data - no known method available');
                  }

                  // Convert image to standard format if needed
                  const conversionResult = await convertImageIfNeeded(
                    imageBytes,
                    filterStr,
                    imgWidth,
                    imgHeight,
                    colorSpaceStr,
                    bitsPerComp
                  );

                  const imageExt = conversionResult.ext;
                  const imageBuffer = Buffer.isBuffer(conversionResult.buffer)
                    ? conversionResult.buffer
                    : Buffer.from(conversionResult.buffer);

                  console.log(`📸 Image detected: ${imgWidth}x${imgHeight} (${isInlineImage ? 'inline' : 'block'}, format: ${imageExt}${conversionResult.converted ? ' - converted' : ''})`);

                  // Create image filename with new structure: page{N}_image{M}.{ext}
                  const imageFileName = `page${pageNumber}_image${imgIndex}.${imageExt}`;
                  const imageFilePath = path.join(storagePath, imageFileName);
                  const imageId = `${filenameSlug}_page${pageNumber}_img${imgIndex}`;

                  // Save image data
                  fs.writeFileSync(imageFilePath, imageBuffer);
                  console.log(`   ✅ Saved image to: ${imageFileName} (${imageBuffer.length} bytes)`);

                  // Extract context based on image type (async for LLM caption detection)
                  const contextInfo = await extractImageContext(pageText, pageNumber, imgIndex, isInlineImage);

                  const imageMetadata = {
                    id: imageId,
                    pageNumber,
                    fileName: imageFileName,
                    filePath: imageFilePath,
                    caption: contextInfo.caption,
                    surroundingText: contextInfo.surroundingText,
                    sectionTitle: contextInfo.sectionTitle,
                    documentName: filename,
                    extractionMethod: "pdf-lib",
                    isInline: isInlineImage,
                    format: imageExt,
                    originalFilter: filterStr,
                    converted: conversionResult.converted,
                    dimensions: { width: imgWidth, height: imgHeight },
                    colorSpace: colorSpaceStr,
                    bitsPerComponent: bitsPerComp,
                    sizeBytes: imageBuffer.length
                  };

                  images.push(imageMetadata);
                  imgIndex++;
                } catch (saveError) {
                  console.warn(`   ⚠️  Failed to save image: ${saveError.message}`);
                  console.warn(saveError.stack);
                }
              }
            }
          } catch (err) {
            console.warn(`Failed to process XObject ${name}: ${err.message}`);
            console.warn(err.stack);
          }
        }
      } catch (pageError) {
        console.warn(`Error processing page ${pageNumber}: ${pageError.message}`);
        console.warn(pageError.stack);
      }
    }

    return images;
  } catch (error) {
    console.error(`Error in pdf-lib image extraction: ${error.message}`);
    console.error(error.stack);
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
      surroundingText: "",
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
    let caption = await findFigureCaption(lines, pageNumber, imgIndex);

    return {
      caption: caption || `Image ${pageNumber}-${imgIndex + 1}`,
      surroundingText: surroundingText || "",
      sectionTitle
    };
  }

  // For block images, extract preceding and following text
  const linesPerImage = Math.max(1, Math.floor(totalLines / 4));
  const startIdx = imgIndex * linesPerImage;

  const precedingLines = lines.slice(Math.max(0, startIdx - 2), startIdx);
  const followingLines = lines.slice(startIdx, Math.min(totalLines, startIdx + 3));

  const precedingText = precedingLines.join(' ').substring(0, 200);
  const followingText = followingLines.join(' ').substring(0, 200);

  // Look for figure captions using LLM (language-agnostic)
  let caption = await findFigureCaption([...precedingLines, ...followingLines], pageNumber, imgIndex);

  // If still no caption found, search the entire page text
  if (!caption) {
    caption = await findFigureCaption(lines, pageNumber, imgIndex);
  }

  // Final fallback: use page-image numbering (generic label)
  if (!caption) {
    caption = `Image ${pageNumber}-${imgIndex + 1}`;
  }

  // Surrounding text without placeholder
  const surroundingText = `${precedingText} ${followingText}`;

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
async function findFigureCaption(lines, pageNumber, imgIndex) {
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
  // Look for lines that have number patterns typical of figure labels
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

/**
 * Generate a standalone markdown file with embedded images
 * @param {string} filename - Original PDF filename
 * @param {Array} docs - Array of document pages with metadata
 * @param {string} contentWithImages - Full content with embedded image references
 * @param {Array} images - Array of extracted image metadata
 * @param {Object} data - Document data object
 */
async function generateMarkdownFile(filename, docs, contentWithImages, images, data) {
  try {
    // Determine storage path (same as image storage - inside filename subdirectory)
    const baseStoragePath = process.env.STORAGE_DIR
      ? path.resolve(process.env.STORAGE_DIR, 'extract-images')
      : path.resolve(__dirname, '../../../../frontend/src/extract-images');

    // Create markdown filename based on PDF name
    const baseFilename = filename.replace(/\.pdf$/i, '');
    const filenameSlug = slugify(baseFilename);
    const storagePath = path.join(baseStoragePath, filenameSlug);
    const mdFilename = `${filenameSlug}.md`;
    const mdFilePath = path.join(storagePath, mdFilename);

    // Build markdown content
    let markdownContent = '';

    // Add metadata header
    markdownContent += `# ${filename}\n\n`;
    markdownContent += `---\n\n`;
    markdownContent += `**Author**: ${data.docAuthor}\n\n`;
    markdownContent += `**Title**: ${data.description}\n\n`;
    markdownContent += `**Published**: ${data.published}\n\n`;
    markdownContent += `**Pages**: ${docs.length}\n\n`;
    markdownContent += `**Images**: ${images.length}\n\n`;
    markdownContent += `**Word Count**: ${data.wordCount}\n\n`;
    markdownContent += `---\n\n`;

    // Add the full content with embedded images
    markdownContent += contentWithImages;

    // Add image reference table at the end
    if (images.length > 0) {
      markdownContent += `\n\n---\n\n## Image References\n\n`;
      markdownContent += `| Page | Image | Caption | Dimensions | Format |\n`;
      markdownContent += `|------|-------|---------|------------|--------|\n`;

      images.forEach((img, idx) => {
        const dimensions = `${img.dimensions.width}x${img.dimensions.height}`;
        const caption = img.caption || 'N/A';
        markdownContent += `| ${img.pageNumber} | ${idx + 1} | ${caption} | ${dimensions} | ${img.format} |\n`;
      });
    }

    // Write markdown file to disk
    fs.writeFileSync(mdFilePath, markdownContent, 'utf8');
    console.log(`📝 Generated markdown file: ${mdFilename}`);
    console.log(`   Path: ${mdFilePath}`);
    console.log(`   Size: ${markdownContent.length} characters`);

    return mdFilePath;
  } catch (error) {
    console.error(`Error generating markdown file: ${error.message}`);
    console.error(error.stack);
    return null;
  }
}

module.exports = asPdfMultimodal;
