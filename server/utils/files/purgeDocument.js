const fs = require("fs");
const path = require("path");
const {
  purgeVectorCache,
  purgeSourceDocument,
  normalizePath,
  isWithin,
  documentsPath,
} = require(".");
const { Document } = require("../../models/documents");
const { Workspace } = require("../../models/workspace");
const { cleanupMultimodalAssets } = require("./cleanupMultimodalAssets");

async function purgeDocument(filename = null) {
  if (!filename || !normalizePath(filename)) return;

  // Clean up multimodal assets (images and markdown) before deleting document
  try {
    console.log(`[purgeDocument] Checking for multimodal assets to clean up for: ${filename}`);
    const cleanupResult = await cleanupMultimodalAssets(filename);
    if (cleanupResult.success && cleanupResult.removedFiles.length > 0) {
      console.log(`[purgeDocument] Cleaned up ${cleanupResult.removedFiles.length} multimodal asset(s)`);
    }
    if (cleanupResult.errors.length > 0) {
      console.warn(`[purgeDocument] Cleanup warnings: ${cleanupResult.errors.join(", ")}`);
    }
  } catch (error) {
    console.error(`[purgeDocument] Error during multimodal cleanup: ${error.message}`);
    // Continue with document deletion even if cleanup fails
  }

  await purgeVectorCache(filename);
  await purgeSourceDocument(filename);
  const workspaces = await Workspace.where();
  for (const workspace of workspaces) {
    await Document.removeDocuments(workspace, [filename]);
  }
  return;
}

/**
 * Purge a folder and all its contents. This will also remove all vector-cache files and workspace document associations
 * for the documents within the folder.
 * @notice This function is not recursive. It only purges the contents of the specified folder.
 * @notice You cannot purge the `custom-documents` folder.
 * @param {string} folderName - The name/path of the folder to purge.
 * @returns {Promise<void>}
 */
async function purgeFolder(folderName = null) {
  if (!folderName) return;
  const subFolder = normalizePath(folderName);
  const subFolderPath = path.resolve(documentsPath, subFolder);
  const validRemovableSubFolders = fs
    .readdirSync(documentsPath)
    .map((folder) => {
      // Filter out any results which are not folders or
      // are the protected custom-documents folder.
      if (folder === "custom-documents") return null;
      const subfolderPath = path.resolve(documentsPath, folder);
      if (!fs.lstatSync(subfolderPath).isDirectory()) return null;
      return folder;
    })
    .filter((subFolder) => !!subFolder);

  if (
    !validRemovableSubFolders.includes(subFolder) ||
    !fs.existsSync(subFolderPath) ||
    !isWithin(documentsPath, subFolderPath)
  )
    return;

  const filenames = fs
    .readdirSync(subFolderPath)
    .map((file) =>
      path.join(subFolderPath, file).replace(documentsPath + "/", "")
    );
  const workspaces = await Workspace.where();

  const purgePromises = [];

  // Clean up multimodal assets for each document
  for (const filename of filenames) {
    const rmMultimodalAssets = () =>
      new Promise((resolve) => {
        cleanupMultimodalAssets(filename)
          .then((result) => {
            if (result.success && result.removedFiles.length > 0) {
              console.log(`[purgeFolder] Cleaned up multimodal assets for: ${filename}`);
            }
            resolve(true);
          })
          .catch((error) => {
            console.error(`[purgeFolder] Error cleaning multimodal assets for ${filename}: ${error.message}`);
            resolve(true); // Continue even if cleanup fails
          });
      });
    purgePromises.push(rmMultimodalAssets);
  }

  // Remove associated Vector-cache files
  for (const filename of filenames) {
    const rmVectorCache = () =>
      new Promise((resolve) =>
        purgeVectorCache(filename).then(() => resolve(true))
      );
    purgePromises.push(rmVectorCache);
  }

  // Remove workspace document associations
  for (const workspace of workspaces) {
    const rmWorkspaceDoc = () =>
      new Promise((resolve) =>
        Document.removeDocuments(workspace, filenames).then(() => resolve(true))
      );
    purgePromises.push(rmWorkspaceDoc);
  }

  await Promise.all(purgePromises.flat().map((f) => f()));
  fs.rmSync(subFolderPath, { recursive: true }); // Delete target document-folder and source files.

  return;
}

module.exports = {
  purgeDocument,
  purgeFolder,
};
