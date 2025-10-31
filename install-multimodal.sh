#!/bin/bash

echo "============================================"
echo "  Multimodal RAG Integration Installer"
echo "============================================"
echo ""

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check if we're in the right directory
if [ ! -f "package.json" ]; then
    echo -e "${RED}Error: package.json not found. Please run this script from the anything-llm root directory.${NC}"
    exit 1
fi

echo -e "${YELLOW}Step 1: Installing server dependencies...${NC}"
cd server
npm install @xenova/transformers chromadb sharp pdf-lib pdf2pic tesseract.js canvas --save
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Server dependencies installed${NC}"
else
    echo -e "${RED}✗ Failed to install server dependencies${NC}"
    exit 1
fi
cd ..

echo ""
echo -e "${YELLOW}Step 2: Installing collector dependencies...${NC}"
cd collector
npm install pdf2pic tesseract.js sharp canvas --save
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Collector dependencies installed${NC}"
else
    echo -e "${RED}✗ Failed to install collector dependencies${NC}"
    exit 1
fi
cd ..

echo ""
echo -e "${YELLOW}Step 3: Copying configuration template...${NC}"
if [ ! -f ".env" ]; then
    cp .env.multimodal.example .env
    echo -e "${GREEN}✓ Created .env from template${NC}"
    echo -e "${YELLOW}⚠ Please edit .env to configure your settings${NC}"
else
    echo -e "${YELLOW}⚠ .env already exists. Multimodal configuration is in .env.multimodal.example${NC}"
    echo -e "${YELLOW}  Please manually copy the multimodal settings to your .env${NC}"
fi

echo ""
echo -e "${YELLOW}Step 4: Creating storage directories...${NC}"
mkdir -p storage/multimodal
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Storage directories created${NC}"
else
    echo -e "${RED}✗ Failed to create storage directories${NC}"
fi

echo ""
echo "============================================"
echo -e "${GREEN}Installation Complete!${NC}"
echo "============================================"
echo ""
echo "Next steps:"
echo "1. Edit your .env file to enable multimodal:"
echo "   EMBEDDING_ENGINE=multimodal"
echo "   COLLECTOR_MULTIMODAL_ENABLED=true"
echo ""
echo "2. Review MULTIMODAL_INTEGRATION_GUIDE.md for:"
echo "   - Configuration options"
echo "   - Integration steps"
echo "   - Testing procedures"
echo ""
echo "3. Restart your server and collector services"
echo ""
echo "4. Upload a PDF with images to test!"
echo ""
echo "For help, see: MULTIMODAL_INTEGRATION_GUIDE.md"
echo ""
