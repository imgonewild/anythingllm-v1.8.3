# Figure Reference Fix

## Problem
When users asked to "show Figure 5-1", the system incorrectly returned `page5_image0` instead of finding the actual page where Figure 5-1 appears.

## Root Cause
- Figure numbers (e.g., "Figure 5-1") refer to the first figure in chapter/section 5, not page 5
- Images are saved as `page{N}_image{M}.ext` where N = page number, M = image index on that page
- No mapping existed between figure captions and image files
- Figure 5-1 could appear on any page (e.g., page 12)

## Solution Implemented

### 1. Figure Caption Mapping (collector/processSingleFile/convert/asPDF/)
**Files Modified:**
- `multimodal.js` (lines 97-113)
- `multimodal-enhanced.js` (lines 74-89)

**Changes:**
- Added `figureCaptionMap` to document metadata
- Maps figure numbers to actual image files: `"5-1" → {fileName: "page12_image0.jpg", pageNumber: 12, ...}`
- Extracted during PDF processing using regex: `/Figure\s+(\d+[-\.]\d+)/i`

**Example Mapping:**
```javascript
{
  "5-1": {
    fileName: "page12_image0.jpg",
    filePath: "/path/to/page12_image0.jpg",
    pageNumber: 12,
    fullCaption: "Figure 5-1: System Architecture"
  }
}
```

### 2. Enhanced System Prompt (server/utils/chats/index.js)
**File Modified:** `server/utils/chats/index.js` (lines 98-108)

**Changes:**
- Added explicit instructions to search by figure caption, not page number
- Instructs LLM to find "Figure 5-1" in image markdown captions
- Handles partial matches (e.g., "Figure 5" if "Figure 5-1" not found)

**Key Instruction:**
> "When users request a specific figure by number (e.g., 'show Figure 5-1'), you must find the correct image by searching for that figure number in the IMAGE CAPTIONS, NOT by page number."

## How It Works

### Before (Broken):
1. User: "show Figure 5-1"
2. System: Assumes page 5, image 0 → Returns `page5_image0.jpg`
3. **WRONG**: Figure 5-1 is actually on page 12

### After (Fixed):
1. User: "show Figure 5-1"
2. System: Searches context for markdown containing "Figure 5-1" in caption
3. Finds: `![Figure 5-1: System Architecture from page 12](src/extract-images/doc/page12_image0.jpg)`
4. **CORRECT**: Returns the actual image containing Figure 5-1

## Usage Instructions

### For Users:
1. **Re-process PDFs**: Existing PDFs must be re-uploaded to generate figure mappings
2. **Query format**: "show Figure X-Y" or "display Figure X-Y"
3. **Partial matches**: If "Figure 5-1" not found, system searches for "Figure 5"

### For Developers:
1. Figure mapping is automatic during PDF processing
2. Mapping stored in document metadata as `figureCaptionMap`
3. LLM uses markdown image captions for matching
4. No changes needed to existing code beyond this fix

## Supported Figure Caption Formats
- `Figure 5-1: Description`
- `Figure 5.1: Description`
- `Fig 5-1`
- `FIG 5-1`
- `5-1: Description` (standalone number)

## Testing
To verify the fix works:

1. Upload a PDF with numbered figures
2. Check console logs for mapping output:
   ```
   📌 Mapped Figure 5-1 -> page12_image0.jpg (page 12)
   ```
3. Ask: "show Figure 5-1"
4. Verify correct image is returned (not page5_image0)

## Migration Notes
- **Existing documents**: Must be re-processed to generate mappings
- **Backward compatible**: Old documents without mappings still work (by page number)
- **No database changes**: Mapping stored in document JSON metadata
