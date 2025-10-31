"""Response generator for the multimodal RAG system."""

import os
from typing import List, Dict, Any, Optional, Tuple
from PIL import Image
import openai
from langchain.llms import OpenAI
from langchain.chat_models import ChatOpenAI
from langchain.schema import HumanMessage, SystemMessage
from langchain.prompts import PromptTemplate
import config
from ollama_client import OllamaClient

class MultimodalResponseGenerator:
    """Generates responses combining text and images from retrieved content."""
    
    def __init__(self):
        """Initialize the response generator."""
        self.provider = config.LLM_PROVIDER
        self.llm = None
        self.ollama_client = None
        
        # Initialize based on provider
        if self.provider == "openai" or (self.provider == "auto" and config.OPENAI_API_KEY):
            self._init_openai()
        elif self.provider == "ollama" or self.provider == "auto":
            self._init_ollama()
        
        if not self.llm and not self.ollama_client:
            print("Warning: No LLM provider available. Using mock responses.")
    
    def _init_openai(self):
        """Initialize OpenAI client."""
        if config.OPENAI_API_KEY:
            try:
                openai.api_key = config.OPENAI_API_KEY
                self.llm = ChatOpenAI(
                    model_name="gpt-3.5-turbo",
                    temperature=0.7,
                    openai_api_key=config.OPENAI_API_KEY
                )
                self.provider = "openai"
                print(f"✅ Using OpenAI GPT-3.5-turbo")
            except Exception as e:
                print(f"Failed to initialize OpenAI: {e}")
                self.llm = None
    
    def _init_ollama(self):
        """Initialize Ollama client."""
        try:
            self.ollama_client = OllamaClient()
            if self.ollama_client.is_available:
                # Ensure the model is available
                if self.ollama_client.ensure_model_available():
                    self.provider = "ollama"
                    print(f"✅ Using Ollama with model: {self.ollama_client.model}")
                else:
                    print(f"❌ Ollama model {self.ollama_client.model} not available")
                    self.ollama_client = None
            else:
                print("❌ Ollama server not available")
                self.ollama_client = None
        except Exception as e:
            print(f"Failed to initialize Ollama: {e}")
            self.ollama_client = None
        
        # System prompt for the RAG assistant
        self.system_prompt = """You are a helpful assistant that answers questions based on provided document content. 
        You have access to both text content and images from documents. 

        When answering:
        1. Use the provided text content to form your response
        2. Reference specific images when they are relevant to the the text content you reference.
        3. If images contain important information, mention what they show
        4. Each image should be annotated exactly once
        5. If images contain important information, mention what they show
        6. If you cannot find relevant information, say so clearly
        7. Always prioritize accuracy over completeness
        

        Format your response in a clear, helpful manner."""
        
        

        # Prompt template for generating responses
        self.response_template = PromptTemplate(
            input_variables=["query", "text_context", "image_context"],
            template="""Based on the following retrieved content, please answer the user's question.

User Question: {query}

Text Content:
{text_context}

Image Information:
{image_context}

Please provide a comprehensive answer based on the retrieved content. When referencing images, use the format [Image X] where X is the image number (1, 2, 3, etc.) to indicate where the image should be displayed inline with the text.

For example: "To connect to the server, open the dialog box [Image 1] and enter your credentials."

This will help users see the relevant images exactly where they are mentioned in the instructions."""
        )
    
    def generate_response(self, query: str, retrieved_results: List[Dict[str, Any]], max_images: int = None) -> Dict[str, Any]:
        """
        Generate a response based on query and retrieved results.
        
        Args:
            query: User's query
            retrieved_results: Results from the retrieval engine
            max_images: Maximum number of images to include in response (None for no limit)
            
        Returns:
            Dictionary containing the response and associated images
        """
        if not retrieved_results:
            return {
                'response': "I couldn't find any relevant information in the documents to answer your question.",
                'images': [],
                'sources': [],
                'confidence': 0.0
            }
        
        # Separate text and image results
        text_results = [r for r in retrieved_results if r.get('content_type') == 'text']
        image_results = [r for r in retrieved_results if r.get('content_type') == 'image']
        
        # Prepare context
        text_context = self._format_text_context(text_results, max_results=None)  # No limit on text context
        image_context = self._format_image_context(image_results, max_images=max_images)
        
        # Generate response using LLM
        if self.llm or self.ollama_client:
            response_text = self._generate_llm_response(query, text_context, image_context)
        else:
            response_text = self._generate_mock_response(query, text_context, image_context, max_images)
        
        # Collect relevant images
        relevant_images = self._collect_relevant_images(image_results, max_images)
        #print(response_text)
        # Process response to embed image references inline
        response_text, inline_images = self._embed_images_inline(response_text, relevant_images)
        print(inline_images)
        # Prepare sources
        sources = self._prepare_sources(retrieved_results)
        
        # Calculate confidence score
        confidence = self._calculate_confidence(retrieved_results)
        
        return {
            'response': response_text,
            'images': relevant_images,  # Keep for backward compatibility
            'inline_images': inline_images,  # New: images with their positions
            'sources': sources,
            'confidence': confidence,
            'query': query
        }
    
    def _format_text_context(self, text_results: List[Dict[str, Any]], max_results: int = None) -> str:
        """Format text results into context string."""
        if not text_results:
            return "No relevant text content found."
        
        # Use all results or limit based on max_results parameter
        results_to_process = text_results if max_results is None else text_results[:max_results]
        
        context_parts = []
        for i, result in enumerate(results_to_process, 1):
            metadata = result.get('metadata', {})
            document_name = metadata.get('document_name', 'Unknown')
            page_number = metadata.get('page_number', 'Unknown')
            similarity = result.get('similarity_score', 0)
            section_title = metadata.get('section_title', result.get('section_title', ''))
            

            context_part = f"""
                [Source {i}] From {document_name}, Page {page_number} (Relevance: {similarity:.2f})
                {result.get('text', result.get('documents', ''))}
                """
            if section_title:
                context_part += f"\nSection Title: {section_title}"

            context_parts.append(context_part)
        
        return "\n".join(context_parts)
    
    def _format_image_context(self, image_results: List[Dict[str, Any]], max_images: int = None) -> str:
        """Format image results into context string."""
        if not image_results:
            return "No relevant images found."
        
        # Use all results or limit based on max_images parameter
        results_to_process = image_results if max_images is None else image_results[:max_images]
        
        context_parts = []
        for i, result in enumerate(results_to_process, 1):
            metadata = result.get('metadata', {})
            document_name = metadata.get('document_name', 'Unknown')
            page_number = metadata.get('page_number', 'Unknown')
            caption = metadata.get('caption', result.get('caption', ''))
            ocr_text = metadata.get('ocr_text', result.get('ocr_text', ''))
            similarity = result.get('similarity_score', 0)
            surrounding_text = metadata.get('surrounding_text', result.get('ocr_text', ''))
            section_title = metadata.get('section_title', result.get('section_title', ''))

            image_info = f"[Image {i}] From {document_name}, Page {page_number} (Relevance: {similarity:.2f})"
            
            if section_title:
                image_info += f"\nSection Title: {section_title}"

            if caption:
                image_info += f"\nCaption: {caption}"
            
            if ocr_text:
                image_info += f"\nText in image: {ocr_text}"

            if surrounding_text:
                image_info += f"\nImage Context: {surrounding_text}"
            
            
            context_parts.append(image_info)
        
        return "\n\n".join(context_parts)
    
    def _generate_llm_response(self, query: str, text_context: str, image_context: str) -> str:
        """Generate response using LLM (OpenAI or Ollama)."""
        try:
            # Create the prompt
            prompt = self.response_template.format(
                query=query,
                text_context=text_context,
                image_context=image_context
            )

            #print(prompt)
            
            if self.provider == "openai" and self.llm:
                # Use OpenAI
                messages = [
                    SystemMessage(content=self.system_prompt),
                    HumanMessage(content=prompt)
                ]
                response = self.llm(messages)
                return response.content
                
            elif self.provider == "ollama" and self.ollama_client:
                # Use Ollama
                full_prompt = f"{self.system_prompt}\n\nUser: {prompt}\n\nAssistant:"
                print(full_prompt)
                response = self.ollama_client.generate(
                    prompt=full_prompt,
                    temperature=0.7,
                    max_tokens=1000
                )
                return response if response else self._generate_mock_response(query, text_context, image_context, max_images)
            
            else:
                return self._generate_mock_response(query, text_context, image_context, max_images)
            
        except Exception as e:
            print(f"Error generating LLM response: {e}")
            return self._generate_mock_response(query, text_context, image_context, max_images)
    
    def _generate_mock_response(self, query: str, text_context: str, image_context: str, max_images: int = None) -> str:
        """Generate a mock response when LLM is not available."""
        response_parts = [f"Based on the retrieved documents, here's what I found regarding '{query}':"]
        
        if "No relevant text content found." not in text_context:
            response_parts.append("\n## Step-by-Step Instructions:")
            
            # Extract and format text content more naturally
            text_lines = text_context.split('\n')
            step_content = []
            
            for line in text_lines:
                line = line.strip()
                if line and not line.startswith('[Source') and not line.startswith('From '):
                    # Clean up the line
                    if 'Page' in line and 'Relevance:' in line:
                        continue  # Skip metadata lines
                    step_content.append(line)
            
            if step_content:
                # Format as steps
                response_parts.append("\n1. **Connect to SQL Server**: " + step_content[0])
                if len(step_content) > 1:
                    response_parts.append("\n2. **Configure Settings**: " + step_content[1])
                if len(step_content) > 2:
                    response_parts.append("\n3. **Complete Setup**: " + step_content[2])
        
        if "No relevant images found." not in image_context:
            response_parts.append("\n## Visual Guide:")
            response_parts.append("The following images show the key steps in the process:")
            
            # Extract image descriptions and format them
            if "Caption:" in image_context:
                captions = []
                lines = image_context.split('\n')
                for line in lines:
                    if line.startswith("Caption:"):
                        caption = line.replace("Caption:", "").strip()
                        if caption and len(caption) > 10:  # Only meaningful captions
                            captions.append(caption)
                
                # Reference images in a more natural way with inline markers
                captions_to_process = captions if max_images is None else captions[:max_images]
                for i, caption in enumerate(captions_to_process, 1):
                    if "Step" in caption or "Figure" in caption:
                        response_parts.append(f"\n- **Step {i}**: {caption} [Image {i}]")
        
        return "\n".join(response_parts)
    
    def _collect_relevant_images(self, image_results: List[Dict[str, Any]], max_images: int = None) -> List[Dict[str, Any]]:
        """Collect and format relevant images for the response."""
        relevant_images = []
        
        # Use all provided images or limit based on max_images parameter
        images_to_process = image_results if max_images is None else image_results[:max_images]
        
        for result in images_to_process:
            image_data = {
                'id': result.get('id'),
                'caption': result.get('caption', result.get('metadata', {}).get('caption', '')),
                'page_number': result.get('metadata', {}).get('page_number', result.get('page_number')),
                'document_name': result.get('metadata', {}).get('document_name', result.get('document_name')),
                'similarity_score': result.get('similarity_score', 0),
                'ocr_text': result.get('ocr_text', result.get('metadata', {}).get('ocr_text', ''))
            }
            
            # Include the image object if available
            if 'image_object' in result:
                image_data['image_object'] = result['image_object']
            
            relevant_images.append(image_data)
        
        return relevant_images
    
    def _prepare_sources(self, retrieved_results: List[Dict[str, Any]]) -> List[Dict[str, str]]:
        """Prepare source information for citation."""
        sources = []
        seen_sources = set()
        
        for result in retrieved_results:
            metadata = result.get('metadata', {})
            document_name = metadata.get('document_name', 'Unknown')
            page_number = str(metadata.get('page_number', 'Unknown'))
            content_type = result.get('content_type', 'unknown')
            
            source_key = f"{document_name}_{page_number}_{content_type}"
            
            if source_key not in seen_sources:
                source = {
                    'document': document_name,
                    'page': page_number,
                    'type': content_type,
                    'relevance': f"{result.get('similarity_score', 0):.2f}"
                }
                sources.append(source)
                seen_sources.add(source_key)
        
        return sources[:5]  # Limit to top 5 sources
    
    def _calculate_confidence(self, retrieved_results: List[Dict[str, Any]]) -> float:
        """Calculate confidence score for the response."""
        if not retrieved_results:
            return 0.0
        
        # Get similarity scores
        similarity_scores = [r.get('similarity_score', 0) for r in retrieved_results]
        
        if not similarity_scores:
            return 0.0
        
        # Normalize similarity scores to 0-1 range
        # Since similarity can be negative, we need to map the range appropriately
        min_sim = min(similarity_scores)
        max_sim = max(similarity_scores)
        
        if max_sim == min_sim:
            # All similarities are the same
            normalized_scores = [0.5] * len(similarity_scores)
        else:
            # Normalize to 0-1 range
            normalized_scores = [(s - min_sim) / (max_sim - min_sim) for s in similarity_scores]
        
        # Calculate average normalized score
        avg_normalized = sum(normalized_scores) / len(normalized_scores)
        
        # Base confidence on the best result and average
        best_normalized = max(normalized_scores)
        base_confidence = (avg_normalized * 0.6) + (best_normalized * 0.4)
        
        # Boost confidence if we have both text and images (multimodal response)
        has_text = any(r.get('content_type') == 'text' for r in retrieved_results)
        has_images = any(r.get('content_type') == 'image' for r in retrieved_results)
        
        multimodal_boost = 0.15 if (has_text and has_images) else 0.0
        
        # Boost confidence if we have multiple relevant results
        result_count_boost = min(0.1, len(retrieved_results) * 0.02)
        
        # Final confidence score (0-1)
        confidence = min(1.0, base_confidence + multimodal_boost + result_count_boost)
        
        # Ensure minimum confidence if we found results
        confidence = max(0.2, confidence) if retrieved_results else 0.0
        
        return round(confidence, 2)
    
    def generate_summary_response(self, document_name: str, document_summary: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate a summary response for a document.
        
        Args:
            document_name: Name of the document
            document_summary: Document summary from retrieval engine
            
        Returns:
            Summary response
        """
        total_pages = document_summary.get('total_pages', 0)
        total_text_chunks = document_summary.get('total_text_chunks', 0)
        total_images = document_summary.get('total_images', 0)
        
        summary_text = f"""Document Summary for "{document_name}":

This document contains {total_pages} pages with {total_text_chunks} text sections and {total_images} images.

The document appears to be a comprehensive manual or guide with both textual information and visual aids to help explain concepts."""
        
        # Collect some sample images
        sample_images = []
        pages = document_summary.get('pages', {})
        
        for page_num in sorted(pages.keys())[:3]:  # First 3 pages
            page_data = pages[page_num]
            for img in page_data.get('images', [])[:1]:  # One image per page
                sample_images.append({
                    'id': img.get('id'),
                    'page_number': page_num,
                    'caption': img.get('metadata', {}).get('caption', ''),
                    'document_name': document_name
                })
        
        return {
            'response': summary_text,
            'images': sample_images,
            'sources': [{'document': document_name, 'page': 'All', 'type': 'summary'}],
            'confidence': 1.0,
            'query': f"Summary of {document_name}"
        }
    
    def format_response_for_display(self, response_data: Dict[str, Any]) -> str:
        """
        Format response for text display.
        
        Args:
            response_data: Response data from generate_response
            
        Returns:
            Formatted text response
        """
        formatted_response = response_data['response']
        
        # Add source information
        if response_data.get('sources'):
            formatted_response += "\n\n**Sources:**\n"
            for source in response_data['sources']:
                formatted_response += f"- {source['document']} (Page {source['page']}, {source['type']})\n"
        
        # Add confidence information
        confidence = response_data.get('confidence', 0)
        formatted_response += f"\n*Confidence: {confidence:.0%}*"
        
        # Add image information
        if response_data.get('images'):
            formatted_response += f"\n\n*This response includes {len(response_data['images'])} relevant image(s).*"
        
        return formatted_response
    
    def _embed_images_inline(self, response_text: str, relevant_images: List[Dict[str, Any]]) -> tuple:
        """
        Embed image references inline in the response text.
        
        Args:
            response_text: Generated response text
            relevant_images: List of relevant images
            
        Returns:
            Tuple of (modified_response_text, inline_images_list)
        """
        import re
        
        inline_images = []
        modified_response = response_text
        
        # Pattern to find image references in the text
        # Look for patterns like "Image 1", "Figure 1", "Step 1", etc.
        image_patterns = [
            r'(\[Image (\d+)\])',                    # "[Image 1]"
            r'(Image (\d+))',                        # "Image 1"
            r'(Figure (\d+))',                       # "Figure 1"
            r'(Figure — Step (\d+)[^.]*)',          # "Figure — Step 1 — Connect to Server"
            r'(see Figure[^.]*)',                    # "see Figure..."
            r'(as shown in Figure[^.]*)',            # "as shown in Figure..."
            r'(\(see Figure[^)]*\))',                # "(see Figure...)"
        ]
        
        # Create image placeholders
        for i, img_data in enumerate(relevant_images, 1):
            page_num = img_data.get('page_number', '?')
            doc_name = img_data.get('document_name', 'Unknown')
            
            # Try to find where this image should be placed
            placement_found = False
            
            # Look for specific mentions of this image
            for pattern in image_patterns:
                matches = re.finditer(pattern, modified_response, re.IGNORECASE)
                for match in matches:
                    matched_text = match.group(1)
                    
                    # Check if this might refer to our image
                    if self._is_image_reference_match(matched_text, img_data, i):
                        # Only create image info if we found a reference in the text
                        image_info = {
                            'id': img_data.get('id', f'image_{i}'),
                            'image_object': img_data.get('image_object'),
                            'caption': img_data.get('caption', ''),
                            'page_number': page_num,
                            'document_name': doc_name,
                            'similarity_score': img_data.get('similarity_score', 0),
                            'ocr_text': img_data.get('ocr_text', ''),
                            'position': None  # Will be set when we find where to place it
                        }
                        
                        # For explicit "[Image X]" references, replace directly
                        if matched_text.startswith('[Image') and matched_text.endswith(']'):
                            placeholder = f"\n\n[IMAGE_{i}_PLACEHOLDER]\n\n"
                            modified_response = modified_response.replace(matched_text, placeholder, 1)
                            image_info['position'] = match.start()
                        else:
                            # For other references, insert after the sentence
                            sentence_end = modified_response.find('.', match.end())
                            if sentence_end == -1:
                                sentence_end = modified_response.find('\n', match.end())
                            if sentence_end == -1:
                                sentence_end = match.end()
                            
                            placeholder = f"\n\n[IMAGE_{i}_PLACEHOLDER]\n\n"
                            modified_response = (modified_response[:sentence_end+1] + 
                                               placeholder + 
                                               modified_response[sentence_end+1:])
                            image_info['position'] = sentence_end + 1
                        
                        placement_found = True
                        break
                
                if placement_found:
                    break
            
            # Only add image if it was referenced in the text
            if placement_found:
                inline_images.append(image_info)
            # If not referenced, skip this image entirely
        
        return modified_response, inline_images
    
    def _is_image_reference_match(self, matched_text: str, img_data: Dict[str, Any], img_index: int) -> bool:
        """
        Check if a text reference matches an image.
        
        Args:
            matched_text: The matched text reference
            img_data: Image data
            img_index: Index of the image (1-based)
            
        Returns:
            True if this reference likely refers to this image
        """
        matched_text_lower = matched_text.lower()
        
        # Extract numbers from the matched text
        import re
        numbers = re.findall(r'\d+', matched_text)
        
        # Direct image index match (highest priority)
        if f"[image {img_index}]" in matched_text_lower:
            return True
        
        if f"image {img_index}" in matched_text_lower:
            return True
        
        # Check if the reference number matches the image index
        if numbers and int(numbers[0]) == img_index:
            return True
        
        # Check caption/content matching for "Figure — Step X" patterns
        caption = img_data.get('caption', '').lower()
        if caption and "figure" in matched_text_lower and "step" in matched_text_lower:
            # Extract step number from caption
            caption_numbers = re.findall(r'step\s*(\d+)', caption)
            text_numbers = re.findall(r'step\s*(\d+)', matched_text_lower)
            
            if caption_numbers and text_numbers:
                if caption_numbers[0] == text_numbers[0]:
                    return True
        
        # Check if the reference matches the image's page number
        if numbers and int(numbers[0]) == img_data.get('page_number', 0):
            return True
        
        # For generic references, match sequentially
        if not numbers and img_index <= 3:
            if any(keyword in matched_text_lower for keyword in ['figure', 'image', 'see', 'shown']):
                return True
        
        return False