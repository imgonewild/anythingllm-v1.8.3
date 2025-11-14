# PDF Image Extraction Fix & Enhancement

## Summary
Fixed critical bug preventing image extraction and enhanced the system to save images with proper file extensions (.jpg, .png, etc.) instead of generic .dat files.

## Issues Fixed

### 1. Critical Bug: PDFNumber Dimension Extraction (FIXED)
**Problem**: Image dimensions were being logged as function objects instead of numbers:
```
Image dimensions: function () { return this.numberValue; }xfunction () { return this.numberValue; }
-- Extracted 0 images --
```

**Root Cause**: Incorrect property access on PDFNumber objects returned by pdf-lib.

**Solution**: Import and use the `asNumber()` helper function from pdf-lib:
```javascript
// ❌ BROKEN
const imgWidth = width && typeof width === 'object' && 'value' in width
  ? width.value
  : (width || 0);

// ✅ FIXED
const { PDFName, asNumber } = require('pdf-lib');
const imgWidth = width ? asNumber(width) : 0;
const imgHeight = height ? asNumber(height) : 0;
const bitsPerComp = bitsPerComponent ? asNumber(bitsPerComponent) : 8;
```

### 2. Enhancement: Proper Image File Extensions (NEW)
**Problem**: All images were saved as `.dat` files regardless of actual format.

**Solution**: Implemented intelligent format detection and conversion:

#### Format Detection
Based on PDF Filter property:
- **DCTDecode** → `.jpg` (JPEG - saved directly)
- **JPXDecode** → `.jp2` (JPEG2000 - saved directly)
- **FlateDecode/LZWDecode/RunLengthDecode** → `.png` (converted via sharp) or `.dat` (if conversion fails)
- **CCITTFaxDecode/JBIG2Decode** → `.dat` (raw data)
- **Unknown/None** → `.dat` (raw data)

#### Automatic Conversion
- JPEG and JPEG2000 images are saved directly (stream data is already in standard format)
- Other compressed formats attempt conversion to PNG using the `sharp` library
- If conversion fails, saves as `.dat` with raw data

## Files Modified

**File**: `collector/processSingleFile/convert/asPDF/multimodal.js`

### Changes:
1. **Import sharp library** (line 14):
   ```javascript
   const sharp = require("sharp");
   ```

2. **Import asNumber from pdf-lib** (line 139):
   ```javascript
   const { PDFName, asNumber } = require('pdf-lib');
   ```

3. **New helper functions** (lines 103-191):
   - `getImageExtension()` - Determines proper file extension based on filter type
   - `canSaveDirectly()` - Checks if image can be saved without conversion
   - `convertImageIfNeeded()` - Attempts to convert compressed formats to standard formats

4. **Updated dimension extraction** (lines 257-258):
   ```javascript
   const imgWidth = width ? asNumber(width) : 0;
   const imgHeight = height ? asNumber(height) : 0;
   ```

5. **Updated image saving logic** (lines 344-369):
   - Calls `convertImageIfNeeded()` to get proper format and buffer
   - Saves with correct file extension
   - Logs conversion status

6. **Enhanced metadata** (lines 374-392):
   ```javascript
   {
     format: imageExt,              // Actual saved format (jpg, png, dat, etc.)
     originalFilter: filterStr,      // Original PDF filter (DCTDecode, etc.)
     converted: boolean,             // Whether conversion was performed
     ...
   }
   ```

## Usage

After this fix, images will be automatically:
1. **Extracted successfully** (asNumber bug fixed)
2. **Saved with proper extensions**:
   - JPEG images → `.jpg`
   - JPEG2000 images → `.jp2`
   - Convertible formats → `.png`
   - Others → `.dat`

### Example Output
```
Processing 1 pages for image extraction...
Found 1 XObjects on page 1
   Found image XObject: /Image7
   Image dimensions: 800x600
   Filter: /DCTDecode, ColorSpace: /DeviceRGB, BitsPerComponent: 8
📸 Image detected: 800x600 (block, format: jpg)
   ✅ Saved image to: network-layout_page1_img0_1234567890.jpg (45678 bytes)
-- Extracted 1 images --
```

## Testing

To test the fix:
1. Process a PDF with embedded images
2. Check the console output for dimension values (should be numbers, not functions)
3. Verify images are saved with proper extensions in `server/storage/extract_img/`
4. Check metadata includes `format`, `originalFilter`, and `converted` fields

## Benefits

1. ✅ **Image extraction now works** (critical bug fixed)
2. ✅ **Proper file extensions** for easier identification and use
3. ✅ **Standard formats** where possible (JPEG, PNG)
4. ✅ **Automatic conversion** for compatible compressed formats
5. ✅ **Enhanced metadata** tracking format and conversion status
6. ✅ **Graceful fallback** to .dat for unsupported formats

## Dependencies

- **pdf-lib**: Already installed (uses `asNumber()` helper)
- **sharp**: Already installed (used for image format conversion)

No additional dependencies required.
