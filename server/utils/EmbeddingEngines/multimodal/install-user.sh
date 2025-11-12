#!/bin/bash
# User-level installation (no sudo required)

echo "=== Installing PyMuPDF (User-Level Installation) ==="
echo ""

cd "$(dirname "$0")"

# Try to install using system Python with --break-system-packages
echo "Step 1/2: Installing PyMuPDF and Pillow using system Python..."
python3 -m pip install --break-system-packages PyMuPDF==1.23.14 Pillow==10.1.0

if [ $? -ne 0 ]; then
    echo ""
    echo "❌ Installation failed."
    echo ""
    echo "This happens because your system requires sudo access."
    echo "Please run this command in your WSL terminal:"
    echo ""
    echo "  sudo apt-get update && sudo apt-get install -y python3-pip python3.12-venv"
    echo "  cd /mnt/c/Git-Projects/anything-llm-v1.8.3/anything-llm/server/utils/EmbeddingEngines/multimodal"
    echo "  python3 -m venv venv"
    echo "  source venv/bin/activate"
    echo "  pip install PyMuPDF==1.23.14 Pillow==10.1.0"
    echo ""
    exit 1
fi

# Step 2: Verify installation
echo ""
echo "Step 2/2: Verifying installation..."
python3 -c "import fitz; print('✅ PyMuPDF version:', fitz.version)"
python3 -c "import PIL; print('✅ Pillow version:', PIL.__version__)"

echo ""
echo "==================================="
echo "✅ Installation completed successfully!"
echo "==================================="
echo ""
