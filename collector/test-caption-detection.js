/**
 * Test script for LLM-based caption detection
 */

const path = require('path');
const fs = require('fs');

// Set environment variables for testing
process.env.NODE_ENV = 'development';
process.env.COLLECTOR_MULTIMODAL_ENABLED = 'true';
process.env.OLLAMA_BASE_PATH = 'http://wpjk.inteplast.com:11434';
process.env.OLLAMA_MODEL_PREF = 'llama3.2:latest'; // , qwen2.5:14b
// llama3.1:8b

// Source PDF path
const sourcePdfPath = path.resolve(__dirname, '../(Caption-Typo) IT Daily Support of XF2025Oct.pdf');
const hotdirPath = path.resolve(__dirname, 'hotdir');
const targetPdfPath = path.join(hotdirPath, '(Caption-Typo) IT Daily Support of XF2025Oct.pdf');

async function runTest() {
  console.log('='.repeat(60));
  console.log('LLM Caption Detection Test');
  console.log('='.repeat(60));
  console.log(`Ollama URL: ${process.env.OLLAMA_BASE_PATH}`);
  console.log(`Ollama Model: ${process.env.OLLAMA_MODEL_PREF}`);
  console.log(`Source PDF: ${sourcePdfPath}`);
  console.log('='.repeat(60));

  // Check if source PDF exists
  if (!fs.existsSync(sourcePdfPath)) {
    console.error(`❌ Source PDF not found: ${sourcePdfPath}`);
    process.exit(1);
  }

  // Ensure hotdir exists
  if (!fs.existsSync(hotdirPath)) {
    fs.mkdirSync(hotdirPath, { recursive: true });
  }

  // Copy PDF to hotdir
  console.log(`\n📄 Copying PDF to hotdir...`);
  fs.copyFileSync(sourcePdfPath, targetPdfPath);
  console.log(`✅ PDF copied to: ${targetPdfPath}`);

  // Run the processor
  console.log(`\n🚀 Starting multimodal PDF processing...\n`);

  const { processSingleFile } = require('./processSingleFile');

  try {
    const result = await processSingleFile('(Caption-Typo) IT Daily Support of XF2025Oct.pdf', {});

    console.log('\n' + '='.repeat(60));
    console.log('RESULTS');
    console.log('='.repeat(60));

    if (result.success) {
      console.log('✅ Processing successful!');
      console.log(`\nDocuments created: ${result.documents.length}`);

      if (result.documents.length > 0) {
        const doc = result.documents[0];
        console.log(`\n📊 Document Info:`);
        console.log(`   - Title: ${doc?.title || 'N/A'}`);
        console.log(`   - Images: ${doc?.imageCount || 0}`);

        if (doc?.images && doc.images.length > 0) {
          console.log(`\n🖼️  Extracted Images with Captions:`);
          doc.images.forEach((img, idx) => {
            console.log(`\n   Image ${idx + 1}:`);
            console.log(`   - Caption: ${img.caption}`);
            console.log(`   - Page: ${img.pageNumber}`);
            console.log(`   - File: ${img.fileName || 'N/A'}`);
          });
        }

        if (doc?.figureCaptionMap) {
          console.log(`\n📌 Figure Caption Map:`);
          Object.entries(doc.figureCaptionMap).forEach(([key, value]) => {
            console.log(`   ${key}: ${value.fullCaption || value.fileName}`);
          });
        }
      }
    } else {
      console.log('❌ Processing failed!');
      console.log(`Reason: ${result.reason}`);
    }
  } catch (error) {
    console.error('❌ Error during processing:', error);
    console.error(error.stack);
  }
}

runTest().catch(console.error);
