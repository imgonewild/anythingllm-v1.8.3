"""Vector database for storing and retrieving multimodal embeddings."""

import os
import json
import pickle
from typing import List, Dict, Any, Optional, Tuple
import numpy as np
import chromadb
from chromadb.config import Settings
import config

class MultimodalVectorStore:
    """Vector database for storing text and image embeddings."""
    
    def __init__(self, persist_directory: str = None):
        """
        Initialize the vector store.
        
        Args:
            persist_directory: Directory to persist the database
        """
        self.persist_directory = persist_directory or config.VECTOR_DB_PATH
        os.makedirs(self.persist_directory, exist_ok=True)
        
        # Initialize ChromaDB
        self.client = chromadb.PersistentClient(path=self.persist_directory)
        
        # Create collections for different content types
        self.text_collection = self._get_or_create_collection("text_chunks")
        self.image_collection = self._get_or_create_collection("image_chunks")
        
        # Metadata storage for images (since ChromaDB doesn't store binary data well)
        self.image_metadata_file = os.path.join(self.persist_directory, "image_metadata.json")
        self.image_objects_file = os.path.join(self.persist_directory, "image_objects.pkl")
        
        self.image_metadata = self._load_image_metadata()
        self.image_objects = self._load_image_objects()
    
    def _get_or_create_collection(self, name: str):
        """Get or create a ChromaDB collection."""
        try:
            return self.client.get_collection(name)
        except ValueError:
            return self.client.create_collection(name)
    
    def _load_image_metadata(self) -> Dict[str, Any]:
        """Load image metadata from file."""
        if os.path.exists(self.image_metadata_file):
            with open(self.image_metadata_file, 'r') as f:
                return json.load(f)
        return {}
    
    def _save_image_metadata(self):
        """Save image metadata to file."""
        with open(self.image_metadata_file, 'w') as f:
            json.dump(self.image_metadata, f, indent=2)
    
    def _load_image_objects(self) -> Dict[str, Any]:
        """Load image objects from pickle file."""
        if os.path.exists(self.image_objects_file):
            with open(self.image_objects_file, 'rb') as f:
                return pickle.load(f)
        return {}
    
    def _save_image_objects(self):
        """Save image objects to pickle file."""
        with open(self.image_objects_file, 'wb') as f:
            pickle.dump(self.image_objects, f)
    
    def add_text_chunks(self, embedded_chunks: List[Dict[str, Any]]):
        """
        Add text chunks to the vector store.
        
        Args:
            embedded_chunks: List of embedded text chunks
        """
        if not embedded_chunks:
            return
        
        ids = [chunk['id'] for chunk in embedded_chunks]
        
        # Normalize embeddings if needed
        embeddings = []
        for chunk in embedded_chunks:
            emb = chunk['text_embedding']
            norm = np.linalg.norm(emb)
            if norm > 0:
                emb = emb / norm
            embeddings.append(emb.tolist())
            
        print(f"🔧 Adding {len(embeddings)} text embeddings (normalized)")
        
        # Prepare metadata (ChromaDB doesn't allow numpy arrays in metadata)
        metadatas = []
        documents = []
        
        for chunk in embedded_chunks:
            metadata = {
                'page_number': chunk['page_number'],
                'document_name': chunk['document_name'],
                'chunk_type': chunk['chunk_type'],
                'content_type': chunk['content_type']
            }
            # Add section_title if available
            if 'section_title' in chunk and chunk['section_title']:
                metadata['section_title'] = chunk['section_title'][:100]  # Truncate for metadata
            
            # Add all_sections if available (for enhanced section matching)
            if 'all_sections' in chunk and chunk['all_sections']:
                metadata['all_sections'] = ','.join(chunk['all_sections'])  # Store as comma-separated string
                #print(f"🔍 DEBUG: Storing all_sections in metadata: {metadata['all_sections']}")
            
            metadatas.append(metadata)
            documents.append(chunk['text'])
        
        # Add to ChromaDB
        self.text_collection.add(
            ids=ids,
            embeddings=embeddings,
            metadatas=metadatas,
            documents=documents
        )
        
        print(f"Added {len(embedded_chunks)} text chunks to vector store")
    
    def add_image_chunks(self, embedded_images: List[Dict[str, Any]]):
        """
        Add image chunks to the vector store.
        
        Args:
            embedded_images: List of embedded images
        """
        if not embedded_images:
            return
        
        ids = [img['id'] for img in embedded_images]
        # Always use image_embedding for consistency with existing collections
        embeddings = []
        for img in embedded_images:
            if 'image_embedding' in img:
                embeddings.append(img['image_embedding'].tolist())
            else:
                # This shouldn't happen, but fallback just in case
                raise ValueError(f"No image_embedding found for image {img.get('id', 'unknown')}")
        
        # Prepare metadata
        metadatas = []
        documents = []
        
        for img in embedded_images:
            metadata = {
                'page_number': img['page_number'],
                'document_name': img['document_name'],
                'caption': img['caption'],
                'ocr_text': img['ocr_text'],
                'content_type': img['content_type']
            }
            # Add section_title if available (always check, not just for rich context)
            if 'section_title' in img and img['section_title']:
                metadata['section_title'] = img['section_title'][:100]  # Truncate for metadata
            
            # Add rich context metadata if available
            if 'surrounding_text' in img:
                metadata.update({
                    'surrounding_text': img['surrounding_text'][:500],  # Truncate for metadata
                    'page_context': img['page_context'][:300] if 'page_context' in img else ''
                })
            
            metadatas.append(metadata)
            
            # Use rich context text if available, otherwise use combined_text
            document_text = img.get('rich_context_text', img.get('combined_text', ''))
            documents.append(document_text)
            
            # Store additional metadata and image object separately
            enhanced_metadata = {
                'page_number': img['page_number'],
                'document_name': img['document_name'],
                'caption': img['caption'],
                'ocr_text': img['ocr_text'],
                'combined_text': img.get('combined_text', ''),
                'text_embedding': img.get('text_embedding', img.get('simple_text_embedding', [])),
                'clip_text_embedding': img.get('clip_text_embedding', img.get('simple_clip_embedding', []))
            }
            # Add rich context data if available
            if 'rich_context_text' in img:
                enhanced_metadata.update({
                    'rich_context_text': img['rich_context_text'],
                    'rich_text_embedding': img['rich_text_embedding'].tolist() if 'rich_text_embedding' in img else [],
                    'rich_clip_embedding': img['rich_clip_embedding'].tolist() if 'rich_clip_embedding' in img else [],
                    'surrounding_text': img.get('surrounding_text', ''),
                    'section_title': img.get('section_title', ''),
                    'page_context': img.get('page_context', ''),
                    'preceding_text': img.get('preceding_text', ''),
                    'following_text': img.get('following_text', '')
                })
            
            # Convert embeddings to list for JSON serialization
            for key in ['text_embedding', 'clip_text_embedding', 'rich_text_embedding', 'rich_clip_embedding']:
                if key in enhanced_metadata and hasattr(enhanced_metadata[key], 'tolist'):
                    enhanced_metadata[key] = enhanced_metadata[key].tolist()
                    
            self.image_metadata[img['id']] = enhanced_metadata
            
            # Store PIL image object
            self.image_objects[img['id']] = img['image_object']
        
        # Add to ChromaDB
        self.image_collection.add(
            ids=ids,
            embeddings=embeddings,
            metadatas=metadatas,
            documents=documents
        )
        
        # Save metadata and objects
        self._save_image_metadata()
        self._save_image_objects()
        
        print(f"Added {len(embedded_images)} image chunks to vector store")
    
    def search_text(self, query_embedding: np.ndarray, top_k: int = 5, 
                   document_filter: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Search for similar text chunks.
        
        Args:
            query_embedding: Query embedding
            top_k: Number of results to return
            document_filter: Optional document name to filter by
            
        Returns:
            List of similar text chunks with metadata
        """
        where_clause = {}
        if document_filter:
            where_clause['document_name'] = document_filter
        
        results = self.text_collection.query(
            query_embeddings=[query_embedding.tolist()],
            n_results=top_k,
            where=where_clause if where_clause else None
        )
        
        # Format results
        formatted_results = []
        for i in range(len(results['ids'][0])):
            distance = results['distances'][0][i]
            similarity = max(0, 1 - distance)
            
            result = {
                'id': results['ids'][0][i],
                'text': results['documents'][0][i],
                'metadata': results['metadatas'][0][i],
                'distance': distance,
                'similarity_score': similarity,
                'content_type': 'text'
            }
            formatted_results.append(result)
        
        return formatted_results
    
    def search_images(self, query_embedding: np.ndarray, top_k: int = 5,
                     document_filter: Optional[str] = None,
                     page_filter: Optional[Dict] = None,
                     section_filter: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Search for similar images.
        
        Args:
            query_embedding: Query embedding (image embedding from CLIP)
            top_k: Number of results to return
            document_filter: Optional document name to filter by
            page_filter: Optional filter dict (e.g., {'page_number': 1})
            section_filter: Optional section title to filter by
            
        Returns:
            List of similar images with metadata
        """
        where_clause = {}
        
        # Build a list of conditions for the $and operator if multiple filters are present
        conditions = []
        
        if document_filter:
            conditions.append({"document_name": document_filter})
        
        if page_filter:
            conditions.append(page_filter)
        
        if section_filter:
            conditions.append({"section_title": section_filter})
        
        # Handle multiple filters with ChromaDB's format
        if len(conditions) > 1:
            where_clause = {"$and": conditions}
        elif len(conditions) == 1:
            where_clause = conditions[0]
        
        results = self.image_collection.query(
            query_embeddings=[query_embedding.tolist()],
            n_results=top_k,
            where=where_clause if where_clause else None
        )
        
        # Format results with additional metadata and image objects
        formatted_results = []
        for i in range(len(results['ids'][0])):
            image_id = results['ids'][0][i]
            
            result = {
                'id': image_id,
                'text': results['documents'][0][i],
                'metadata': results['metadatas'][0][i],
                'distance': results['distances'][0][i],
                'similarity_score': max(0, 1 - results['distances'][0][i]),  # Ensure non-negative
                'content_type': 'image'
            }
            
            # Add additional metadata if available
            if image_id in self.image_metadata:
                result.update(self.image_metadata[image_id])
            
            # Add image object if available
            if image_id in self.image_objects:
                result['image_object'] = self.image_objects[image_id]
            
            formatted_results.append(result)
        
        return formatted_results
    
    def search_images_by_section(self, query_embedding: np.ndarray, section_titles: List[str], 
                                top_k: int = 5, document_filter: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Search for images that belong to specific sections.
        
        Args:
            query_embedding: Query embedding (image embedding from CLIP)
            section_titles: List of section titles to filter by
            top_k: Number of results to return (maximum)
            document_filter: Optional document name to filter by
            
        Returns:
            List of images from the specified sections (may be less than top_k)
        """
        if not section_titles:
            return self.search_images(query_embedding, top_k, document_filter)
        
        # Search for images from each section and combine results
        all_section_results = []
        results_per_section = max(1, top_k // len(section_titles)) + 1  # Distribute top_k across sections
        
        for section_title in section_titles:
            # Use the new section_filter parameter for direct filtering
            section_results = self.search_images(
                query_embedding,
                results_per_section,
                document_filter,
                section_filter=section_title
            )
            
            # Add matched section info
            for result in section_results:
                result['matched_section'] = section_title
            
            all_section_results.extend(section_results)
        
        # Remove duplicates if any
        seen_ids = set()
        unique_results = []
        for result in all_section_results:
            result_id = result.get('id')
            if result_id and result_id not in seen_ids:
                seen_ids.add(result_id)
                unique_results.append(result)
        
        print(f"🔍 Section-based image search: Found {len(unique_results)} images from {len(section_titles)} sections")
        
        # Sort by similarity score and return up to top_k (may be less)
        unique_results.sort(key=lambda x: x.get('similarity_score', 0), reverse=True)
        return unique_results[:top_k]
    
    def search_multimodal(self, text_embedding: np.ndarray, image_embedding: np.ndarray,
                         top_k: int = 5, text_weight: float = 0.5,
                         document_filter: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Search for both text and images with weighted combination.
        
        Args:
            text_embedding: Text query embedding
            image_embedding: Image query embedding (from CLIP)
            top_k: Number of results to return
            text_weight: Weight for text results (0-1), image weight = 1 - text_weight
            document_filter: Optional document name to filter by
            
        Returns:
            Combined list of text and image results
        """
        # Get text and image results
        text_results = self.search_text(text_embedding, top_k * 2, document_filter)
        image_results = self.search_images(image_embedding, top_k * 2, document_filter)
        
        # Apply weights to similarity scores
        for result in text_results:
            result['weighted_score'] = result['similarity_score'] * text_weight
        
        for result in image_results:
            result['weighted_score'] = result['similarity_score'] * (1 - text_weight)
        
        # Combine and sort by weighted score
        combined_results = text_results + image_results
        combined_results.sort(key=lambda x: x['weighted_score'], reverse=True)
        
        return combined_results[:top_k]
    
    def get_document_list(self) -> List[str]:
        """Get list of all documents in the vector store."""
        # Get from text collection
        text_docs = set()
        try:
            text_results = self.text_collection.get()
            for metadata in text_results['metadatas']:
                text_docs.add(metadata['document_name'])
        except:
            pass
        
        # Get from image collection
        image_docs = set()
        try:
            image_results = self.image_collection.get()
            for metadata in image_results['metadatas']:
                image_docs.add(metadata['document_name'])
        except:
            pass
        
        return sorted(list(text_docs.union(image_docs)))
    
    def get_stats(self) -> Dict[str, Any]:
        """Get statistics about the vector store."""
        try:
            text_count = self.text_collection.count()
        except:
            text_count = 0
        
        try:
            image_count = self.image_collection.count()
        except:
            image_count = 0
        
        return {
            'total_text_chunks': text_count,
            'total_image_chunks': image_count,
            'total_documents': len(self.get_document_list()),
            'persist_directory': self.persist_directory
        }
    
    def delete_document(self, document_name: str):
        """
        Delete all chunks related to a specific document.
        
        Args:
            document_name: Name of the document to delete
        """
        # Delete from text collection
        try:
            text_results = self.text_collection.get(where={'document_name': document_name})
            if text_results['ids']:
                self.text_collection.delete(ids=text_results['ids'])
                print(f"Deleted {len(text_results['ids'])} text chunks for document: {document_name}")
        except Exception as e:
            print(f"Error deleting text chunks: {e}")
        
        # Delete from image collection
        try:
            image_results = self.image_collection.get(where={'document_name': document_name})
            if image_results['ids']:
                self.image_collection.delete(ids=image_results['ids'])
                
                # Also remove from metadata and objects
                for img_id in image_results['ids']:
                    if img_id in self.image_metadata:
                        del self.image_metadata[img_id]
                    if img_id in self.image_objects:
                        del self.image_objects[img_id]
                
                self._save_image_metadata()
                self._save_image_objects()
                
                print(f"Deleted {len(image_results['ids'])} image chunks for document: {document_name}")
        except Exception as e:
            print(f"Error deleting image chunks: {e}")
    
    def clear_all(self):
        """Clear all data from the vector store."""
        try:
            self.client.delete_collection("text_chunks")
            self.client.delete_collection("image_chunks")
            
            # Recreate collections
            self.text_collection = self._get_or_create_collection("text_chunks")
            self.image_collection = self._get_or_create_collection("image_chunks")
            
            # Clear metadata
            self.image_metadata = {}
            self.image_objects = {}
            self._save_image_metadata()
            self._save_image_objects()
            
            print("Cleared all data from vector store")
        except Exception as e:
            print(f"Error clearing vector store: {e}")