#!/bin/bash
# Start ChromaDB server using pip installation

echo "Starting ChromaDB server on port 8000..."

# Check if chromadb is installed
if ! command -v chroma &> /dev/null; then
    echo "ChromaDB not found. Installing..."
    pip3 install chromadb
fi

# Create storage directory
mkdir -p ./server/storage/chroma

# Start ChromaDB server
echo "Starting ChromaDB server..."
echo "Data directory: $(pwd)/server/storage/chroma"
cd ./server/storage/chroma
chroma run --path . --host 0.0.0.0 --port 8000
