# Multimodal RAG System - Embedding Storage Flowchart

```mermaid
graph TD
    %% Input Layer
    A[📄 PDF Document] --> B{Document Type Check}
    B -->|PDF| C[PyMuPDF Parser]
    B -->|DOCX| D[python-docx Parser]
    B -->|TXT| E[Text Reader]
    
    %% Processing Layer
    C --> F[Text Extraction]
    C --> G[Image Extraction]
    D --> F
    E --> F
    D --> H[DOCX Image Extraction]
    
    %% Content Processing
    F --> I[Text Chunking<br/>500 chars per chunk]
    G --> J[Image Processing]
    H --> J
    
    I --> K[DocumentChunk Objects<br/>• text<br/>• page_number<br/>• chunk_id<br/>• document_name<br/>• chunk_type]
    
    J --> L[ImageData Objects<br/>• PIL.Image<br/>• image_id<br/>• page_number<br/>• caption<br/>• ocr_text]
    
    %% Embedding Generation
    K --> M[Text Embedding<br/>OpenAI text-embedding-ada-002]
    L --> N[Image Embedding<br/>OpenAI CLIP/Vision Model]
    
    M --> O[Text Vector<br/>1536 dimensions]
    N --> P[Image Vector<br/>1536 dimensions]
    
    %% Storage Layer
    O --> Q[(Vector Database<br/>FAISS/Chroma)]
    P --> Q
    
    Q --> R[Vector Index<br/>• Embedding vectors<br/>• Similarity search]
    
    %% Metadata Storage
    K --> S[(Metadata Store)]
    L --> S
    
    S --> T[Text Metadata<br/>• chunk_id<br/>• document_name<br/>• page_number<br/>• chunk_type<br/>• content<br/>• content_type: 'text']
    
    S --> U[Image Metadata<br/>• image_id<br/>• document_name<br/>• page_number<br/>• caption<br/>• ocr_text<br/>• content_type: 'image'<br/>• image_data: PIL.Image]
    
    %% Query Processing
    V[🔍 User Query] --> W{Query Type}
    W -->|Text Query| X[Text Embedding]
    W -->|Image Query| Y[Image Embedding]
    
    X --> Z[Vector Search<br/>Cosine Similarity]
    Y --> Z
    
    Z --> Q
    Q --> AA[Retrieve Top-K<br/>Similar Vectors]
    
    AA --> BB[Fetch Corresponding<br/>Metadata]
    BB --> S
    
    S --> CC[Return Results<br/>• Text content<br/>• Image objects<br/>• Metadata]
    
    %% Response Generation
    CC --> DD[Response Generator]
    DD --> EE[📝 Final Response<br/>• Text answers<br/>• Relevant images<br/>• Source references]
    
    %% Styling
    classDef inputNode fill:#e3f2fd,stroke:#1976d2,stroke-width:2px
    classDef processNode fill:#f3e5f5,stroke:#7b1fa2,stroke-width:2px
    classDef embeddingNode fill:#e8f5e8,stroke:#388e3c,stroke-width:2px
    classDef storageNode fill:#fff3e0,stroke:#f57c00,stroke-width:2px
    classDef queryNode fill:#fce4ec,stroke:#c2185b,stroke-width:2px
    
    class A,V inputNode
    class B,C,D,E,F,G,H,I,J,K,L processNode
    class M,N,O,P,X,Y,Z embeddingNode
    class Q,R,S,T,U,AA,BB storageNode
    class W,CC,DD,EE queryNode
```

## System Architecture Details

### 🔄 Data Flow Process

1. **Document Ingestion**
   - PDF → PyMuPDF → Text + Images
   - DOCX → python-docx → Text + Embedded Images
   - TXT → Direct text processing

2. **Content Processing**
   - Text: Chunked into 500-character segments
   - Images: PIL objects with OCR text extraction
   - Metadata: Rich contextual information preserved

3. **Embedding Generation**
   - Text: OpenAI text-embedding-ada-002 (1536D)
   - Images: Vision model embeddings (1536D)
   - Unified vector space for multimodal search

4. **Storage Architecture**
   ```
   Vector Database (FAISS/Chroma)
   ├── Text Vectors [1536D float arrays]
   ├── Image Vectors [1536D float arrays]
   └── Vector Index [Similarity search optimization]
   
   Metadata Store
   ├── Text Metadata [JSON objects with content]
   ├── Image Metadata [JSON + PIL.Image objects]
   └── Document Context [Page numbers, sources]
   ```

5. **Query Processing**
   - Query → Embedding → Vector Search → Metadata Retrieval → Response

### 📊 Storage Distribution

| Component | Storage Location | Content Type |
|-----------|------------------|--------------|
| **Embedding Vectors** | Vector DB | Float arrays (1536D) |
| **Text Content** | Metadata Store | Original text strings |
| **Image Objects** | Metadata Store | PIL.Image objects |
| **Document Context** | Metadata Store | JSON metadata |
| **Search Index** | Vector DB | Optimized search structures |

### 🎯 Key Benefits

- **Unified Search**: Text and images in same vector space
- **Rich Context**: Complete metadata preservation  
- **Fast Retrieval**: Optimized vector similarity search
- **Multimodal**: Support for text + visual queries
- **Scalable**: Vector DB handles large document collections