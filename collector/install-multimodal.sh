#!/bin/bash

# Installation script for multimodal PDF processing dependencies
# This script installs optional dependencies for enhanced image extraction

echo "============================================"
echo "Multimodal PDF Processing Setup"
echo "============================================"
echo ""

# Step 1: Rebuild canvas for current environment (important for WSL)
echo "Step 1: Rebuilding canvas module for current environment..."
echo ""

if npm rebuild canvas 2>&1 | grep -q "rebuilt dependencies successfully"; then
    echo "✅ Canvas rebuilt successfully"

    # Verify canvas works
    if node -e "require('canvas'); console.log('Canvas verification: OK')" 2>&1 | grep -q "OK"; then
        echo "✅ Canvas verification passed"
    else
        echo "⚠️  Canvas verification failed. Checking dependencies..."
        echo ""
    fi
else
    echo "⚠️  Canvas rebuild had warnings. Checking system dependencies..."
    echo ""
fi

echo ""

# Step 2: Check and install GraphicsMagick
echo "Step 2: Checking for GraphicsMagick (optional optimization)..."
echo ""

# Check current OS
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    echo "Detected Linux system"

    # Check for package manager
    if command -v apt-get &> /dev/null; then
        echo "Using apt-get package manager"
        echo ""
        echo "Installing GraphicsMagick for optimal PDF image extraction..."
        echo "This is OPTIONAL - the system will work without it using pure JavaScript fallback"
        echo ""

        sudo apt-get update
        sudo apt-get install -y graphicsmagick

        # Verify installation
        if command -v gm &> /dev/null; then
            echo "✅ GraphicsMagick installed successfully!"
            gm version | head -3
        else
            echo "⚠️  GraphicsMagick installation failed or not in PATH"
            echo "The system will use pure JavaScript fallback (pdfjs+canvas)"
        fi

    elif command -v yum &> /dev/null; then
        echo "Using yum package manager"
        sudo yum install -y GraphicsMagick

    elif command -v dnf &> /dev/null; then
        echo "Using dnf package manager"
        sudo dnf install -y GraphicsMagick
    else
        echo "⚠️  Could not detect package manager"
        echo "Please install GraphicsMagick manually:"
        echo "  Ubuntu/Debian: sudo apt-get install graphicsmagick"
        echo "  CentOS/RHEL:   sudo yum install GraphicsMagick"
        echo "  Fedora:        sudo dnf install GraphicsMagick"
    fi

elif [[ "$OSTYPE" == "darwin"* ]]; then
    echo "Detected macOS system"

    if command -v brew &> /dev/null; then
        echo "Installing GraphicsMagick via Homebrew..."
        brew install graphicsmagick
    else
        echo "⚠️  Homebrew not found. Please install GraphicsMagick manually:"
        echo "  brew install graphicsmagick"
        echo "  Or install Homebrew first: https://brew.sh"
    fi

else
    echo "⚠️  Unsupported operating system: $OSTYPE"
    echo "Please install GraphicsMagick manually for your platform"
fi

echo ""
echo "============================================"
echo "Setup Information"
echo "============================================"
echo ""
echo "Image Extraction Strategies:"
echo "  1. pdf-lib: Detects embedded images (always available)"
echo "  2. pdf2pic: High-quality extraction (requires GraphicsMagick)"
echo "  3. pdfjs+canvas: Pure JavaScript fallback (always available)"
echo ""
echo "If GraphicsMagick is not installed, the system will automatically"
echo "fall back to the pure JavaScript solution using pdfjs+canvas."
echo ""
echo "To verify GraphicsMagick installation:"
echo "  gm version"
echo ""
