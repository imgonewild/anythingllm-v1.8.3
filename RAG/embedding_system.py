"""Embedding system for text and image content using CLIP and sentence transformers."""

import os
import numpy as np
from typing import List, Union, Dict, Any
import torch
from sentence_transformers import SentenceTransformer
from PIL import Image
import config
from document_processor import DocumentChunk, ImageData
import requests
import json

# Try to import CLIP, fall back to transformers if not available
try:
    import clip
    CLIP_AVAILABLE = True
except ImportError:
    print("Warning: CLIP not available, using transformers CLIP model")
    from transformers import CLIPProcessor, CLIPModel
    CLIP_AVAILABLE = False

class MultimodalEmbedder:
    """Handles embedding generation for both text and images."""
    
    def __init__(self):
        """Initialize the embedding models."""
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        print(f"Using device: {self.device}")
        
        # Load CLIP model for multimodal embeddings
        if CLIP_AVAILABLE:
            self.clip_model, self.clip_preprocess = clip.load("ViT-B/32", device=self.device)
            self.clip_dim = 512  # CLIP embedding dimension
        else:
            # Fallback to transformers CLIP
            self.clip_model = CLIPModel.from_pretrained("openai/clip-vit-base-patch32")
            self.clip_processor = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32")
            self.clip_model.to(self.device)
            self.clip_dim = 512
        
        # Load text embedding model based on provider
        if config.EMBEDDING_PROVIDER == "ollama":
            print("exception1")
            self.text_model = None  # We'll use Ollama API
            self.ollama_base_url = config.OLLAMA_BASE_URL
            self.text_embedding_model = config.TEXT_EMBEDDING_MODEL
            # Try to get embedding dimension from Ollama
            try:
                self.text_dim = self._get_ollama_embedding_dim()
            except:
                print("exception")
                self.text_dim = 384  # Default fallback
        else:
            print("exception2")
            # Use sentence transformers (HuggingFace)
            self.text_model = SentenceTransformer(config.TEXT_EMBEDDING_MODEL)
            self.text_dim = self.text_model.get_sentence_embedding_dimension()
        
        print(f"CLIP embedding dimension: {self.clip_dim}")
        print(f"Text embedding dimension: {self.text_dim}")
        print(f"Text embedding model dimension: {config.TEXT_EMBEDDING_MODEL}")
        print(f"Text embedding provider: {config.EMBEDDING_PROVIDER}")
    
    def _get_ollama_embedding_dim(self) -> int:
        """Get embedding dimension from Ollama model."""
        try:
            print(f"🔍 Testing Ollama API connection to {self.ollama_base_url} with model {self.text_embedding_model}")
            response = requests.post(
                f"{self.ollama_base_url}/api/embeddings",
                json={"model": self.text_embedding_model, "prompt": "test"},
                timeout=120
            )
            if response.status_code == 200:
                embedding = response.json().get("embedding", [])
                print(f"✅ Ollama API successful, embedding dimension: {len(embedding)}")
                return len(embedding)
            else:
                print(f"❌ Ollama API error {response.status_code}: {response.text}")
        except Exception as e:
            print(f"❌ Ollama API connection failed: {e}")
        
        print(f"⚠️ Falling back to default dimension 384")
        return 384  # Default fallback
    
    def _embed_text_ollama(self, texts: List[str]) -> np.ndarray:
        """Generate text embeddings using Ollama."""
        embeddings = []
        for i, text in enumerate(texts):
            try:
                response = requests.post(
                    f"{self.ollama_base_url}/api/embeddings",
                    json={"model": self.text_embedding_model, "prompt": text},
                    timeout=120
                )
                if response.status_code == 200:
                    embedding = response.json().get("embedding", [])
                    if embedding:
                        emb_array = np.array(embedding)
                        # Normalize the embedding vector
                        norm = np.linalg.norm(emb_array)
                        if norm > 0:
                            emb_array = emb_array / norm
                        embeddings.append(emb_array)
                        # Debug for first few embeddings
                        if i < 2:
                            print(f"🔧 Ollama embedding {i}: dim={len(embedding)}, norm={norm:.4f}, normalized_mean={np.mean(emb_array):.4f}")
                    else:
                        print(f"❌ Empty embedding from Ollama for text: {text[:50]}...")
                        embeddings.append(np.zeros(self.text_dim))
                else:
                    print(f"❌ Ollama API error {response.status_code}: {response.text}")
                    embeddings.append(np.zeros(self.text_dim))
            except Exception as e:
                print(f"❌ Error getting embedding from Ollama: {e}")
                embeddings.append(np.zeros(self.text_dim))
        
        result = np.array(embeddings)
        print(f"🔧 Final embeddings shape: {result.shape}")
        return result

    def embed_text(self, texts: Union[str, List[str]]) -> np.ndarray:
        """
        Generate embeddings for text using configured provider.
        
        Args:
            texts: Single text string or list of text strings
            
        Returns:
            Numpy array of embeddings
        """
        if isinstance(texts, str):
            texts = [texts]
        
        if config.EMBEDDING_PROVIDER == "ollama":
            return self._embed_text_ollama(texts)
        else:
            # Use sentence transformers (HuggingFace)
            embeddings = self.text_model.encode(texts, convert_to_numpy=True)
            return embeddings
    
    def embed_text_with_clip(self, texts: Union[str, List[str]]) -> np.ndarray:
        """
        Generate embeddings for text using CLIP (for multimodal alignment).
        
        Args:
            texts: Single text string or list of text strings
            
        Returns:
            Numpy array of embeddings
        """
        if isinstance(texts, str):
            texts = [texts]
        
        with torch.no_grad():
            if CLIP_AVAILABLE:
                # Use original CLIP
                text_tokens = clip.tokenize(texts).to(self.device)
                text_features = self.clip_model.encode_text(text_tokens)
            else:
                # Use transformers CLIP
                inputs = self.clip_processor(text=texts, return_tensors="pt", padding=True, truncation=True)
                inputs = {k: v.to(self.device) for k, v in inputs.items()}
                text_features = self.clip_model.get_text_features(**inputs)
            
            text_features = text_features / text_features.norm(dim=-1, keepdim=True)
        
        return text_features.cpu().numpy()
    
    def embed_images(self, images: Union[Image.Image, List[Image.Image]]) -> np.ndarray:
        """
        Generate embeddings for images using CLIP.
        
        Args:
            images: Single PIL Image or list of PIL Images
            
        Returns:
            Numpy array of embeddings
        """
        if isinstance(images, Image.Image):
            images = [images]
        
        with torch.no_grad():
            if CLIP_AVAILABLE:
                # Use original CLIP
                image_tensors = torch.stack([self.clip_preprocess(img) for img in images]).to(self.device)
                image_features = self.clip_model.encode_image(image_tensors)
            else:
                # Use transformers CLIP
                inputs = self.clip_processor(images=images, return_tensors="pt")
                inputs = {k: v.to(self.device) for k, v in inputs.items()}
                image_features = self.clip_model.get_image_features(**inputs)
            
            image_features = image_features / image_features.norm(dim=-1, keepdim=True)
        
        return image_features.cpu().numpy()
    
    def embed_document_chunks(self, chunks: List[DocumentChunk]) -> List[Dict[str, Any]]:
        """
        Embed document chunks and return with metadata.
        
        Args:
            chunks: List of DocumentChunk objects
            
        Returns:
            List of dictionaries containing embeddings and metadata
        """
        embedded_chunks = []
        
        # Extract texts
        texts = [chunk.text for chunk in chunks]
        
        # Generate embeddings
        text_embeddings = self.embed_text(texts)
        clip_text_embeddings = self.embed_text_with_clip(texts)
        
        for i, chunk in enumerate(chunks):
            embedded_chunk = {
                'id': chunk.chunk_id,
                'text': chunk.text,
                'page_number': chunk.page_number,
                'document_name': chunk.document_name,
                'chunk_type': chunk.chunk_type,
                'text_embedding': text_embeddings[i],
                'clip_text_embedding': clip_text_embeddings[i],
                'content_type': 'text'
            }
            # Add section_title if available
            if hasattr(chunk, 'section_title') and chunk.section_title:
                embedded_chunk['section_title'] = chunk.section_title
            
            # Add all_sections if available
            if hasattr(chunk, 'all_sections') and chunk.all_sections:
                embedded_chunk['all_sections'] = chunk.all_sections
                print(f"🔍 DEBUG: Added all_sections to chunk {chunk.chunk_id}: {chunk.all_sections}")
            else:
                print(f"⚠️ DEBUG: No all_sections for chunk {chunk.chunk_id}")
            
            embedded_chunks.append(embedded_chunk)
        
        return embedded_chunks
    
    def embed_images_with_metadata(self, images: List[ImageData]) -> List[Dict[str, Any]]:
        """
        Embed images and return with metadata.
        
        Args:
            images: List of ImageData objects
            
        Returns:
            List of dictionaries containing embeddings and metadata
        """
        embedded_images = []
        
        if not images:
            return embedded_images
        
        # Extract PIL images
        pil_images = [img_data.image for img_data in images]
        
        # Generate image embeddings
        image_embeddings = self.embed_images(pil_images)
        
        # Also embed captions and OCR text if available
        captions = [img_data.caption for img_data in images]
        ocr_texts = [img_data.ocr_text for img_data in images]
        
        # Combine caption and OCR text for better searchability
        combined_texts = []
        for caption, ocr in zip(captions, ocr_texts):
            combined_text = f"{caption} {ocr}".strip()
            if not combined_text:
                combined_text = "image"  # fallback
            combined_texts.append(combined_text)
        
        caption_embeddings = self.embed_text(combined_texts)
        clip_caption_embeddings = self.embed_text_with_clip(combined_texts)
        
        for i, img_data in enumerate(images):
            embedded_image = {
                'id': img_data.image_id,
                'page_number': img_data.page_number,
                'document_name': img_data.document_name,
                'caption': img_data.caption,
                'ocr_text': img_data.ocr_text,
                'combined_text': combined_texts[i],
                'image_embedding': image_embeddings[i],
                'text_embedding': caption_embeddings[i],
                'clip_text_embedding': clip_caption_embeddings[i],
                'content_type': 'image',
                'image_object': img_data.image  # Keep reference to PIL image
            }
            
            # Add section_title and rich context if available
            if hasattr(img_data, 'section_title') and img_data.section_title:
                embedded_image['section_title'] = img_data.section_title
                
            # Add other rich context fields if available
            for context_field in ['surrounding_text', 'page_context', 'preceding_text', 'following_text']:
                if hasattr(img_data, context_field):
                    embedded_image[context_field] = getattr(img_data, context_field)
            
            embedded_images.append(embedded_image)
        
        return embedded_images
    
    def embed_query(self, query: str) -> Dict[str, np.ndarray]:
        """
        Embed a query for both text and image retrieval.
        
        Args:
            query: Query string
            
        Returns:
            Dictionary containing different types of embeddings
        """
        return {
            'text_embedding': self.embed_text(query)[0],
            'clip_text_embedding': self.embed_text_with_clip(query)[0]
        }
    
    def calculate_similarity(self, embedding1: np.ndarray, embedding2: np.ndarray) -> float:
        """
        Calculate cosine similarity between two embeddings.
        
        Args:
            embedding1: First embedding
            embedding2: Second embedding
            
        Returns:
            Cosine similarity score
        """
        # Normalize embeddings
        embedding1 = embedding1 / np.linalg.norm(embedding1)
        embedding2 = embedding2 / np.linalg.norm(embedding2)
        
        # Calculate cosine similarity
        similarity = np.dot(embedding1, embedding2)
        return float(similarity)
    
    def find_similar_content(self, query_embeddings: Dict[str, np.ndarray], 
                           content_embeddings: List[Dict[str, Any]], 
                           top_k: int = 5,
                           similarity_threshold: float = 0.7) -> List[Dict[str, Any]]:
        """
        Find similar content based on embeddings.
        
        Args:
            query_embeddings: Query embeddings
            content_embeddings: List of content with embeddings
            top_k: Number of top results to return
            similarity_threshold: Minimum similarity threshold
            
        Returns:
            List of similar content with similarity scores
        """
        results = []
        
        for content in content_embeddings:
            # Calculate similarity based on content type
            if content['content_type'] == 'text':
                # For text content, use text embeddings
                similarity = self.calculate_similarity(
                    query_embeddings['text_embedding'],
                    content['text_embedding']
                )
            else:  # image content
                # For image content, use CLIP embeddings for cross-modal search
                similarity = self.calculate_similarity(
                    query_embeddings['clip_text_embedding'],
                    content['image_embedding']
                )
                
                # Also check text similarity with caption/OCR
                text_similarity = self.calculate_similarity(
                    query_embeddings['text_embedding'],
                    content['text_embedding']
                )
                
                # Take the maximum of image and text similarity
                similarity = max(similarity, text_similarity)
            
            if similarity >= similarity_threshold:
                result = content.copy()
                result['similarity_score'] = similarity
                results.append(result)
        
        # Sort by similarity score
        results.sort(key=lambda x: x['similarity_score'], reverse=True)
        
        return results[:top_k]
    
    def get_embedding_stats(self) -> Dict[str, Any]:
        """Get statistics about the embedding models."""
        return {
            'device': self.device,
            'clip_model': 'ViT-B/32',
            'text_model': config.TEXT_EMBEDDING_MODEL,
            'clip_embedding_dim': self.clip_dim,
            'text_embedding_dim': self.text_dim
        }