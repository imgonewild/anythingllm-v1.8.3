# Multimodal PDF Processing Setup

This document explains the multimodal PDF image extraction system and how to optimize it.

## Overview

The multimodal PDF processor uses a **multi-strategy approach** to extract images from PDFs:

1. **pdf-lib**: Detects embedded images (lightweight, always available)
2. **pdf2pic**: High-quality page-to-image conversion (requires GraphicsMagick)
3. **pdfjs+canvas**: Pure JavaScript fallback (always available)

## Quick Start

### ⚠️ WSL Users: Important First Step

If you're running in WSL (Windows Subsystem for Linux), rebuild canvas first:

```bash
cd collector
npm rebuild canvas

# Verify it works
node -e "require('canvas'); console.log('✅ Canvas OK')"
```

This fixes the "not a valid Win32 application" error.

### Option 1: Automatic Setup (Recommended)
```bash
cd collector
./install-multimodal.sh
```

### Option 2: Manual Installation

#### Ubuntu/Debian (WSL)
```bash
sudo apt-get update
sudo apt-get install graphicsmagick
```

#### macOS
```bash
brew install graphicsmagick
```

#### CentOS/RHEL
```bash
sudo yum install GraphicsMagick
```

#### Fedora
```bash
sudo dnf install GraphicsMagick
```

### Verify Installation
```bash
gm version
```

## How It Works

### Extraction Strategy Flow

```
PDF Upload
    ↓
Check for Embedded Images (pdf-lib)
    ↓
    ├─ Found → Extract embedded images
    └─ Not Found
        ↓
    Try pdf2pic (GraphicsMagick)
        ↓
        ├─ Success → Extract page images
        └─ Failed (GM not installed)
            ↓
        Fallback to pdfjs+canvas
            ↓
        Extract page renders
```

### Strategy Details

#### 1. pdf-lib (Embedded Image Detection)
- **Pros**: Lightweight, fast, extracts original image quality
- **Cons**: Only works for PDFs with directly embedded images
- **Always available**: Yes

#### 2. pdf2pic (GraphicsMagick)
- **Pros**: High-quality, handles complex PDFs, optimal for scanned documents
- **Cons**: Requires external dependency (GraphicsMagick)
- **Requires**: GraphicsMagick or ImageMagick installed
- **Fallback**: Automatically skips to strategy 3 if not available

#### 3. pdfjs+canvas (Pure JavaScript)
- **Pros**: No external dependencies, always works
- **Cons**: Slower than pdf2pic, larger output files
- **Always available**: Yes (uses existing canvas package)

## Performance Comparison

| Strategy | Speed | Quality | Dependencies | Availability |
|----------|-------|---------|--------------|--------------|
| pdf-lib | ⚡⚡⚡ | ⭐⭐⭐ | None | ✅ Always |
| pdf2pic | ⚡⚡ | ⭐⭐⭐⭐⭐ | GraphicsMagick | ⚠️ Optional |
| pdfjs+canvas | ⚡ | ⭐⭐⭐⭐ | canvas (installed) | ✅ Always |

## Troubleshooting

### No Images Extracted

**Symptom:**
```
-- Extracted 0 images --
```

**Diagnosis:**
1. Check if GraphicsMagick is installed:
   ```bash
   gm version
   ```

2. Check logs for fallback activation:
   ```
   pdf2pic failed. Using pdfjs+canvas fallback...
   ```

3. Verify canvas package is installed:
   ```bash
   npm list canvas
   ```

**Solutions:**

- **Best**: Install GraphicsMagick (see Quick Start above)
- **Fallback**: System should automatically use pdfjs+canvas
- **If still failing**: Check that canvas package is properly installed

### Low Image Quality

**Solution**: Install GraphicsMagick for optimal quality:
```bash
sudo apt-get install graphicsmagick  # Linux
brew install graphicsmagick           # macOS
```

### Slow Extraction

**Cause**: Using pdfjs+canvas fallback (slower than pdf2pic)

**Solution**: Install GraphicsMagick for faster extraction

### Page Size Too Large

The pdfjs+canvas strategy filters pages by size (> 50KB) to avoid blank pages.

**Adjust threshold** in `multimodal.js:281`:
```javascript
if (imageBuffer.length > 50000) {  // Change threshold here
```

## Development Notes

### File: `collector/processSingleFile/convert/asPDF/multimodal.js`

Key functions:
- `extractImagesFromPDF()`: Main orchestrator
- `extractEmbeddedImages()`: pdf-lib strategy
- `extractWithPdf2Pic()`: GraphicsMagick strategy
- `extractWithPdfJsCanvas()`: Pure JS fallback

### Testing

Test with a PDF containing images:
```bash
# Start collector
npm run dev

# Upload PDF via API or UI
# Check logs for extraction strategy used
```

### Logs to Monitor

```
Processing X pages with pdf2pic...           # Using GraphicsMagick
Processing X pages with pdfjs+canvas...      # Using fallback
Extracted X images using pdf2pic            # Success with GM
Extracted X images using pdfjs+canvas       # Success with fallback
```

## Future Improvements

- [ ] Implement actual image buffer extraction in `extractEmbeddedImages()`
- [ ] Add OCR support for extracted images
- [ ] Implement parallel page processing for faster extraction
- [ ] Add image deduplication for repeated images
- [ ] Support for additional image formats (JPEG2000, JBIG2)

## Support

If you encounter issues:

1. Check that all npm dependencies are installed: `npm install`
2. Verify canvas installation: `npm list canvas`
3. For optimal performance, install GraphicsMagick
4. Check collector logs for detailed error messages

## References

- [pdf-lib documentation](https://pdf-lib.js.org/)
- [pdf2pic documentation](https://www.npmjs.com/package/pdf2pic)
- [canvas documentation](https://www.npmjs.com/package/canvas)
- [GraphicsMagick website](http://www.graphicsmagick.org/)
