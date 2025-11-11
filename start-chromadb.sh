#!/bin/bash
# Start ChromaDB server for AnythingLLM development

echo "Starting ChromaDB server on port 8000..."
echo "Data will be persisted in: ./server/storage/chroma"

# Create storage directory if it doesn't exist
mkdir -p ./server/storage/chroma

# Run ChromaDB in Docker
docker run -d \
  --name chromadb \
  -p 8000:8000 \
  -v "$(pwd)/server/storage/chroma:/chroma/chroma" \
  -e IS_PERSISTENT=TRUE \
  -e ANONYMIZED_TELEMETRY=FALSE \
  chromadb/chroma:latest

echo ""
echo "✅ ChromaDB server started!"
echo "   - Server: http://localhost:8000"
echo "   - Data: ./server/storage/chroma"
echo ""
echo "To stop: docker stop chromadb"
echo "To remove: docker rm chromadb"
echo "To view logs: docker logs -f chromadb"
