# Enhanced Multimodal RAG System 使用指南

## 🎯 系統改進概述

我們成功實現了**富含上下文的圖片檢索**系統，主要改進包括：

### 1. 增強的 ImageData 結構
- ✅ 新增上下文欄位：`surrounding_text`, `section_title`, `page_context`
- ✅ 提取圖片前後文字：`preceding_text`, `following_text` 
- ✅ 保留完整的頁面語境資訊

### 2. 智能上下文提取
- ✅ 基於位置的前後文字提取
- ✅ 章節標題識別（字體大小判斷）
- ✅ 頁面摘要生成

### 3. 富含上下文的 Embedding
- ✅ 圖片 + 上下文文字組合 embedding
- ✅ 多層次 embedding（簡單+豐富）
- ✅ 智能相似度計算

### 4. 兩階段檢索系統
- ✅ Stage 1: 文字搜尋找相關內容
- ✅ Stage 2: 基於上下文的圖片搜尋
- ✅ 查詢增強和上下文過濾

## 🚀 使用方法

### 快速測試
```bash
# 基本測試
python test_enhanced_system.py

# 完整系統測試  
python enhanced_main.py --mode interactive

# 批次測試
python enhanced_main.py --mode batch
```

### 程式碼整合
```python
from enhanced_retrieval_engine import EnhancedRetrievalEngine
from document_processor import DocumentProcessor
from embedding_system import MultimodalEmbedder

# 初始化系統
processor = DocumentProcessor()
embedder = MultimodalEmbedder()
retriever = EnhancedRetrievalEngine()

# 處理文檔
text_chunks, images = processor.process_document("document.pdf")
text_emb = embedder.embed_document_chunks(text_chunks)
image_emb = embedder.embed_images_with_metadata(images)

# 初始化檢索
retriever.initialize_stores(text_emb, image_emb)

# 兩階段查詢
results = retriever.two_stage_query(
    query="系統架構圖",
    text_top_k=5,
    image_top_k=3,
    enable_context_enhancement=True
)
```

## 📊 檢索流程圖

```
用戶查詢: "微服務架構圖"
    ↓
階段1: 文字搜尋
    → 找到相關文字段落
    → 提取上下文資訊 (頁數、章節、關鍵字)
    ↓
階段2: 上下文增強圖片搜尋
    → 建構增強查詢: "微服務架構圖 | 第5頁 | 系統設計章節"
    → 搜尋圖片向量庫
    → 應用上下文過濾和排序
    ↓
返回結果: 文字 + 相關圖片
```

## 🔍 查詢範例

### 範例 1: 技術架構查詢
- **查詢**: "系統架構設計"
- **Stage 1**: 找到架構相關文字段落
- **Stage 2**: 基於頁數和章節找到架構圖
- **結果**: 精準匹配的架構圖片

### 範例 2: 性能分析查詢  
- **查詢**: "性能測試結果"
- **Stage 1**: 找到性能相關段落
- **Stage 2**: 找到同頁面或同章節的性能圖表
- **結果**: 相關的性能圖表和數據

## 🎯 系統優勢

### 精準度提升
- **上下文匹配**: 圖片不再孤立，帶有完整語境
- **智能過濾**: 基於頁面和章節的相關性過濾
- **多層次搜尋**: 圖片內容 + 上下文文字的組合搜尋

### 用戶體驗改善
- **更相關的結果**: 基於文檔結構的智能匹配
- **詳細的來源資訊**: 頁數、章節、上下文資訊
- **透明的搜尋過程**: 顯示搜尋策略和匹配方法

## 📈 性能指標

### Embedding 增強
- **Rich Context**: 1000字符的完整上下文描述
- **多重 Embedding**: 4種不同的向量表示
- **智能組合**: 基於相似度的最佳匹配選擇

### 檢索效果
- **上下文加成**: 同頁面圖片 +0.2，同文檔 +0.1 分數提升
- **章節匹配**: 標題匹配額外 +0.15 分數提升
- **過濾排序**: 基於多重因子的智能排序

## 🔧 配置選項

### 檢索參數
```python
results = retriever.two_stage_query(
    query="查詢內容",
    text_top_k=10,          # Stage 1 文字結果數量
    image_top_k=5,          # Stage 2 圖片結果數量  
    similarity_threshold=0.6, # 相似度閾值
    enable_context_enhancement=True  # 啟用上下文增強
)
```

### 上下文設定
- `surrounding_text`: 圖片前後文字
- `section_title`: 章節標題提取
- `page_context`: 頁面摘要長度（200字符）

## 🐛 故障排除

### 常見問題
1. **上下文提取失敗**: 檢查PDF結構和字體資訊
2. **Embedding 錯誤**: 確保模型載入正確
3. **記憶體不足**: 調整batch大小或圖片尺寸

### 調試模式
```python
# 顯示詳細資訊
results = retriever.two_stage_query(query, enable_context_enhancement=True)
print("檢索統計:", results['stats'])
print("增強查詢:", results['enhanced_query'])
```

## 🔮 未來改進方向

1. **更智能的章節識別**: 基於內容理解的章節檢測
2. **圖表類型分類**: 不同類型圖片的專門處理
3. **多語言支援**: 中英文混合文檔的更好處理
4. **相關性學習**: 基於用戶反饋的相關性調整

---

**🎉 恭喜！你現在擁有了一個功能強大的多模態RAG系統，可以精準地找到與查詢相關的圖片內容！**