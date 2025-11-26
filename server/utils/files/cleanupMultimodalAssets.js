const fs = require("fs");
const path = require("path");

/**
 * Extract images directory path from document metadata
 * Documents store image filePaths in their metadata.images array
 * @param {Object} documentData - Parsed document JSON data
 * @returns {string|null} - Directory path containing images, or null if not found
 */
function extractImagesDirectory(documentData) {
  try {
    // Check if document has multimodal images
    if (!documentData.isMultimodal || !documentData.images || documentData.images.length === 0) {
      return null;
    }

    // Get the first image's filePath to determine the directory
    const firstImage = documentData.images[0];
    if (!firstImage.filePath) {
      return null;
    }

    // Extract the parent directory from the filePath
    const imageDir = path.dirname(firstImage.filePath);
    return imageDir;
  } catch (error) {
    console.error(`Error extracting images directory: ${error.message}`);
    return null;
  }
}

/**
 * Clean up multimodal assets (images and markdown) associated with a document
 * @param {string} docPath - Path to the document JSON file (relative to documents folder)
 * @param {Object} documentData - Optional: Already-parsed document data (to avoid re-reading)
 * @returns {Promise<{success: boolean, removedFiles: string[], errors: string[]}>}
 */
async function cleanupMultimodalAssets(docPath, documentData = null) {
  const removedFiles = [];
  const errors = [];

  try {
    // If document data not provided, try to load it
    if (!documentData) {
      const documentsPath = process.env.NODE_ENV === "development"
        ? path.resolve(__dirname, `../../storage/documents`)
        : path.resolve(process.env.STORAGE_DIR, `documents`);

      const fullDocPath = path.resolve(documentsPath, docPath);

      // Document might already be deleted, so we can't read it
      // In this case, we'll try to infer the cleanup path from the docPath
      if (!fs.existsSync(fullDocPath)) {
        console.log(`Document ${docPath} already deleted, attempting cleanup based on filename`);
        const cleanupResult = await cleanupByDocumentPath(docPath);
        return cleanupResult;
      }

      const fileContent = fs.readFileSync(fullDocPath, "utf8");
      documentData = JSON.parse(fileContent);
    }

    // Check if this is a multimodal document
    if (!documentData.isMultimodal || !documentData.images || documentData.images.length === 0) {
      console.log(`Document ${docPath} is not multimodal or has no images, skipping cleanup`);
      return { success: true, removedFiles: [], errors: [] };
    }

    // Extract the images directory
    const imagesDir = extractImagesDirectory(documentData);
    if (!imagesDir) {
      errors.push("Could not determine images directory from document metadata");
      return { success: false, removedFiles, errors };
    }

    console.log(`Cleaning up multimodal assets in: ${imagesDir}`);

    // Check if directory exists
    if (!fs.existsSync(imagesDir)) {
      console.log(`Images directory ${imagesDir} does not exist, nothing to clean up`);
      return { success: true, removedFiles: [], errors: [] };
    }

    // Remove all files in the directory (images and markdown)
    const files = fs.readdirSync(imagesDir);
    for (const file of files) {
      const filePath = path.join(imagesDir, file);
      try {
        fs.unlinkSync(filePath);
        removedFiles.push(filePath);
        console.log(`   ✅ Removed: ${filePath}`);
      } catch (error) {
        const errorMsg = `Failed to remove ${filePath}: ${error.message}`;
        console.error(`   ❌ ${errorMsg}`);
        errors.push(errorMsg);
      }
    }

    // Remove the directory itself
    try {
      fs.rmdirSync(imagesDir);
      removedFiles.push(imagesDir);
      console.log(`   ✅ Removed directory: ${imagesDir}`);
    } catch (error) {
      const errorMsg = `Failed to remove directory ${imagesDir}: ${error.message}`;
      console.error(`   ❌ ${errorMsg}`);
      errors.push(errorMsg);
    }

    return {
      success: errors.length === 0,
      removedFiles,
      errors
    };

  } catch (error) {
    console.error(`Error in cleanupMultimodalAssets: ${error.message}`);
    errors.push(error.message);
    return { success: false, removedFiles, errors };
  }
}

/**
 * Cleanup based on document path when document JSON is already deleted
 * Infers the image directory from the document filename
 * @param {string} docPath - Path to the document (e.g., "custom-documents/filename-uuid.json")
 * @returns {Promise<{success: boolean, removedFiles: string[], errors: string[]}>}
 */
async function cleanupByDocumentPath(docPath) {
  const removedFiles = [];
  const errors = [];

  try {
    // Extract filename from docPath (e.g., "custom-documents/filename-uuid.json" -> "filename-uuid")
    const basename = path.basename(docPath, ".json");

    // Try to extract the original filename (remove UUID suffix)
    // Format is typically: {slugified-filename}-{uuid}
    // We need to reconstruct the slugified filename
    const parts = basename.split("-");
    if (parts.length < 2) {
      errors.push(`Cannot infer original filename from: ${basename}`);
      return { success: false, removedFiles, errors };
    }

    // Remove the last part (UUID) and reconstruct the filename
    const uuidPattern = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;
    let filenameSlug = basename;

    // If last part looks like a UUID, remove it
    const lastPart = parts[parts.length - 1];
    if (uuidPattern.test(lastPart)) {
      filenameSlug = parts.slice(0, -1).join("-");
    }

    // Determine the extract-images path
    const extractImagesBasePath = process.env.NODE_ENV === "development"
      ? path.resolve(__dirname, `../../../frontend/src/extract-images`)
      : path.resolve(process.env.STORAGE_DIR || __dirname, `../../../frontend/src/extract-images`);

    const imagesDir = path.join(extractImagesBasePath, filenameSlug);

    console.log(`Attempting cleanup for inferred directory: ${imagesDir}`);

    // Check if directory exists
    if (!fs.existsSync(imagesDir)) {
      console.log(`Inferred directory ${imagesDir} does not exist, nothing to clean up`);
      return { success: true, removedFiles: [], errors: [] };
    }

    // Remove all files in the directory
    const files = fs.readdirSync(imagesDir);
    for (const file of files) {
      const filePath = path.join(imagesDir, file);
      try {
        fs.unlinkSync(filePath);
        removedFiles.push(filePath);
        console.log(`   ✅ Removed: ${filePath}`);
      } catch (error) {
        const errorMsg = `Failed to remove ${filePath}: ${error.message}`;
        console.error(`   ❌ ${errorMsg}`);
        errors.push(errorMsg);
      }
    }

    // Remove the directory itself
    try {
      fs.rmdirSync(imagesDir);
      removedFiles.push(imagesDir);
      console.log(`   ✅ Removed directory: ${imagesDir}`);
    } catch (error) {
      const errorMsg = `Failed to remove directory ${imagesDir}: ${error.message}`;
      console.error(`   ❌ ${errorMsg}`);
      errors.push(errorMsg);
    }

    return {
      success: errors.length === 0,
      removedFiles,
      errors
    };

  } catch (error) {
    console.error(`Error in cleanupByDocumentPath: ${error.message}`);
    errors.push(error.message);
    return { success: false, removedFiles, errors };
  }
}

module.exports = {
  cleanupMultimodalAssets,
  cleanupByDocumentPath,
  extractImagesDirectory
};
