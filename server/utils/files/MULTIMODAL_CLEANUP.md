# Multimodal Asset Cleanup

Automatic cleanup of images and markdown files when documents are deleted from AnythingLLM workspaces.

## Overview

When PDF documents with embedded images (multimodal documents) are deleted from a workspace, this feature automatically removes the associated image files and markdown documents from the `/frontend/src/extract-images/` directory.

## Architecture

### Files Modified

1. **`server/utils/files/cleanupMultimodalAssets.js`** (NEW)
   - Core cleanup functionality
   - Handles both document-based and path-based cleanup
   - Safe error handling to prevent blocking document deletion

2. **`server/utils/files/purgeDocument.js`** (MODIFIED)
   - Integrated cleanup into `purgeDocument()` function
   - Integrated cleanup into `purgeFolder()` function
   - Cleanup runs before document deletion

3. **`server/models/documents.js`** (MODIFIED)
   - Integrated cleanup into `removeDocuments()` function
   - Ensures cleanup when documents are removed from workspace

### Cleanup Flow

```
Document Deletion Request
         ↓
    Check if multimodal
         ↓
Extract images directory from metadata
         ↓
    Remove all files in directory
         ↓
    Remove directory itself
         ↓
Continue with normal deletion
```

## Directory Structure

### Before Implementation
```
/frontend/src/extract-images/
  ├── document1_page1_img0_timestamp.png
  ├── document1_page1_img1_timestamp.jpg
  ├── document1.md
  ├── document2_page1_img0_timestamp.png
  └── ...
```

### After Implementation (With New Structure)
```
/frontend/src/extract-images/
  ├── document1/
  │   ├── page1_image0.png
  │   ├── page1_image1.jpg
  │   └── document1.md
  └── document2/
      ├── page1_image0.png
      └── document2.md
```

When a document is deleted, the entire subdirectory (e.g., `document1/`) is removed.

## Functions

### `cleanupMultimodalAssets(docPath, documentData)`

Main cleanup function that removes multimodal assets.

**Parameters:**
- `docPath` (string): Path to document JSON file relative to documents folder
- `documentData` (object, optional): Pre-parsed document data

**Returns:**
```javascript
{
  success: boolean,
  removedFiles: string[],  // Array of removed file paths
  errors: string[]         // Array of error messages
}
```

**Usage:**
```javascript
const { cleanupMultimodalAssets } = require("./cleanupMultimodalAssets");

const result = await cleanupMultimodalAssets("custom-documents/doc-uuid.json");
console.log(`Removed ${result.removedFiles.length} files`);
```

### `cleanupByDocumentPath(docPath)`

Fallback cleanup when document JSON is already deleted. Infers the image directory from the document filename.

**Parameters:**
- `docPath` (string): Path to document (e.g., "custom-documents/filename-uuid.json")

**Returns:** Same as `cleanupMultimodalAssets`

**Usage:**
```javascript
const { cleanupByDocumentPath } = require("./cleanupMultimodalAssets");

// Document is already deleted, but cleanup images
const result = await cleanupByDocumentPath("custom-documents/report-abc123.json");
```

### `extractImagesDirectory(documentData)`

Utility function to extract the images directory path from document metadata.

**Parameters:**
- `documentData` (object): Parsed document JSON data

**Returns:**
- `string`: Directory path containing images
- `null`: If not a multimodal document or no images found

## Integration Points

The cleanup is automatically triggered at three integration points:

### 1. Single Document Deletion (`purgeDocument`)

```javascript
// server/utils/files/purgeDocument.js
await cleanupMultimodalAssets(filename);
await purgeVectorCache(filename);
await purgeSourceDocument(filename);
```

### 2. Folder Deletion (`purgeFolder`)

```javascript
// server/utils/files/purgeDocument.js
for (const filename of filenames) {
  await cleanupMultimodalAssets(filename);
}
```

### 3. Workspace Document Removal (`Document.removeDocuments`)

```javascript
// server/models/documents.js
for (const path of removals) {
  await cleanupMultimodalAssets(path);
  await VectorDb.deleteDocumentFromNamespace(...);
}
```

## Error Handling

The cleanup function is designed to fail gracefully:

1. **Document Already Deleted**: Falls back to `cleanupByDocumentPath()`
2. **Directory Not Found**: Returns success with empty `removedFiles`
3. **File Removal Errors**: Logs errors but continues processing other files
4. **Cleanup Failure**: Document deletion continues even if cleanup fails

```javascript
try {
  const result = await cleanupMultimodalAssets(filename);
  if (result.errors.length > 0) {
    console.warn("Cleanup warnings:", result.errors);
  }
} catch (error) {
  console.error("Cleanup error:", error.message);
  // Continue with document deletion
}
```

## Testing

### Manual Testing

Use the provided test script:

```bash
cd server/utils/files
node test-cleanup.js custom-documents/your-document-uuid.json
```

### Test Scenarios

1. **Normal Deletion**: Document exists, has images, cleanup succeeds
2. **Document Already Deleted**: JSON missing, falls back to path-based cleanup
3. **Non-Multimodal Document**: No images, returns success immediately
4. **Missing Images Directory**: Directory doesn't exist, no-op success
5. **Partial Failure**: Some files fail to delete, logs errors but continues

### Expected Output

```
=== Testing Multimodal Asset Cleanup ===

Document path: custom-documents/test-document-uuid.json

Test 1: Cleanup with existing document data
--------------------------------------------------
Cleaning up multimodal assets in: /path/to/frontend/src/extract-images/test-document

Result:
  Success: true
  Files removed: 5

  Removed files:
    - /path/to/frontend/src/extract-images/test-document/page1_image0.png
    - /path/to/frontend/src/extract-images/test-document/page2_image0.jpg
    - /path/to/frontend/src/extract-images/test-document/test-document.md
    - /path/to/frontend/src/extract-images/test-document

=== Test Complete ===
```

## Logging

The cleanup function provides detailed logging:

- `[purgeDocument]` - Logs from single document purge
- `[purgeFolder]` - Logs from folder purge
- `[removeDocuments]` - Logs from workspace removal

Example logs:
```
[purgeDocument] Checking for multimodal assets to clean up for: custom-documents/doc.json
Cleaning up multimodal assets in: /frontend/src/extract-images/doc-name
   ✅ Removed: /frontend/src/extract-images/doc-name/page1_image0.png
   ✅ Removed directory: /frontend/src/extract-images/doc-name
[purgeDocument] Cleaned up 3 multimodal asset(s)
```

## Security Considerations

1. **Path Traversal Protection**: All paths are validated against base directories
2. **Sandboxed Operations**: Only files within `/extract-images/` are affected
3. **No Recursive Deletion**: Only removes specified directory, not parent paths
4. **Error Isolation**: Cleanup failures don't prevent document deletion

## Performance

- **Synchronous File Operations**: Uses `fs.unlinkSync` for reliability
- **Parallel Cleanup**: Multiple documents cleaned in parallel via Promise.all
- **Minimal Overhead**: Quick no-op for non-multimodal documents
- **No Database Queries**: Uses document metadata, no additional DB calls

## Maintenance

### Adding New Asset Types

To clean up additional asset types beyond images and markdown:

```javascript
// In cleanupMultimodalAssets.js
const files = fs.readdirSync(imagesDir);
const allowedExtensions = ['.png', '.jpg', '.jpeg', '.gif', '.md', '.json'];

for (const file of files) {
  const ext = path.extname(file).toLowerCase();
  if (allowedExtensions.includes(ext)) {
    // Remove file
  }
}
```

### Debugging

Enable verbose logging:

```javascript
// Set environment variable
DEBUG=cleanup:* node server.js

// Or add to cleanupMultimodalAssets.js
const DEBUG = process.env.DEBUG?.includes('cleanup');
if (DEBUG) console.log('[DEBUG]', message);
```

## Future Enhancements

1. **Cleanup Statistics**: Track total space reclaimed
2. **Orphan Detection**: Find and clean orphaned image directories
3. **Async Operations**: Use async file operations for large cleanups
4. **Soft Delete**: Move to trash instead of immediate deletion
5. **Cleanup Scheduling**: Background job to clean orphaned assets

## Migration

For existing installations with old directory structure:

```javascript
// Migration script (to be created if needed)
const oldFormat = /.*_page\d+_img\d+_\d+\.(png|jpg|jpeg)/;
// Move old-format images to new subdirectories
```

## Related Documentation

- `collector/processSingleFile/convert/asPDF/multimodal.js` - Image extraction
- `server/utils/files/purgeDocument.js` - Document purging
- `server/models/documents.js` - Document model
- `frontend/src/utils/chat/markdown.js` - Image rendering
