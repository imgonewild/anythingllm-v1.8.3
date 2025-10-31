# Two-Stage Enhanced Retrieval Workflow

## System Overview

**Core Observation**: Images in documents typically follow or illustrate text content. Therefore, use text-based answers as reference to query relevant images.

## Data Storage Structure

```mermaid
flowchart TD
    subgraph "💾 ChromaDB Collections"
        subgraph "📝 Text Collection"
            A[Text Embedding<br/>TEXT Encoder]
            B[Metadata:<br/>• page_number<br/>• chunk_id: doc_p1_c0<br/>• document_name<br/>• section_title]
            C[Document:<br/>chunk content]
        end
        
        subgraph "🖼️ Image Collection"
            D[Image Embedding<br/>CLIP Encoder]
            E[Metadata:<br/>• page_number<br/>• image_id<br/>• document_name<br/>• section_title: 2.2 Search driver<br/>• caption: None<br/>• ocr_text: Search for driver<br/>• surrounding_text: Click on [IMAGE_HERE] to search...]
        end
    end
    
    style A fill:#e3f2fd
    style D fill:#fce4ec
```

## Two-Stage Retrieval Process

```mermaid
flowchart TD
    A[🔍 User Query] --> B[Dual Embedding Generation]
    
    B --> C[Text Embedding<br/>TEXT Encoder]
    B --> D[Image Embedding<br/>CLIP Encoder]
    
    C --> E[🎯 Stage 1: Text-Based Discovery]
    
    E --> F[Vector Search<br/>ChromaDB Text Collection]
    F --> G[Similarity Filtering<br/>Threshold-based]
    G --> H[Top-K Text Chunks]
    
    H --> I[📊 Context Extraction]
    I --> J[Extract: page_number, section_title]
    I --> K[Build Priority Context]
    
    K --> L[🖼️ Stage 2: Context-Aware Image Search]
    
    D --> L
    L --> M[CLIP Vector Search<br/>ChromaDB Image Collection]
    
    M --> N[📈 Priority Scoring System]
    
    N --> O[Base Image Similarity Score]
    N --> P[Same Page Bonus<br/>+0.2]
    N --> Q[Same Title Bonus<br/>+0.3]
    
    O --> R[🎯 Final Image Ranking]
    P --> R
    Q --> R
    
    R --> S[📋 Combined Results<br/>Text + Prioritized Images]
    
    %% Example Data Flow
    T[📝 Example Stage 1 Results] --> U[Chunk1: page 1, title 1, sim: 0.98<br/>Chunk2: page 6, title 2, sim: 0.8]
    U --> V[📊 Priority Context:<br/>Pages: 1, 6<br/>Titles: title 1, title 2]
    
    V --> W[🖼️ Stage 2 Priority Boost]
    W --> X[Images in page 1,6: +0.2<br/>Images under title 1,2: +0.3<br/>Max boost: +0.5 same page + title]
    
    %% Styling
    style E fill:#f1f8e9
    style L fill:#fce4ec
    style R fill:#fff3e0
    style S fill:#e8f5e8
    
    %% Example styling
    style T fill:#e1f5fe
    style W fill:#f3e5f5
```

## Stage 1: Text-Based Discovery Detail

```mermaid
flowchart LR
    A[User Query:<br/>'How to search driver?'] --> B[TEXT Encoder<br/>Embedding Generation]
    
    B --> C[Vector Similarity Search<br/>ChromaDB Text Collection]
    
    C --> D[Raw Results:<br/>All text chunks with scores]
    
    D --> E[Threshold Filtering<br/>Keep similarity > threshold]
    
    E --> F[Top-K Selection<br/>Select best K chunks]
    
    F --> G[📊 Result Example:<br/>Chunk1: page=1, title='2.1 Driver Setup', sim=0.98<br/>Chunk2: page=6, title='2.2 Search Driver', sim=0.85<br/>Chunk3: page=6, title='2.2 Search Driver', sim=0.80]
    
    G --> H[Context Extraction:<br/>Priority Pages: 1, 6<br/>Priority Titles: 2.1 Driver Setup, 2.2 Search Driver]
    
    style A fill:#e3f2fd
    style G fill:#f1f8e9
    style H fill:#fff3e0
```

## Stage 2: Context-Aware Image Search Detail

```mermaid
flowchart TD
    A[Stage 1 Context:<br/>Pages: 1, 6<br/>Titles: 2.1 Driver Setup, 2.2 Search Driver] --> B[User Query CLIP Embedding]
    
    B --> C[Vector Search<br/>All Images in ChromaDB]
    
    C --> D[Base Similarity Scores]
    
    D --> E[Priority Scoring Logic]
    
    E --> F{Image Page in [1, 6]?}
    E --> G{Image Title matches?}
    
    F -->|Yes| H[+0.2 Page Bonus]
    F -->|No| I[No Page Bonus]
    
    G -->|Yes| J[+0.3 Title Bonus]
    G -->|No| K[No Title Bonus]
    
    H --> L[Calculate Final Score]
    I --> L
    J --> L
    K --> L
    
    L --> M[Final Score = Base + Page Bonus + Title Bonus]
    
    M --> N[📊 Scoring Example:<br/><br/>Image A: page=1, title=2.1 Driver Setup<br/>Base: 0.7, Page: +0.2, Title: +0.3, Final: 1.2<br/><br/>Image B: page=3, title=Other<br/>Base: 0.8, Page: +0.0, Title: +0.0, Final: 0.8<br/><br/>Image C: page=6, title=2.2 Search Driver<br/>Base: 0.6, Page: +0.2, Title: +0.3, Final: 1.1]
    
    N --> O[🎯 Ranked Results:<br/>1. Image A score 1.2<br/>2. Image C score 1.1<br/>3. Image B score 0.8]
    
    style A fill:#fff3e0
    style M fill:#f3e5f5
    style N fill:#e8f5e8
    style O fill:#c8e6c9
```

## Priority Bonus System

```mermaid
graph LR
    subgraph "🎯 Priority Scoring Matrix"
        A[Image Metadata] --> B{Same Page?}
        A --> C{Same Title?}
        
        B -->|✅ Yes| D[+0.2 Bonus]
        B -->|❌ No| E[+0.0]
        
        C -->|✅ Yes| F[+0.3 Bonus]
        C -->|❌ No| G[+0.0]
        
        D --> H[📊 Total Bonus Calculation]
        E --> H
        F --> H
        G --> H
        
        H --> I[Max Possible Bonus: +0.5<br/>Same Page + Same Title]
    end
    
    style D fill:#c8e6c9
    style F fill:#c8e6c9
    style I fill:#fff3e0
```

## Complete Flow Example

```mermaid
flowchart TD
    A[👤 User Query: 'How to search for available drivers?'] 
    
    A --> B[🔄 Dual Encoding]
    B --> C[Text Embedding] 
    B --> D[CLIP Embedding]
    
    C --> E[📝 Stage 1: Text Search Results]
    E --> F[Chunk1: page=1, title='2.1 Driver Setup', similarity=0.98<br/>Chunk2: page=6, title='2.2 Search Driver', similarity=0.85]
    
    F --> G[📊 Priority Context Building]
    G --> H[Priority Pages: 1, 6<br/>Priority Titles: 2.1 Driver Setup, 2.2 Search Driver]
    
    D --> I[🖼️ Stage 2: Image Search]
    H --> I
    
    I --> J[Image Search Results with Priority Scoring]
    J --> K[Image A: page=1, title=2.1, base=0.7, final=1.2, bonus=+0.5<br/>Image B: page=6, title=2.2, base=0.6, final=1.1, bonus=+0.5<br/>Image C: page=3, title=other, base=0.8, final=0.8, bonus=+0.0]
    
    K --> L[🎯 Final Ranked Results:<br/>📝 Text: Chunks about driver search<br/>🖼️ Images: Driver search interface, setup screens]
    
    style A fill:#e3f2fd
    style E fill:#f1f8e9
    style I fill:#fce4ec
    style L fill:#c8e6c9
```

## Key Benefits

### 🎯 **Text-First Approach**
- Leverages the fact that images typically illustrate text content
- Uses text context to guide image selection

### 📊 **Priority Scoring System**
- **Page Priority (+0.2)**: Images on same pages as relevant text
- **Title Priority (+0.3)**: Images under same section titles
- **Maximum Boost (+0.5)**: Same page AND same title

### 🔍 **Two-Stage Efficiency**
- **Stage 1**: Fast text search identifies relevant context
- **Stage 2**: Context-aware image search with priority boosting

### 📈 **Enhanced Relevance**
- Combines semantic similarity with structural document context
- Ensures images are contextually related to text answers