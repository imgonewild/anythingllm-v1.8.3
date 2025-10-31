# ChromaDB 存儲格式文檔

## 概述
系統使用ChromaDB作為向量數據庫，分為兩個主要Collection：
- `text_chunks`: 存儲文字段落的向量和元數據
- `image_chunks`: 存儲圖片的向量和元數據

## 1. Text Collection (`text_chunks`)

### 存儲結構
```python
{
    "ids": ["text_chunk_id_1", "text_chunk_id_2", ...],
    "embeddings": [[0.1, 0.2, ...], [0.3, 0.4, ...], ...],  # 歸一化的向量
    "metadatas": [metadata_dict_1, metadata_dict_2, ...],
    "documents": ["文字內容1", "文字內容2", ...]
}
```

### Embedding詳情
- **來源**: Ollama `nomic-embed-text` 或 HuggingFace sentence-transformers
- **維度**: 768 (Ollama) 或 384 (sentence-transformers)
- **歸一化**: ✅ L2歸一化 (向量長度=1)
- **數據類型**: `List[float]`

### Metadata Schema
```python
{
    "page_number": int,           # 頁碼
    "document_name": str,         # 文件名稱
    "chunk_type": str,           # "text" 固定值
    "content_type": str          # "text" 固定值
}
```

### Document內容
- **類型**: 原始文字內容
- **來源**: PDF/DOCX等文件的文字段落
- **處理**: 無特殊處理，保持原始文字

## 2. Image Collection (`image_chunks`)

### 存儲結構
```python
{
    "ids": ["image_id_1", "image_id_2", ...],
    "embeddings": [[0.1, 0.2, ...], [0.3, 0.4, ...], ...],  # CLIP圖片向量
    "metadatas": [image_metadata_dict_1, image_metadata_dict_2, ...],
    "documents": ["富含上下文的圖片描述1", "富含上下文的圖片描述2", ...]
}
```

### Embedding詳情
- **來源**: CLIP `ViT-B/32` 模型
- **維度**: 512 (固定)
- **歸一化**: ✅ 已歸一化 (CLIP輸出)
- **數據類型**: `List[float]`

### Metadata Schema (基本)
```python
{
    "page_number": int,                    # 圖片所在頁碼
    "document_name": str,                  # 文件名稱
    "caption": str,                        # 圖片說明
    "ocr_text": str,                       # 圖片內文字(OCR)
    "content_type": "image",               # 固定值
    
    # 富含上下文版本額外包含:
    "surrounding_text": str,              # 周圍文字(截斷至500字符)
    "section_title": str,                  # 章節標題(截斷至100字符)
    "page_context": str                    # 頁面摘要(截斷至300字符)
}
```

### Document內容
- **類型**: 富含上下文的圖片描述文字
- **格式**: `"文件：xxx | 頁數：第X頁 | 章節：xxx | 圖片說明：xxx | ..."`
- **來源**: 由`_create_rich_image_context()`方法生成

## 3. 外部輔助存儲

### image_metadata.json
**位置**: `./vector_db/image_metadata.json`

**目的**: 存儲ChromaDB無法直接存儲的複雜數據

**結構**:
```json
{
    "image_id_1": {
        "page_number": 1,
        "document_name": "document.pdf",
        "caption": "圖片說明",
        "ocr_text": "圖片內文字",
        "combined_text": "簡單組合文字",
        "text_embedding": [0.1, 0.2, ...],           // 文字embedding(歸一化)
        "clip_text_embedding": [0.3, 0.4, ...],      // CLIP文字embedding
        
        // 富含上下文版本額外包含:
        "rich_context_text": "完整上下文描述",
        "rich_text_embedding": [0.5, 0.6, ...],      // 富含上下文embedding
        "rich_clip_embedding": [0.7, 0.8, ...],      // 富含上下文CLIP embedding
        "surrounding_text": "周圍文字內容",
        "section_title": "章節標題",
        "page_context": "頁面主題",
        "preceding_text": "前置文字",
        "following_text": "後續文字"
    }
}
```

### image_objects.pkl
**位置**: `./vector_db/image_objects.pkl`

**目的**: 存儲PIL Image對象供前端顯示

**結構**:
```python
{
    "image_id_1": PIL.Image.Image,  # PIL圖片對象
    "image_id_2": PIL.Image.Image,
    ...
}
```

## 4. ID生成規則

### Text Chunk ID
**格式**: `f"{document_name}_{page_number}_{chunk_index}"`
**範例**: `"report.pdf_1_0"`, `"manual.pdf_3_2"`

### Image ID
**格式**: `f"{document_name}_{page_number}_image_{image_index}"`
**範例**: `"report.pdf_1_image_0"`, `"manual.pdf_3_image_1"`

## 5. 搜索流程

### Text搜索
```python
query_embedding = embed_text(query)              # 生成query向量
results = text_collection.query(
    query_embeddings=[query_embedding],
    n_results=top_k
)
# 返回: 文字內容 + 基本metadata
```

### Image搜索
```python
query_embedding = embed_text_with_clip(query)    # 生成CLIP query向量
results = image_collection.query(
    query_embeddings=[query_embedding], 
    n_results=top_k
)
# 從image_metadata.json補充詳細信息
# 從image_objects.pkl獲取PIL圖片對象
```

## 6. 數據完整性

### 一致性保證
- ChromaDB的image_id必須在image_metadata.json中有對應記錄
- ChromaDB的image_id必須在image_objects.pkl中有對應PIL對象
- 所有embedding都經過L2歸一化處理

### 清理機制
- `delete_document()`: 同時清理ChromaDB + JSON + Pickle
- `clear_all()`: 同時清理所有存儲

## 7. 版本兼容性

### Enhanced vs Simple模式
- **Simple**: 只有基本caption+OCR的embedding
- **Enhanced**: 額外包含rich context的多種embedding
- 系統向後兼容，會自動檢查rich context欄位是否存在

### Embedding Provider兼容性
- **Ollama**: 768維，需要歸一化
- **HuggingFace**: 384維，已歸一化
- **CLIP**: 512維，已歸一化

## 8. 性能優化

### 向量歸一化
- Query時和存儲時都進行L2歸一化
- 確保餘弦相似度計算正確性

### 元數據分離
- 基本信息存ChromaDB (快速過濾)
- 詳細信息存JSON (詳細展示)  
- 圖片對象存Pickle (前端顯示)

### 搜索優化
- ChromaDB使用HNSW索引進行高效向量搜索
- 元數據過濾在向量搜索後進行
- 分離存儲減少ChromaDB負載