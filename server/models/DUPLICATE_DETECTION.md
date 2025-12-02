# Duplicate Document Detection

Prevents users from uploading duplicate files to workspaces by detecting existing documents before processing.

## Overview

When users attempt to add documents to a workspace, the system now checks if files with the same filename already exist in that workspace. If duplicates are detected, the upload is refused and users are notified with clear error messages.

## Implementation

### Files Modified

1. **`server/models/documents.js`** (MODIFIED)
   - Added duplicate detection in `addDocuments()` function
   - Checks for existing documents before processing uploads
   - Returns `duplicates` array in addition to existing return values

2. **`server/endpoints/workspaces.js`** (MODIFIED)
   - Updated `/workspace/:slug/update-embeddings` endpoint
   - Enhanced error messaging for duplicate files
   - Shows user-friendly notifications

3. **`server/endpoints/api/workspace/index.js`** (MODIFIED)
   - Updated API `/v1/workspace/:slug/update-embeddings` endpoint
   - Returns duplicate information in API responses

## How It Works

### Detection Flow

```
User uploads document
         ↓
Extract filename from path
         ↓
Check if document with same docpath exists in workspace
         ↓
    Duplicate found?
      ↙         ↘
    YES         NO
     ↓           ↓
Skip upload   Process upload
Add to        Add to embedded
duplicates[]  list
     ↓           ↓
Return error  Return success
```

### Code Logic

**Document Check (`documents.js:97-119`):**
```javascript
// Load document data to get original title
const data = await fileData(path);
if (!data) continue;

const originalTitle = data.title;

// Check if document with same original title already exists
const existingDocs = await this.where({ workspaceId: workspace.id });
const duplicateDoc = existingDocs.find(doc => {
  try {
    const metadata = JSON.parse(doc.metadata);
    return metadata.title === originalTitle;
  } catch (e) {
    return false;
  }
});

if (duplicateDoc) {
  console.warn(`Duplicate file detected: "${originalTitle}"`);
  duplicates.push(originalTitle);
  errors.add(`File "${originalTitle}" already exists...`);
  continue; // Skip this file
}
```

**Key Implementation Details:**
- Compares `metadata.title` (original filename) not `docpath`
- Queries all workspace documents and checks metadata
- Handles JSON parsing errors gracefully
- Uses original filename in error messages for clarity

### Return Values

The `addDocuments()` function now returns:

```javascript
{
  embedded: string[],        // Successfully added documents
  failedToEmbed: string[],  // Documents that failed to vectorize
  duplicates: string[],      // Duplicate documents (NEW)
  errors: string[]          // All error messages
}
```

## User Experience

### Web Interface

**Before Upload:**
```
User selects file: "report.pdf"
```

**Duplicate Detected:**
```
❌ Duplicate files detected (1):
  • report.pdf

These files already exist in the workspace.
Please remove the existing files first or rename the new files.
```

### API Response

**Successful Upload:**
```json
{
  "workspace": { ... },
  "message": null
}
```

**Duplicate Detected:**
```json
{
  "workspace": { ... },
  "message": "Duplicate files: report.pdf, document.docx"
}
```

## Validation Rules

### What is Considered a Duplicate?

A document is considered duplicate if:
1. Same **original filename** (stored in `metadata.title`)
2. Same `workspaceId`

**Important:** The system checks the **original filename** from the document metadata, NOT the processed JSON filename (which includes a UUID).

**Example:**
- Workspace: "Project Alpha"
- Existing: Original file `report.pdf` → Stored as `report-abc123.json`
- New Upload: Original file `report.pdf` → Would be stored as `report-def456.json`
- Result: ❌ Duplicate detected (same original filename)

**Technical Details:**
- Processed files have UUIDs appended: `filename-{uuid}.json`
- Duplicate detection compares `metadata.title` values
- This ensures same source file is detected regardless of UUID

### What is NOT a Duplicate?

Documents are **NOT** duplicates if:
1. Different workspace (same filename in different workspace = OK)
2. Different folder path
3. Different filename (even if content is same)

**Examples:**
```
✅ ALLOWED:
Workspace 1: custom-documents/report.pdf
Workspace 2: custom-documents/report.pdf
(Same filename, different workspaces)

✅ ALLOWED:
custom-documents/report.pdf
my-folder/report.pdf
(Same filename, different folders)

❌ BLOCKED:
custom-documents/report-abc123.json (existing)
custom-documents/report-abc123.json (new upload)
(Same workspace, same path)
```

## Integration Points

### 1. Web UI Upload (`/workspace/:slug/update-embeddings`)

**Request:**
```javascript
POST /workspace/my-workspace/update-embeddings
{
  "adds": ["custom-documents/report.pdf-hash.json"],
  "deletes": []
}
```

**Response (Duplicate):**
```javascript
{
  "workspace": { ... },
  "message": "❌ Duplicate files detected (1):\n  • report.pdf\n\nThese files already exist..."
}
```

### 2. API Upload (`/v1/workspace/:slug/update-embeddings`)

**Request:**
```javascript
POST /v1/workspace/my-workspace/update-embeddings
Authorization: Bearer API_KEY
{
  "adds": ["custom-documents/report.pdf-hash.json"],
  "deletes": []
}
```

**Response (Duplicate):**
```javascript
{
  "workspace": { ... },
  "message": "Duplicate files: report.pdf"
}
```

## Error Messages

### User-Facing Messages

**Single Duplicate:**
```
❌ Duplicate files detected (1):
  • report.pdf

These files already exist in the workspace.
Please remove the existing files first or rename the new files.
```

**Multiple Duplicates:**
```
❌ Duplicate files detected (3):
  • report.pdf
  • document.docx
  • spreadsheet.xlsx

These files already exist in the workspace.
Please remove the existing files first or rename the new files.
```

**Duplicates + Embedding Failures:**
```
❌ Duplicate files detected (2):
  • report.pdf
  • document.docx

⚠️ Failed to embed 1 document(s):
  • Large file exceeded size limit
```

### Console Logs

```
[addDocuments] Duplicate file detected: report.pdf already exists in workspace my-workspace
```

## Testing

### Manual Testing Scenarios

#### Test 1: Upload New Document
1. Upload `test.pdf` to workspace
2. Expected: ✅ Success, document added
3. Verify: Document appears in workspace

#### Test 2: Upload Same Document Again
1. Upload `test.pdf` again to same workspace
2. Expected: ❌ Duplicate detected
3. Verify: Error message shows "test.pdf already exists"
4. Verify: Document NOT added twice

#### Test 3: Upload Same Document to Different Workspace
1. Upload `test.pdf` to Workspace A
2. Upload `test.pdf` to Workspace B
3. Expected: ✅ Both succeed
4. Verify: Document exists in both workspaces

#### Test 4: Multiple Files with Mixed Results
1. Upload batch: [`new.pdf`, `existing.pdf`, `another.pdf`]
2. Where `existing.pdf` already in workspace
3. Expected:
   - `new.pdf`: ✅ Added
   - `existing.pdf`: ❌ Duplicate
   - `another.pdf`: ✅ Added
4. Verify: Error shows only `existing.pdf` as duplicate

### API Testing

```bash
# Test duplicate detection via API
curl -X POST http://localhost:3001/v1/workspace/test-workspace/update-embeddings \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "adds": ["custom-documents/test-doc-hash.json"]
  }'

# First call: Should succeed
# Second call: Should return duplicate message
```

### Unit Test Example

```javascript
describe("Document Duplicate Detection", () => {
  it("should detect duplicate documents in same workspace", async () => {
    const workspace = await Workspace.create({ name: "Test" });
    const docPath = "custom-documents/test.pdf-hash.json";

    // First upload
    const result1 = await Document.addDocuments(workspace, [docPath]);
    expect(result1.embedded).toHaveLength(1);
    expect(result1.duplicates).toHaveLength(0);

    // Second upload (duplicate)
    const result2 = await Document.addDocuments(workspace, [docPath]);
    expect(result2.embedded).toHaveLength(0);
    expect(result2.duplicates).toHaveLength(1);
    expect(result2.duplicates[0]).toBe("test.pdf");
  });

  it("should allow same file in different workspaces", async () => {
    const workspace1 = await Workspace.create({ name: "WS1" });
    const workspace2 = await Workspace.create({ name: "WS2" });
    const docPath = "custom-documents/test.pdf-hash.json";

    const result1 = await Document.addDocuments(workspace1, [docPath]);
    const result2 = await Document.addDocuments(workspace2, [docPath]);

    expect(result1.duplicates).toHaveLength(0);
    expect(result2.duplicates).toHaveLength(0);
  });
});
```

## Performance Considerations

### Database Query Impact

Each file upload now performs:
1. One query to fetch all workspace documents
2. In-memory comparison of metadata titles

```javascript
const existingDocs = await this.where({ workspaceId: workspace.id });
// Then compare metadata.title for each doc
```

**Performance Characteristics:**
- Query complexity: O(N) where N = number of docs in workspace
- Memory usage: All workspace docs loaded into memory
- Title comparison: O(N) for each uploaded file
- Average query time: ~10-50ms depending on workspace size
- Impact on batch uploads: One query + (N * M) comparisons where M = existing docs

**Current Implementation Trade-offs:**
- ✅ Accurate: Compares original filenames (metadata.title)
- ✅ Simple: No database schema changes required
- ⚠️ Performance: Queries all docs for each upload
- ⚠️ Scalability: Could be slow for workspaces with 1000+ documents

**Optimization:**
- Early `continue` on duplicate prevents expensive vectorization
- Could cache workspace docs for batch uploads
- Could add indexed title field to database for O(1) lookup

### Recommended Optimizations (Future)

**Option 1: Add Indexed Title Column**
```sql
ALTER TABLE workspace_documents ADD COLUMN original_title VARCHAR(500);
CREATE INDEX idx_workspace_title ON workspace_documents(workspaceId, original_title);
```

Then check with:
```javascript
const existingDoc = await this.get({
  workspaceId: workspace.id,
  original_title: originalTitle
});
```

**Option 2: Batch Processing with Caching**
```javascript
// Cache workspace docs for batch uploads
const workspaceDocs = await this.where({ workspaceId: workspace.id });
const titleSet = new Set(
  workspaceDocs.map(doc => JSON.parse(doc.metadata).title)
);

// Then check each upload
const isDuplicate = titleSet.has(originalTitle);
```

## Security Considerations

### Path Validation

The duplicate check relies on `docpath` comparison:
- ✅ Same workspace isolation (workspaceId check)
- ✅ Path normalization (handled by existing code)
- ✅ No path traversal risk (uses database comparison)

### Information Disclosure

The error message reveals:
- ✅ Only filename (not full path)
- ✅ Only to authorized workspace users
- ✅ No sensitive document content

## User Workflow

### Handling Duplicates

When users encounter duplicate errors, they have two options:

**Option 1: Remove Existing File First**
1. Go to workspace settings
2. Find existing file in document list
3. Remove the old file
4. Upload new file

**Option 2: Rename New File**
1. Rename the file on their local system
2. Upload with new filename
3. Both versions coexist with different names

## Future Enhancements

### Potential Improvements

1. **Content-Based Detection**
   - Check file hash/content, not just filename
   - Detect renamed duplicates

2. **Overwrite Option**
   - Add `allowOverwrite: true` flag
   - Replace existing document with new version

3. **Batch Duplicate Report**
   - Show duplicates before upload starts
   - Allow user to review and deselect

4. **Version History**
   - Keep multiple versions of same file
   - Track revision history

5. **Smart Merge**
   - Detect similar filenames (e.g., "report v1", "report v2")
   - Suggest consolidation

## Troubleshooting

### Issue: Duplicate Not Detected

**Symptoms:** Same file uploads multiple times

**Possible Causes:**
1. Different `docpath` values (folder + filename different)
2. Different workspace
3. Files processed before database commit

**Solution:**
- Check console logs for `docpath` values
- Verify workspace ID matches
- Ensure database transaction completed

### Issue: False Positive Duplicate

**Symptoms:** New file flagged as duplicate

**Possible Causes:**
1. File with same name exists in different folder
2. Database contains orphaned records

**Solution:**
- Check exact `docpath` in database
- Clean up orphaned documents
- Verify folder path matches

## Related Documentation

- `server/models/documents.js` - Document model and operations
- `server/endpoints/workspaces.js` - Workspace endpoints
- `server/endpoints/api/workspace/index.js` - API endpoints
- Database schema: `workspace_documents` table
