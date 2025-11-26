#!/usr/bin/env node

/**
 * Test script for multimodal asset cleanup functionality
 * Usage: node test-cleanup.js <document-path>
 * Example: node test-cleanup.js custom-documents/test-document-uuid.json
 */

const { cleanupMultimodalAssets, cleanupByDocumentPath } = require("./cleanupMultimodalAssets");
const fs = require("fs");
const path = require("path");

async function testCleanup() {
  const args = process.argv.slice(2);

  if (args.length === 0) {
    console.log("Usage: node test-cleanup.js <document-path>");
    console.log("Example: node test-cleanup.js custom-documents/test-document-uuid.json");
    process.exit(1);
  }

  const docPath = args[0];
  console.log("\n=== Testing Multimodal Asset Cleanup ===\n");
  console.log(`Document path: ${docPath}\n`);

  // Test 1: Cleanup with document data (normal flow)
  console.log("Test 1: Cleanup with existing document data");
  console.log("-".repeat(50));

  try {
    const result = await cleanupMultimodalAssets(docPath);

    console.log("\nResult:");
    console.log(`  Success: ${result.success}`);
    console.log(`  Files removed: ${result.removedFiles.length}`);

    if (result.removedFiles.length > 0) {
      console.log("\n  Removed files:");
      result.removedFiles.forEach(file => console.log(`    - ${file}`));
    }

    if (result.errors.length > 0) {
      console.log("\n  Errors:");
      result.errors.forEach(error => console.log(`    - ${error}`));
    }
  } catch (error) {
    console.error(`\n  ERROR: ${error.message}`);
  }

  // Test 2: Cleanup by path (when document is already deleted)
  console.log("\n\nTest 2: Cleanup by document path (document already deleted)");
  console.log("-".repeat(50));

  try {
    const result = await cleanupByDocumentPath(docPath);

    console.log("\nResult:");
    console.log(`  Success: ${result.success}`);
    console.log(`  Files removed: ${result.removedFiles.length}`);

    if (result.removedFiles.length > 0) {
      console.log("\n  Removed files:");
      result.removedFiles.forEach(file => console.log(`    - ${file}`));
    }

    if (result.errors.length > 0) {
      console.log("\n  Errors:");
      result.errors.forEach(error => console.log(`    - ${error}`));
    }
  } catch (error) {
    console.error(`\n  ERROR: ${error.message}`);
  }

  console.log("\n=== Test Complete ===\n");
}

// Run tests
testCleanup().catch(error => {
  console.error("Test failed:", error);
  process.exit(1);
});
