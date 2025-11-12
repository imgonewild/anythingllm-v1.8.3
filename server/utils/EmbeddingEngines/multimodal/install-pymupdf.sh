#!/bin/bash
# Installation script for PyMuPDF and Pillow

echo "=== Installing PyMuPDF for Multimodal Image Extraction ==="
echo ""

# Check if running with sudo
if [ "$EUID" -ne 0 ]; then
    echo "This script needs sudo access to install system packages."
    echo "You will be prompted for your password."
    echo ""
fi

# Step 1: Install system dependencies
echo "Step 1/4: Installing system dependencies..."
sudo apt-get update
sudo apt-get install -y python3.12-venv python3-pip

if [ $? -ne 0 ]; then
    echo "❌ Failed to install system dependencies"
    exit 1
fi

# Step 2: Create virtual environment
echo ""
echo "Step 2/4: Creating virtual environment..."
cd "$(dirname "$0")"
python3 -m venv venv

if [ $? -ne 0 ]; then
    echo "❌ Failed to create virtual environment"
    exit 1
fi

# Step 3: Install Python packages
echo ""
echo "Step 3/4: Installing PyMuPDF and Pillow..."
./venv/bin/pip install --upgrade pip
./venv/bin/pip install PyMuPDF==1.23.14 Pillow==10.1.0

if [ $? -ne 0 ]; then
    echo "❌ Failed to install Python packages"
    exit 1
fi

# Step 4: Verify installation
echo ""
echo "Step 4/4: Verifying installation..."
./venv/bin/python3 -c "import fitz; print('✅ PyMuPDF version:', fitz.version)"
./venv/bin/python3 -c "import PIL; print('✅ Pillow version:', PIL.__version__)"

echo ""
echo "==================================="
echo "✅ Installation completed successfully!"
echo "==================================="
echo ""
echo "You can now upload PDFs and images will be automatically extracted."
echo ""
