#!/usr/bin/env python3
"""
Bridge script to extract images from PDFs using PyMuPDF.
Adapted from ../../../../../RAG/document_processor.py
"""

import sys
import json
import io
import base64
from PIL import Image
import fitz  # PyMuPDF

def extract_images_from_pdf(pdf_path):
    """Extract images from PDF using PyMuPDF."""
    images = []

    try:
        doc = fitz.open(pdf_path)

        for page_num in range(len(doc)):
            page = doc[page_num]
            page_text = page.get_text()

            # Get embedded images
            image_list = page.get_images()

            for img_index, img in enumerate(image_list):
                try:
                    # Get image data
                    xref = img[0]
                    pix = fitz.Pixmap(doc, xref)

                    # Convert to RGB if needed
                    if pix.n - pix.alpha < 4:
                        img_data = pix.tobytes("png")
                        pil_image = Image.open(io.BytesIO(img_data))

                        # Convert to base64
                        buffered = io.BytesIO()
                        pil_image.save(buffered, format="PNG")
                        img_base64 = base64.b64encode(buffered.getvalue()).decode()

                        # Get surrounding text (simple approach)
                        surrounding_text = page_text[:500] if len(page_text) > 500 else page_text

                        images.append({
                            'id': f'page{page_num+1}_img{img_index}',
                            'image': img_base64,
                            'pageNumber': page_num + 1,
                            'caption': f'Image from page {page_num + 1}',
                            'ocrText': '',  # Would need Tesseract for OCR
                            'surroundingText': surrounding_text,
                            'metadata': {
                                'contentType': 'image/png',
                                'hasOCR': False,
                                'pageNumber': page_num + 1
                            }
                        })

                    pix = None
                except Exception as e:
                    print(f"Error extracting image {img_index} from page {page_num + 1}: {e}", file=sys.stderr)
                    continue

        doc.close()
        return images

    except Exception as e:
        print(f"Error processing PDF: {e}", file=sys.stderr)
        return []

if __name__ == '__main__':
    if len(sys.argv) != 2:
        print("Usage: extract_images.py <pdf_path>", file=sys.stderr)
        sys.exit(1)

    pdf_path = sys.argv[1]
    images = extract_images_from_pdf(pdf_path)

    # Output as JSON
    print(json.dumps(images, indent=2))
