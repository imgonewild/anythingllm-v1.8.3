# Troubleshooting Guide - Multimodal PDF Processing

## Common Issues and Solutions

### Issue 1: "document is not defined" (PDF.js Error) ✅ FIXED

**Error Message:**
```
ReferenceError: document is not defined
    at FontLoader.fontLoaderInsertRule
```

**Root Cause:**
The bundled pdf.js in pdf-parse was trying to use browser APIs in Node.js environment.

**Solution:**
✅ **Already Fixed** - The system now uses standalone `pdfjs-dist` package configured for Node.js.

**Verification:**
The error should no longer occur. System now processes PDFs without crashing.

---

### Issue 2: "canvas.node is not a valid Win32 application"

**Error Message:**
```
pdfjs+canvas extraction failed: canvas.node is not a valid Win32 application
```

**Root Cause:**
The `canvas` package was installed/compiled for Windows but you're running in WSL (Linux environment), or it was built for a different Node.js version.

**Solution:**
✅ **Already Handled** - The system now gracefully handles missing canvas and continues processing.

**Optional Enhancement (for full page rendering):**
Canvas is only needed for Strategy 3 (fallback). To enable it:

```bash
# 1. Install system dependencies first
sudo apt-get update
sudo apt-get install -y build-essential libcairo2-dev libpango1.0-dev libjpeg-dev libgif-dev librsvg2-dev pkg-config

# 2. Then rebuild canvas
cd collector
npm rebuild canvas
```

**Verification:**
```bash
node -e "const canvas = require('canvas'); console.log('Canvas version:', canvas.version);"
```

Should output:
```
Canvas loaded successfully!
Canvas version: 3.2.0
```

---

### Issue 3: Canvas Build Dependencies Missing

**Error Message:**
```
node-gyp rebuild errors
Package cairo was not found
```

**Solution:**
Install required system dependencies:

```bash
# Ubuntu/Debian (WSL)
sudo apt-get update
sudo apt-get install -y build-essential libcairo2-dev libpango1.0-dev libjpeg-dev libgif-dev librsvg2-dev

# Then rebuild
npm rebuild canvas
```

---

### Issue 4: GraphicsMagick Not Found

**Error Message:**
```
pdf2pic failed. Using pdfjs+canvas fallback...
```

**Behavior:**
System automatically falls back to pure JavaScript extraction (this is normal and expected).

**For Optimal Performance:**
Install GraphicsMagick (optional):

```bash
sudo apt-get install graphicsmagick

# Verify
gm version
```

---

### Issue 5: No Images Extracted (0 images)

**Diagnosis Steps:**

1. **Check if fallback is working:**
   ```
   Look for logs:
   - "Processing X pages with pdfjs+canvas..."
   - "Extracted X images using pdfjs+canvas"
   ```

2. **Check canvas installation:**
   ```bash
   npm list canvas
   node -e "require('canvas')"
   ```

3. **Check PDF has visual content:**
   - Text-only PDFs may not have extractable images
   - Blank pages are filtered out (< 50KB)

**Solutions:**
- Rebuild canvas: `npm rebuild canvas`
- Install GraphicsMagick for better detection
- Verify PDF actually contains images/graphics

---

### Issue 6: WSL Path Issues

**Symptoms:**
```
Error: ENOENT: no such file or directory
Windows paths (C:\) not working
```

**Solution:**
Ensure you're using WSL paths:
- ✅ `/mnt/c/Git-Projects/...`
- ❌ `C:\Git-Projects\...`

**Verify current directory:**
```bash
pwd  # Should show /mnt/c/...
```

---

### Issue 7: Node Version Mismatch

**Canvas requires Node.js >= 18.x**

**Check version:**
```bash
node --version
```

**Update if needed:**
```bash
# Using nvm (recommended)
nvm install 18
nvm use 18

# Or update via apt
sudo apt-get update
sudo apt-get install nodejs
```

---

## Recent Fixes (2025-11-05)

### ✅ Fixed: PDF.js Browser API Error
- **Problem**: `document is not defined` error crashing the collector
- **Solution**: Migrated from bundled pdf-parse pdf.js to standalone `pdfjs-dist`
- **Impact**: PDF processing now works without crashes

### ✅ Improved: Canvas Error Handling
- **Problem**: Canvas errors would crash the entire process
- **Solution**: Graceful error handling - system continues without canvas
- **Impact**: PDFs can be processed even without canvas installed

### 📦 New Dependency
- Added `pdfjs-dist@^2.16.105` for better Node.js compatibility

---

## Extraction Strategy Flow

### Expected Log Sequence

**Scenario 1: GraphicsMagick Installed (Optimal)**
```
-- Extracting images from document.pdf --
No embedded images found. Trying page rendering strategies...
Processing 3 pages with pdf2pic...
Extracted 3 images using pdf2pic
-- Extracted 3 images --
```

**Scenario 2: GraphicsMagick Not Installed (Fallback)**
```
-- Extracting images from document.pdf --
No embedded images found. Trying page rendering strategies...
Processing 3 pages with pdf2pic...
pdf2pic failed. Using pdfjs+canvas fallback...
Processing 3 pages with pdfjs+canvas...
Extracted 3 images using pdfjs+canvas
-- Extracted 3 images --
```

**Scenario 3: Embedded Images (Fast Path)**
```
-- Extracting images from document.pdf --
Found 4 embedded images using pdf-lib
-- Extracted 4 images --
```

---

## Quick Diagnostic Script

Create `test-extraction.js`:

```javascript
const { createCanvas } = require('canvas');
const fs = require('fs');

async function test() {
  console.log('✓ Canvas module loads');

  const canvas = createCanvas(100, 100);
  const ctx = canvas.getContext('2d');

  console.log('✓ Canvas context created');

  ctx.fillStyle = 'red';
  ctx.fillRect(0, 0, 100, 100);

  console.log('✓ Canvas drawing works');

  const buffer = canvas.toBuffer('image/png');
  console.log(`✓ Canvas to buffer: ${buffer.length} bytes`);

  console.log('\n✅ All canvas tests passed!');
}

test().catch(err => {
  console.error('❌ Test failed:', err.message);
  process.exit(1);
});
```

Run:
```bash
node test-extraction.js
```

---

## Performance Tips

### Optimal Setup (Fastest)
```bash
# Install GraphicsMagick
sudo apt-get install graphicsmagick

# Verify
gm version
```

Expected extraction times:
- pdf2pic (with GM): ~0.5-1s per page
- pdfjs+canvas: ~1-2s per page

### Memory Considerations

Large PDFs with many pages may require increased memory:

```bash
# Increase Node.js memory limit
NODE_OPTIONS=--max-old-space-size=4096 npm run dev
```

---

## When to Use Each Strategy

### pdf-lib (Embedded Images)
- ✅ Fast and lightweight
- ✅ Original image quality
- ❌ Limited to directly embedded images
- **Use for**: Modern PDFs with embedded images

### pdf2pic (GraphicsMagick)
- ✅ High quality
- ✅ Handles complex PDFs
- ❌ Requires external dependency
- **Use for**: Scanned documents, complex layouts

### pdfjs+canvas (Pure JavaScript)
- ✅ Always available (no external deps)
- ✅ Handles all PDFs
- ❌ Slower than pdf2pic
- **Use for**: Fallback when GraphicsMagick unavailable

---

## Environment-Specific Notes

### WSL2 (Windows Subsystem for Linux)
- ✅ Recommended environment
- ⚠️ Must rebuild canvas after npm install
- ⚠️ Use WSL paths (/mnt/c/...), not Windows paths

### Native Linux
- ✅ Best performance
- ✅ Canvas builds automatically
- ✅ Easy GraphicsMagick installation

### Docker
- ⚠️ Include GraphicsMagick in Dockerfile
- ⚠️ Ensure build dependencies available

```dockerfile
RUN apt-get update && apt-get install -y \
    build-essential \
    libcairo2-dev \
    libpango1.0-dev \
    libjpeg-dev \
    libgif-dev \
    librsvg2-dev \
    graphicsmagick
```

---

## Getting Help

If issues persist:

1. **Check logs** in collector console
2. **Run diagnostics**: `node test-extraction.js`
3. **Verify environment**: `node --version`, `npm list canvas`
4. **Test canvas**: `node -e "require('canvas')"`
5. **Check dependencies**: `dpkg -l | grep -E "libcairo|libpango"`

## Related Files

- `collector/processSingleFile/convert/asPDF/multimodal.js` - Main extraction logic
- `collector/MULTIMODAL_SETUP.md` - Setup and installation guide
- `collector/install-multimodal.sh` - Automated setup script
