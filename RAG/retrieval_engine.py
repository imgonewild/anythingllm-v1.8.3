"""Retrieval engine for the multimodal RAG system."""

import os
from typing import List, Dict, Any, Optional, Tuple
import numpy as np
from document_processor import DocumentProcessor
from embedding_system import MultimodalEmbedder
from vector_store import MultimodalVectorStore
import config

class MultimodalRAGRetriever:
    """Main retrieval engine for the multimodal RAG system."""
    
    def __init__(self, vector_store_path: str = None):
        """
        Initialize the retrieval engine.
        
        Args:
            vector_store_path: Path to the vector store
        """
        self.document_processor = DocumentProcessor()
        self.embedder = MultimodalEmbedder()
        self.vector_store = MultimodalVectorStore(vector_store_path)
        
        self.top_k = config.TOP_K_RESULTS
        self.similarity_threshold = config.SIMILARITY_THRESHOLD
        
        print("Multimodal RAG Retriever initialized successfully")
    
    def ingest_document(self, file_path: str, chunking_strategy: str = "page") -> Dict[str, Any]:
        """
        Ingest a document into the RAG system.
        
        Args:
            file_path: Path to the document file
            chunking_strategy: "page" for page-based chunking, "section" for section-based chunking
            
        Returns:
            Dictionary with ingestion statistics
        """
        print(f"Ingesting document: {file_path} (strategy: {chunking_strategy})")
        
        try:
            # Process document
            text_chunks, images = self.document_processor.process_document(file_path, chunking_strategy)
            
            # Embed text chunks
            embedded_chunks = []
            if text_chunks:
                embedded_chunks = self.embedder.embed_document_chunks(text_chunks)
                self.vector_store.add_text_chunks(embedded_chunks)
            
            # Embed images
            embedded_images = []
            if images:
                embedded_images = self.embedder.embed_images_with_metadata(images)
                self.vector_store.add_image_chunks(embedded_images)
            
            stats = {
                'document_name': os.path.basename(file_path),
                'text_chunks': len(text_chunks),
                'images': len(images),
                'status': 'success'
            }
            
            print(f"Successfully ingested: {stats}")
            return stats
            
        except Exception as e:
            error_stats = {
                'document_name': os.path.basename(file_path),
                'text_chunks': 0,
                'images': 0,
                'status': 'error',
                'error': str(e)
            }
            print(f"Error ingesting document: {e}")
            return error_stats
    
    def query(self, query_text: str, 
             top_k: Optional[int] = None,
             include_images: bool = True,
             document_filter: Optional[str] = None,
             search_mode: str = "hybrid",
             use_enhanced_search: bool = False,
             text_top_k: int = 10,
             similarity_threshold: float = 0.6) -> Dict[str, Any]:
        """
        Query the RAG system.
        
        Args:
            query_text: The query string
            top_k: Number of results to return
            include_images: Whether to include images in results
            document_filter: Filter results by document name
            search_mode: "text", "image", "hybrid", or "enhanced"
            use_enhanced_search: Enable two-stage contextual search
            text_top_k: Number of text results for stage 1 (enhanced mode)
            similarity_threshold: Minimum similarity threshold
            
        Returns:
            Dictionary containing query results
        """
        if top_k is None:
            top_k = self.top_k
        
        print(f"Querying: '{query_text}' (mode: {search_mode})")
        
        try:
            # Enhanced two-stage search
            if use_enhanced_search or search_mode == "enhanced":
                return self._enhanced_two_stage_query(
                    query_text, top_k, text_top_k, similarity_threshold, 
                    document_filter, include_images
                )
            
            # Original search logic
            # Generate query embeddings
            query_embeddings = self.embedder.embed_query(query_text)
            
            results = {
                'query': query_text,
                'results': [],
                'total_results': 0,
                'search_mode': search_mode
            }
            
            if search_mode == "text":
                # Text-only search
                text_results = self.vector_store.search_text(
                    query_embeddings['text_embedding'],
                    top_k=top_k,
                    document_filter=document_filter
                )
                results['results'] = text_results
                
            elif search_mode == "image" and include_images:
                # Image-only search
                image_results = self.vector_store.search_images(
                    query_embeddings['clip_text_embedding'],
                    top_k=top_k,
                    document_filter=document_filter
                )
                results['results'] = image_results
                
            else:  # hybrid mode
                # Search both text and images
                text_results = self.vector_store.search_text(
                    query_embeddings['text_embedding'],
                    top_k=top_k,
                    document_filter=document_filter
                )
                
                image_results = []
                if include_images:
                    image_results = self.vector_store.search_images(
                        query_embeddings['clip_text_embedding'],
                        top_k=top_k,
                        document_filter=document_filter
                    )
                
                # Combine and rank results
                combined_results = self._combine_and_rank_results(
                    text_results, image_results, top_k
                )
                results['results'] = combined_results
            
            results['total_results'] = len(results['results'])
            
            # Filter by similarity threshold
            results['results'] = [
                r for r in results['results'] 
                if r.get('similarity_score', -999) >= self.similarity_threshold
            ]
            
            print(f"Found {len(results['results'])} relevant results")
            return results
            
        except Exception as e:
            print(f"Error during query: {e}")
            return {
                'query': query_text,
                'results': [],
                'total_results': 0,
                'error': str(e)
            }
    
    def _combine_and_rank_results(self, text_results: List[Dict[str, Any]], 
                                 image_results: List[Dict[str, Any]], 
                                 top_k: int) -> List[Dict[str, Any]]:
        """
        Combine and rank text and image results.
        
        Args:
            text_results: Text search results
            image_results: Image search results
            top_k: Number of top results to return
            
        Returns:
            Combined and ranked results
        """
        # For multimodal results, ensure we get both text and images
        # Take top text results and top image results separately, then combine
        
        # Calculate how many of each type to include
        text_count = min(len(text_results), max(1, top_k // 2))  # At least 1 text if available
        image_count = min(len(image_results), max(1, top_k - text_count))  # Fill remaining with images
        
        # If we have room and more text results, add them
        if text_count + image_count < top_k and len(text_results) > text_count:
            additional_text = min(len(text_results) - text_count, top_k - text_count - image_count)
            text_count += additional_text
        
        # Take the best from each category
        selected_results = []
        selected_results.extend(text_results[:text_count])
        selected_results.extend(image_results[:image_count])
        
        # Sort the final selection by similarity score
        selected_results.sort(key=lambda x: x.get('similarity_score', -999), reverse=True)
        
        return selected_results
    
    def get_similar_content(self, query_text: str, content_type: str = "both") -> List[Dict[str, Any]]:
        """
        Get similar content for a query.
        
        Args:
            query_text: Query string
            content_type: "text", "image", or "both"
            
        Returns:
            List of similar content
        """
        if content_type == "text":
            return self.query(query_text, search_mode="text")['results']
        elif content_type == "image":
            return self.query(query_text, search_mode="image")['results']
        else:
            return self.query(query_text, search_mode="hybrid")['results']
    
    def get_document_context(self, document_name: str, query_text: str) -> Dict[str, Any]:
        """
        Get context from a specific document.
        
        Args:
            document_name: Name of the document
            query_text: Query string
            
        Returns:
            Document-specific context
        """
        return self.query(
            query_text, 
            document_filter=document_name,
            search_mode="hybrid"
        )
    
    def list_documents(self) -> List[str]:
        """Get list of all ingested documents."""
        return self.vector_store.get_document_list()
    
    def get_stats(self) -> Dict[str, Any]:
        """Get system statistics."""
        vector_stats = self.vector_store.get_stats()
        embedding_stats = self.embedder.get_embedding_stats()
        
        return {
            'vector_store': vector_stats,
            'embedding_system': embedding_stats,
            'configuration': {
                'top_k_results': self.top_k,
                'similarity_threshold': self.similarity_threshold,
                'supported_formats': self.document_processor.supported_formats
            }
        }
    
    def delete_document(self, document_name: str):
        """
        Delete a document from the system.
        
        Args:
            document_name: Name of the document to delete
        """
        self.vector_store.delete_document(document_name)
        print(f"Deleted document: {document_name}")
    
    def clear_all_documents(self):
        """Clear all documents from the system."""
        self.vector_store.clear_all()
        print("Cleared all documents from the system")
    
    def batch_ingest(self, file_paths: List[str], chunking_strategy: str = "page") -> List[Dict[str, Any]]:
        """
        Ingest multiple documents in batch.
        
        Args:
            file_paths: List of file paths to ingest
            chunking_strategy: "page" for page-based chunking, "section" for section-based chunking
            
        Returns:
            List of ingestion results
        """
        results = []
        for file_path in file_paths:
            result = self.ingest_document(file_path, chunking_strategy)
            results.append(result)
        
        return results
    
    def search_with_context(self, query_text: str, context_window: int = 2) -> Dict[str, Any]:
        """
        Search with additional context from surrounding chunks.
        
        Args:
            query_text: Query string
            context_window: Number of surrounding chunks to include
            
        Returns:
            Results with expanded context
        """
        # Get initial results
        initial_results = self.query(query_text)
        
        # For each result, try to get surrounding context
        # This is a simplified implementation - could be enhanced
        enhanced_results = []
        
        for result in initial_results['results']:
            enhanced_result = result.copy()
            
            # Add context information
            enhanced_result['context_info'] = {
                'page_number': result.get('metadata', {}).get('page_number'),
                'document_name': result.get('metadata', {}).get('document_name'),
                'chunk_type': result.get('metadata', {}).get('chunk_type')
            }
            
            enhanced_results.append(enhanced_result)
        
        return {
            'query': query_text,
            'results': enhanced_results,
            'total_results': len(enhanced_results),
            'context_window': context_window
        }
    
    def get_document_summary(self, document_name: str) -> Dict[str, Any]:
        """
        Get a summary of a specific document.
        
        Args:
            document_name: Name of the document
            
        Returns:
            Document summary
        """
        # Get all chunks for the document
        text_results = self.vector_store.search_text(
            np.zeros(self.embedder.text_dim),  # Dummy embedding
            top_k=1000,  # Get many results
            document_filter=document_name
        )
        
        image_results = self.vector_store.search_images(
            np.zeros(self.embedder.clip_dim),  # Dummy embedding
            top_k=1000,  # Get many results
            document_filter=document_name
        )
        
        # Organize by pages
        pages = {}
        
        for result in text_results + image_results:
            page_num = result.get('metadata', {}).get('page_number', 1)
            if page_num not in pages:
                pages[page_num] = {'text_chunks': [], 'images': []}
            
            if result['content_type'] == 'text':
                pages[page_num]['text_chunks'].append(result)
            else:
                pages[page_num]['images'].append(result)
        
        return {
            'document_name': document_name,
            'total_pages': len(pages),
            'total_text_chunks': len(text_results),
            'total_images': len(image_results),
            'pages': pages
        }
    
    def _enhanced_two_stage_query(self, query_text: str, image_top_k: int, text_top_k: int, 
                                similarity_threshold: float, document_filter: Optional[str] = None,
                                include_images: bool = True) -> Dict[str, Any]:
        """
        Execute enhanced two-stage retrieval: text search → contextual image search.
        
        Args:
            query_text: User query
            image_top_k: Number of image results to return
            text_top_k: Number of text results to retrieve in stage 1
            similarity_threshold: Minimum similarity threshold
            document_filter: Filter results by specific document name
            include_images: Whether to include images in results
            
        Returns:
            Dictionary containing enhanced search results
        """
        print(f"🔍 開始兩階段檢索: {query_text}")
        
        try:
            # Stage 1: Text retrieval for context
            query_embeddings = self.embedder.embed_query(query_text)
            text_results = self.vector_store.search_text(
                query_embeddings['text_embedding'],
                top_k=text_top_k,
                document_filter=document_filter
            )
            
            # Filter text results by similarity threshold first
            filtered_text_results = [
                r for r in text_results 
                if r.get('similarity_score', 0) >= similarity_threshold
            ]
            
            print(f"📝 階段1: 原始找到 {len(text_results)} 個文字段落，過濾後 {len(filtered_text_results)} 個")
            
            # Extract context information from filtered results only
            context_info = []
            for i, result in enumerate(filtered_text_results):
                metadata = result.get('metadata', {})
                print(f"🔍 DEBUG: Text result metadata keys: {list(metadata.keys())}")
                if 'all_sections' in metadata:
                    print(f"🔍 DEBUG: Found all_sections: {metadata['all_sections']}")
                else:
                    print(f"⚠️ DEBUG: No all_sections in metadata")
                context_info.append({
                    'page_number': metadata.get('page_number'),
                    'document_name': metadata.get('document_name'),
                    'text_content': result.get('text', ''),
                    'chunk_type': metadata.get('chunk_type', 'text'),
                    'similarity_score': result.get('similarity_score', 0),
                    'section_title': metadata.get('section_title', ''),  # Include section title
                    'metadata': metadata  # Include full metadata for flexibility
                })

                # Debug output for first few results
                if i < 3:
                    print(f"   文字段落 {i+1}: 相似度={result.get('similarity_score', 0):.3f}")
            
            results = {
                'query': query_text,
                'results': filtered_text_results.copy(),
                'total_results': len(filtered_text_results),
                'search_mode': 'enhanced',
                'context_info': context_info,
                'enhanced_query': query_text,
                'search_strategy': 'two_stage'
            }

            #print(result)
            
            # Stage 2: Contextual image search if images are requested
            if include_images and context_info:
                enhanced_query = self._build_enhanced_query(query_text, context_info)
                # Add text results for section matching
                enhanced_query['text_results'] = filtered_text_results
                print(f"🔧 增強查詢結構:")
                print(f"   原始問題: {enhanced_query['original_query']}")
                print(f"   相關頁數: {enhanced_query['related_pages']}")
                print(f"   相關文件: {enhanced_query['related_documents'][:2]}...")  # Show first 2
                if enhanced_query.get('section_titles'):
                    titles_str = ', '.join(enhanced_query['section_titles'][:2])
                    print(f"   章節標題: {titles_str}...")
                
                # Search images with section priority (then page priority)
                enhanced_query_embeddings = self.embedder.embed_query(enhanced_query['original_query'])
                image_results = self._search_images_with_section_priority(
                    enhanced_query_embeddings['clip_text_embedding'],
                    enhanced_query,
                    image_top_k,
                    document_filter
                )
                
                # Apply final scoring and ranking
                filtered_image_results = self._apply_final_image_scoring(image_results, enhanced_query)
                
                print(f"🖼️ 階段2: 找到 {len(filtered_image_results)} 個相關圖片")
                
                # Debug: Check if images have image_object
                for i, img_result in enumerate(filtered_image_results):
                    has_img_obj = 'image_object' in img_result
                    similarity = img_result.get('similarity_score', 0)
                    print(f"   圖片 {i+1}: 相似度={similarity:.3f}, 有圖片物件={has_img_obj}")
                
                # Add images to results
                results['results'].extend(filtered_image_results)
                results['total_results'] = len(results['results'])
                results['enhanced_query'] = enhanced_query['text_query']
                results['image_results'] = filtered_image_results
                results['text_results'] = filtered_text_results
            
            # Filter by similarity threshold
            print(f"🔍 過濾前總結果: {len(results['results'])} 個")
            filtered_results = [
                r for r in results['results'] 
                if r.get('similarity_score', 0) >= similarity_threshold
            ]
            print(f"🔍 相似度閾值 {similarity_threshold} 過濾後: {len(filtered_results)} 個")
            results['results'] = filtered_results
            results['total_results'] = len(filtered_results)
            
            # Add statistics
            if context_info:
                pages = set(c['page_number'] for c in context_info if c['page_number'])
                docs = set(c['document_name'] for c in context_info if c['document_name'])
                results['stats'] = {
                    'text_candidates': len(filtered_text_results),
                    'image_candidates': len(results.get('image_results', [])),
                    'context_pages': len(pages),
                    'context_documents': len(docs)
                }
            
            return results
            
        except Exception as e:
            print(f"Error during enhanced query: {e}")
            # Fallback to regular hybrid search
            return self.query(query_text, top_k=image_top_k, include_images=include_images, 
                            document_filter=document_filter, search_mode="hybrid")
    
    def _build_enhanced_query(self, original_query: str, context_info: List[Dict]) -> Dict[str, Any]:
        """Build structured enhanced query using original query + context information."""
        import re
        from collections import Counter
        
        # Extract key information from context
        pages = [c['page_number'] for c in context_info if c.get('page_number') is not None]
        documents = [c['document_name'] for c in context_info if c.get('document_name')]
        
        # Extract section titles from context
        section_titles = []
        for c in context_info:
            # Try to get section title from the context item
            title = None
            if 'section_title' in c and c['section_title']:
                title = c['section_title']
            elif 'metadata' in c and c['metadata'].get('section_title'):
                title = c['metadata']['section_title']
            
            if title and title.strip() and title not in section_titles:
                section_titles.append(title.strip())
        
        # Extract keywords from text content
        all_text = ' '.join([c.get('text_content', '') for c in context_info])
        keywords = self._extract_keywords(all_text, top_n=10)
        
        # Build text query for embedding (enhanced with titles)
        query_parts = [f"原始查詢: {original_query}"]
        
        if pages:
            unique_pages = list(set(pages))[:5]
            query_parts.append(f"相關頁數: {', '.join(map(str, unique_pages))}")
        
        if documents:
            unique_docs = list(set(documents))[:3]
            query_parts.append(f"相關文件: {', '.join(unique_docs)}")
        
        if section_titles:
            # Include top section titles
            unique_titles = section_titles[:3]  # Limit to top 3 titles
            query_parts.append(f"章節標題: {' | '.join(unique_titles)}")
        
        if keywords:
            query_parts.append(f"關鍵詞: {', '.join(keywords)}")
        
        text_query = ' | '.join(query_parts)
        
        # Limit text query length
        if len(text_query) > 500:
            text_query = text_query[:500] + "..."
        
        # Return structured enhanced query with titles
        enhanced_query = {
            "original_query": original_query,
            "related_pages": list(set(pages)) if pages else [],
            "related_documents": list(set(documents)) if documents else [],
            "section_titles": section_titles,
            "keywords": keywords,
            "text_query": text_query
        }
        
        return enhanced_query
    
    def _extract_keywords(self, text: str, top_n: int = 10) -> List[str]:
        """Extract key terms from text content."""
        import re
        from collections import Counter
        
        # Remove common stop words (simplified)
        stop_words = {'的', '是', '在', '有', '和', '與', '或', '但', '及', '等', 
                     '為', '於', '由', '以', '了', '到', '從', '對', '將', '會'}
        
        # Extract words (Chinese + English)
        words = re.findall(r'[\u4e00-\u9fff]+|[a-zA-Z]+', text.lower())
        
        # Filter and count
        filtered_words = [w for w in words if len(w) > 1 and w not in stop_words]
        word_counts = Counter(filtered_words)
        
        # Return top keywords
        return [word for word, count in word_counts.most_common(top_n)]
    
    def _search_images_with_section_priority(self, query_embedding: np.ndarray, 
                                            enhanced_query: Dict[str, Any],
                                            target_count: int,
                                            document_filter: Optional[str] = None) -> List[Dict[str, Any]]:
        """Search images with section priority first, then page priority - prioritize same-section images first."""
        related_pages = enhanced_query.get('related_pages', [])
        related_docs = enhanced_query.get('related_documents', [])
        related_titles = enhanced_query.get('section_titles', [])
        
        # Extract sections from text results for more accurate section-based search
        related_sections = set()
        text_results = enhanced_query.get('text_results', [])
        for text_result in text_results:
            metadata = text_result.get('metadata', {})
            if 'all_sections' in metadata and metadata['all_sections']:
                sections = metadata['all_sections'].split(',')
                related_sections.update(sections)
        
        print(f"🎯 Section-priority search: Found {len(related_sections)} related sections: {list(related_sections)[:3]}...")
        
        if not related_sections and not related_pages and not related_titles:
            # Fallback to regular search if no context info
            return self.vector_store.search_images(
                query_embedding, 
                top_k=target_count,
                document_filter=document_filter
            )
        
        all_results = []
        
        # Step 1: Search for same-section images first (NEW PRIORITY)
        if related_sections:
            section_results = self.vector_store.search_images_by_section(
                query_embedding,
                list(related_sections),
                target_count,
                document_filter
            )
            
            # Mark these as same-section priority images
            for result in section_results:
                result['priority_type'] = 'same_section'
                result['matched_section'] = result.get('matched_section', '')
            
            all_results.extend(section_results)
            print(f"📚 Section search: 找到 {len(section_results)} 個相同section圖片")
        
        # Step 2: Search for same-page images (secondary priority)
        # Create set of already found image IDs to avoid duplicates
        seen_ids = set(result.get('id') for result in all_results)
        
        for page in related_pages:
            try:
                page_results = self.vector_store.search_images(
                    query_embedding,
                    top_k=target_count,
                    document_filter=document_filter,
                    page_filter={'page_number': page}
                )
                
                # Add non-duplicate page results
                for result in page_results:
                    result_id = result.get('id')
                    if result_id and result_id not in seen_ids:
                        # Check if this image already has section priority
                        existing_result = next((r for r in all_results if r.get('id') == result_id), None)
                        if existing_result:
                            # Upgrade priority if it also matches page
                            if existing_result.get('priority_type') == 'same_section':
                                existing_result['priority_type'] = 'same_section_page'
                                existing_result['priority_page'] = page
                        else:
                            # New image with page match
                            result['priority_type'] = 'same_page'
                            result['priority_page'] = page
                            all_results.append(result)
                            seen_ids.add(result_id)
                
                added_count = len([r for r in page_results if r.get('id') not in seen_ids or r.get('id') in seen_ids])
                print(f"📄 頁數 {page}: 找到 {len(page_results)} 個圖片 (新增 {len(page_results) - len(seen_ids & set(r.get('id') for r in page_results))} 個)")
                
            except Exception as e:
                print(f"⚠️ 搜索頁數 {page} 時出錯: {e}")
                continue
        
        # Step 3: Search for same-title images if still needed
        current_seen_ids = set(result.get('id') for result in all_results)
        if related_titles and len(all_results) < target_count:
            title_results = self._search_images_by_title(query_embedding, related_titles, target_count, document_filter)
            
            # Add non-duplicate title results
            for result in title_results:
                result_id = result.get('id')
                if result_id and result_id not in current_seen_ids:
                    result['priority_type'] = 'same_title'
                    all_results.append(result)
                    current_seen_ids.add(result_id)
        
        # Remove duplicates (in case of overlapping results)
        seen_ids = set()
        unique_results = []
        for result in all_results:
            result_id = result.get('id')
            if result_id and result_id not in seen_ids:
                seen_ids.add(result_id)
                unique_results.append(result)
        
        print(f"🎯 Section-priority search 總數: {len(unique_results)}")
        
        # Step 4: If we need more images, search globally
        if len(unique_results) < target_count:
            needed_count = target_count - len(unique_results)
            print(f"🔍 需要額外搜索 {needed_count} 個圖片")
            
            # Search globally, excluding already found images
            global_results = self.vector_store.search_images(
                query_embedding,
                top_k=needed_count * 2,  # Search more to account for duplicates
                document_filter=document_filter
            )
            
            # Add non-duplicate results
            for result in global_results:
                result_id = result.get('id')
                if result_id and result_id not in seen_ids:
                    result['priority_type'] = 'other'
                    unique_results.append(result)
                    seen_ids.add(result_id)
                    
                    if len(unique_results) >= target_count:
                        break
            
            print(f"🔍 全局搜索添加: {len([r for r in unique_results if r.get('priority_type') == 'other'])} 個圖片")
        
        return unique_results[:target_count]
    
    def _search_images_by_title(self, query_embedding: np.ndarray, related_titles: List[str], 
                               target_count: int, document_filter: Optional[str] = None) -> List[Dict[str, Any]]:
        """Search for images that have matching section titles."""
        title_results = []
        
        # Get all images first, then filter by title matching
        # Note: We need a larger search to find title matches since ChromaDB doesn't support text matching in metadata
        try:
            all_images = self.vector_store.search_images(
                query_embedding,
                top_k=target_count * 3,  # Search more to find title matches
                document_filter=document_filter
            )
            
            # Filter images by title matching
            for img_result in all_images:
                metadata = img_result.get('metadata', {})
                img_section_title = metadata.get('section_title', '') or img_result.get('section_title', '')
                
                if img_section_title and related_titles:
                    title_match = False
                    matched_title = None
                    
                    for related_title in related_titles:
                        if related_title and (
                            img_section_title.strip().lower() in related_title.strip().lower() or
                            related_title.strip().lower() in img_section_title.strip().lower()
                        ):
                            title_match = True
                            matched_title = related_title
                            break
                    
                    if title_match:
                        # Check if this is also a same-page image
                        img_page = metadata.get('page_number')
                        
                        # Mark priority type based on what matches
                        if img_result.get('priority_type') == 'same_page':
                            img_result['priority_type'] = 'same_page_title'  # Both page and title match
                        else:
                            img_result['priority_type'] = 'same_title'  # Only title match
                        
                        img_result['matched_title'] = matched_title
                        title_results.append(img_result)
                        
                        if len(title_results) >= target_count:
                            break
            
            print(f"📋 標題匹配: 找到 {len(title_results)} 個圖片")
            
        except Exception as e:
            print(f"⚠️ 標題搜索時出錯: {e}")
        
        return title_results
    
    def search_images_by_sections(self, query_text: str, section_titles: List[str], 
                                 top_k: int = 5, document_filter: Optional[str] = None) -> Dict[str, Any]:
        """
        Search for images specifically from given sections.
        
        Args:
            query_text: Query text
            section_titles: List of section titles to search within
            top_k: Number of results to return
            document_filter: Optional document name filter
            
        Returns:
            Dictionary containing search results
        """
        print(f"🔍 Section-based image search: {query_text}")
        print(f"📚 Target sections: {section_titles}")
        
        try:
            # Generate query embeddings
            query_embeddings = self.embedder.embed_query(query_text)
            
            # Use the new section-based search from vector store
            image_results = self.vector_store.search_images_by_section(
                query_embeddings['clip_text_embedding'],
                section_titles,
                top_k,
                document_filter
            )
            
            # Format results
            results = {
                'query': query_text,
                'results': image_results,
                'total_results': len(image_results),
                'search_mode': 'section_based_images',
                'target_sections': section_titles
            }
            
            print(f"🖼️ Found {len(image_results)} images from specified sections")
            
            return results
            
        except Exception as e:
            print(f"Error during section-based image search: {e}")
            return {
                'query': query_text,
                'results': [],
                'total_results': 0,
                'error': str(e),
                'target_sections': section_titles
            }
    
    def _apply_final_image_scoring(self, image_results: List[Dict[str, Any]], 
                                  enhanced_query: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Apply final scoring and ranking to image results."""
        related_pages = set(enhanced_query.get('related_pages', []))
        related_docs = set(enhanced_query.get('related_documents', []))
        #related_titles = enhanced_query.get('section_titles', [])
        
        # Extract sections from text results for precise section matching
        related_sections = set()
        text_results = enhanced_query.get('text_results', [])
        for text_result in text_results:
            metadata = text_result.get('metadata', {})
            if 'all_sections' in metadata and metadata['all_sections']:
                sections = metadata['all_sections'].split(',')
                related_sections.update(sections)
        
        print(f"🔍 Final scoring: Found {len(related_sections)} related sections for section matching")
        
        scored_results = []
        
        for result in image_results:
            metadata = result.get('metadata', {})
            base_score = result.get('similarity_score', 0)
            priority_type = result.get('priority_type', 'other')
            
            # Calculate context boost
            boost = 0.0
            boost_details = []
            
            # Page match bonus (higher for same-page images)
            if metadata.get('page_number') in related_pages:
                page_bonus = 0.2
                boost += page_bonus
                boost_details.append(f"同頁+{page_bonus}")
            
            # Document match bonus  
            if metadata.get('document_name') in related_docs:
                doc_bonus = 0.1
                boost += doc_bonus
                boost_details.append(f"同文件+{doc_bonus}")
            
            # Section title match bonus
            img_section_title = metadata.get('section_title', '') or result.get('section_title', '')

            # Precise section match bonus (new feature!)
            if img_section_title and related_sections:
                # Check if image section exactly matches any text sections
                if img_section_title in related_sections:
                    section_bonus = 0.3  # Slightly higher than fuzzy title match
                    boost += section_bonus
                    boost_details.append(f"精確section+{section_bonus}")
                    print(f"🎯 Precise section match: Image '{img_section_title}' matches text sections")
            
            # Final score (capped at 1.0)
            final_score = min(base_score + boost, 1.0)
            
            result_copy = result.copy()
            result_copy['similarity_score'] = final_score
            result_copy['context_boost'] = boost
            result_copy['boost_details'] = boost_details
            result_copy['original_similarity'] = base_score
            result_copy['priority_type'] = priority_type
            
            scored_results.append(result_copy)
        
       
        # Debug output
        for i, result in enumerate(scored_results[:3]):
            page = result.get('metadata', {}).get('page_number', '?')
            original = result.get('original_similarity', 0)
            final = result.get('similarity_score', 0)
            priority = result.get('priority_type', 'unknown')
            boost_details = result.get('boost_details', [])
            boost_str = ', '.join(boost_details) if boost_details else '無加分'
            print(f"   最終排序 {i+1}: 頁數={page}, 類型={priority}, 原始={original:.3f}, 最終={final:.3f} ({boost_str})")
        
        return scored_results
    
    def _filter_and_rank_images(self, image_results: List[Dict[str, Any]], 
                               context_info: List[Dict], top_k: int) -> List[Dict[str, Any]]:
        """Legacy filter and rank function for backward compatibility."""
        if not context_info:
            return image_results[:top_k]
        
        # Get context pages and documents
        context_pages = set(c.get('page_number') for c in context_info if c.get('page_number'))
        context_docs = set(c.get('document_name') for c in context_info if c.get('document_name'))
        
        # Score images based on context relevance
        scored_results = []
        for result in image_results:
            metadata = result.get('metadata', {})
            base_score = result.get('similarity_score', 0)
            
            # Boost score for images from relevant pages/documents
            boost = 0.0
            if metadata.get('page_number') in context_pages:
                boost += 0.2  # Same page bonus
            if metadata.get('document_name') in context_docs:
                boost += 0.1  # Same document bonus
            
            final_score = min(base_score + boost, 1.0)  # Cap at 1.0
            
            result_copy = result.copy()
            result_copy['similarity_score'] = final_score
            result_copy['context_boost'] = boost
            scored_results.append(result_copy)
        
        # Sort by final score and return top results
        scored_results.sort(key=lambda x: x['similarity_score'], reverse=True)
        return scored_results[:top_k]