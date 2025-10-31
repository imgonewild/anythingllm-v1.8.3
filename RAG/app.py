"""Streamlit web interface for the multimodal RAG system."""

import streamlit as st
import os
import tempfile
from typing import List, Dict, Any
from PIL import Image
import base64
from io import BytesIO

from retrieval_engine import MultimodalRAGRetriever
from response_generator import MultimodalResponseGenerator
from ollama_client import OllamaClient
import config

# Configure page
st.set_page_config(
    page_title="Multimodal RAG System",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded"
)

@st.cache_resource
def initialize_rag_system():
    """Initialize the RAG system components."""
    try:
        retriever = MultimodalRAGRetriever()
        generator = MultimodalResponseGenerator()
        
        return retriever, generator
    except Exception as e:
        st.error(f"Error initializing RAG system: {e}")
        return None, None

def display_image(image_obj, caption="", max_width=300):
    """Display an image with caption."""
    if image_obj:
        st.image(image_obj, caption=caption, width=max_width)

def display_response_with_inline_images(response_text: str, inline_images: List[Dict[str, Any]]):
    """Display response text with images embedded inline."""
    import re
    
    # Split the response by image placeholders
    parts = re.split(r'\[IMAGE_(\d+)_PLACEHOLDER\]', response_text)
    
    for i, part in enumerate(parts):
        if part.strip():  # Skip empty parts
            if part.isdigit():  # This is an image placeholder number
                img_index = int(part) - 1  # Convert to 0-based index
                if 0 <= img_index < len(inline_images):
                    img_data = inline_images[img_index]
                    
                    # Display the image
                    if 'image_object' in img_data:
                        caption = f"📍 Page {img_data.get('page_number', '?')}"
                        if img_data.get('caption'):
                            clean_caption = img_data['caption'].replace('Image description (long):', '').strip()
                            if len(clean_caption) > 100:
                                clean_caption = clean_caption[:100] + "..."
                            caption += f": {clean_caption}"
                        
                        # Center the image
                        col1, col2, col3 = st.columns([1, 2, 1])
                        with col2:
                            display_image(img_data['image_object'], caption, max_width=400)
                            
                            # Add a small details expander
                            with st.expander(f"🔍 Image Details"):
                                st.write(f"**Document:** {img_data.get('document_name', 'Unknown')}")
                                st.write(f"**Page:** {img_data.get('page_number', 'Unknown')}")
                                st.write(f"**Relevance:** {img_data.get('similarity_score', 0):.1%}")
                                if img_data.get('ocr_text'):
                                    st.write(f"**Text in image:** {img_data['ocr_text'][:150]}...")
                    else:
                        st.warning("⚠️ Image could not be loaded")
            else:
                # This is text content
                if part.strip():
                    st.markdown(part)

def display_images_grid(images: List[Dict[str, Any]], enhanced_mode: bool = False):
    """Display images in a grid layout with enhanced context info."""
    cols = st.columns(min(len(images), 3))
    
    for i, img_data in enumerate(images):
        with cols[i % 3]:
            if 'image_object' in img_data:
                caption = f"Page {img_data.get('page_number', '?')}"
                if img_data.get('caption'):
                    clean_caption = img_data['caption'].replace('Image description (long):', '').strip()
                    if len(clean_caption) > 100:
                        clean_caption = clean_caption[:100] + "..."
                    caption += f": {clean_caption}"
                
                display_image(img_data['image_object'], caption)
                
                # Show additional info with enhanced context
                with st.expander(f"🔍 Image {i+1} Details"):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.write(f"**📄 Document:** {img_data.get('document_name', 'Unknown')}")
                        st.write(f"**📍 Page:** {img_data.get('page_number', 'Unknown')}")
                        st.write(f"**📊 Relevance:** {img_data.get('similarity_score', 0):.3f}")
                        
                        # Enhanced info
                        if enhanced_mode and 'context_boost' in img_data:
                            st.write(f"**🎯 Context Boost:** +{img_data['context_boost']:.3f}")
                        if 'best_match_method' in img_data:
                            st.write(f"**🔍 Best Match:** {img_data['best_match_method']}")
                    
                    with col2:
                        if img_data.get('section_title'):
                            st.write(f"**📖 Section:** {img_data['section_title'][:50]}...")
                        
                        if enhanced_mode and img_data.get('all_similarities'):
                            st.write("**🎯 All Similarities:**")
                            for method, score in img_data['all_similarities'].items():
                                st.write(f"  • {method}: {score:.3f}")
                    
                    # OCR and context text
                    if img_data.get('ocr_text'):
                        st.write(f"**📝 Text in image:** {img_data['ocr_text'][:200]}...")
                    
                    if enhanced_mode:
                        if img_data.get('surrounding_text'):
                            st.write("**📄 Surrounding Context:**")
                            st.text(img_data['surrounding_text'][:300] + "...")
                        
                        if img_data.get('rich_context_text'):
                            st.write("**🧠 Rich Context:**")
                            st.text(img_data['rich_context_text'][:400] + "...")
            else:
                st.warning(f"Image {i+1}: Could not load image data")


def format_sources(sources: List[Dict[str, str]]) -> str:
    """Format sources for display."""
    if not sources:
        return "No sources available"
    
    formatted = []
    for i, source in enumerate(sources, 1):
        formatted.append(
            f"{i}. **{source['document']}** (Page {source['page']}) - "
            f"{source['type']} (Relevance: {source['relevance']})"
        )
    
    return "\n".join(formatted)

def main():
    """Main application function."""
    st.title("📚 Enhanced Multimodal RAG System")
    st.markdown("*Upload documents with images and ask questions to get answers with relevant visual context*")
    
    # Initialize system
    retriever, generator = initialize_rag_system()
    
    if not all([retriever, generator]):
        st.error("Failed to initialize the RAG system. Please check your configuration.")
        return
    
    # Sidebar for system management
    with st.sidebar:
        st.header("📁 Document Management")
        
        # File upload
        uploaded_files = st.file_uploader(
            "Upload Documents",
            type=['pdf', 'docx', 'doc', 'txt'],
            accept_multiple_files=True,
            help="Supported formats: PDF, DOCX, DOC, TXT"
        )
        
        # Chunking strategy selection
        chunking_strategy = st.selectbox(
            "📄 Chunking Strategy",
            options=["page", "section"],
            index=0,  # Default to "page"
            help="Choose how to split documents:\n"
                 "• Page: Split by page boundaries (default)\n"
                 "• Section: Split by document sections/chapters (better for structured docs)"
        )
        
        if uploaded_files:
            if st.button("🚀 Process Documents", type="primary"):
                process_enhanced_documents_unified(uploaded_files, retriever, chunking_strategy)
        
        st.divider()
        
        # Document list
        st.subheader("📋 Ingested Documents")
        
        # Get documents from unified system
        all_documents = retriever.list_documents()
        
        if all_documents:
            for doc in all_documents:
                col1, col2 = st.columns([3, 1])
                
                with col1:
                    st.text(f"🚀 {doc}")
                
                with col2:
                    if st.button("🗑️", key=f"delete_{doc}", help="Delete document"):
                        retriever.delete_document(doc)
                        st.rerun()
        else:
            st.info("No documents uploaded yet")
        
        st.divider()
        
        # System stats
        st.subheader("📊 System Stats")
        
        # Unified system stats
        stats = retriever.get_stats()
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Text Chunks", stats['vector_store']['total_text_chunks'])
        
        with col2:
            st.metric("Images", stats['vector_store']['total_image_chunks'])
            
        with col3:
            st.metric("Documents", stats['vector_store']['total_documents'])
        
        # LLM Provider status
        st.divider()
        st.subheader("🤖 LLM Provider")
        
        # Check Ollama status
        ollama_client = OllamaClient()
        if ollama_client.is_available:
            st.success(f"🟢 Ollama: Connected")
            st.write(f"**Model**: {ollama_client.model}")
            
            # Show available models
            models = ollama_client.list_models()
            if models:
                model_names = [model.get('name', 'Unknown') for model in models]
                st.write(f"**Available**: {', '.join(model_names[:3])}{'...' if len(model_names) > 3 else ''}")
        else:
            st.error("🔴 Ollama: Not connected")
            st.write("Make sure Ollama is running: `ollama serve`")
        
        # OpenAI status
        if config.OPENAI_API_KEY:
            st.success("🟢 OpenAI: API key configured")
        else:
            st.warning("🟡 OpenAI: No API key")
        
        st.write(f"**Current provider**: {config.LLM_PROVIDER}")
        
        # Clear all data
        if st.button("🗑️ Clear All Data", type="secondary"):
            if st.session_state.get('confirm_clear'):
                # Clear unified system
                retriever.clear_all_documents()
                
                st.session_state.confirm_clear = False
                st.success("All data cleared!")
                st.rerun()
            else:
                st.session_state.confirm_clear = True
                st.warning("Click again to confirm deletion of ALL data")
    
    # Main query interface
    st.header("🔍 Ask Questions")
    
    # Get documents from unified system
    all_documents = retriever.list_documents()
    
    # Query input
    query = st.text_input(
        "Enter your question:",
        placeholder="e.g., How do I install the software? What does the diagram show?",
        help="Ask questions about your uploaded documents. The system will find relevant text and images."
    )
    
    # Query options
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        search_mode = st.selectbox(
            "Search Mode",
            ["enhanced", "hybrid", "text", "image"],
            help="Enhanced: Two-stage contextual search with rich context, Hybrid: Search both text and images, Text: Text only, Image: Images only"
        )
    
    with col2:
        include_images = st.checkbox(
            "Include Images in Response",
            value=True,
            help="Whether to include relevant images in the response"
        )
    
    with col3:
        enhanced_context = st.checkbox(
            "Enhanced Context",
            value=True,
            help="Show detailed context information for images"
        )
    
    with col4:
        document_filter = st.selectbox(
            "Filter by Document",
            ["All Documents"] + all_documents,
            help="Search within a specific document only"
        )
        
        if document_filter == "All Documents":
            document_filter = None
    
    # Enhanced mode settings
    if search_mode == "enhanced":
        with st.expander("🔧 Enhanced Search Settings"):
            col1, col2, col3 = st.columns(3)
            with col1:
                text_top_k = st.slider("Text Results", 5, 20, 10, help="Number of text results in stage 1")
            with col2:
                image_top_k = st.slider("Image Results", 1, 10, 3, help="Number of image results to return")
            with col3:
                similarity_threshold = st.slider("Similarity Threshold", 0.0, 1.0, 0.1, 0.05, help="Minimum similarity score")
    else:
        text_top_k, image_top_k, similarity_threshold = 10, 5, 0.1
    
    # Process query
    if query and st.button("🚀 Search", type="primary"):
        with st.spinner("Searching for relevant information..."):
            # Use unified retrieval system with enhanced features
            search_results = retriever.query(
                query_text=query,
                search_mode=search_mode,
                top_k= image_top_k,
                include_images=include_images,
                document_filter=document_filter,
                use_enhanced_search=(search_mode == "enhanced"),
                text_top_k=text_top_k,
                similarity_threshold=similarity_threshold
            )
            
            if search_results['total_results'] > 0:
                # Display enhanced search results if using enhanced mode
                if search_mode == "enhanced" and 'stats' in search_results:
                    st.subheader("🎯 Enhanced Search Results")
                    
                    # Search statistics
                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        st.metric("Search Strategy", search_results.get('search_strategy', 'enhanced'))
                    with col2:
                        st.metric("Text Candidates", search_results['stats']['text_candidates'])
                    with col3:
                        st.metric("Image Results", search_results['stats']['image_candidates'])
                    with col4:
                        st.metric("Pages Covered", search_results['stats']['context_pages'])
                    
                    # Show enhanced query if different
                    if search_results.get('enhanced_query') != query:
                        with st.expander("🔧 Enhanced Query"):
                            enhanced_query = search_results['enhanced_query']
                            display_query = enhanced_query[:500] + "..." if len(enhanced_query) > 500 else enhanced_query
                            st.code(display_query)
                    
                    # Display text results
                    if search_results.get('text_results'):
                        st.subheader("📝 Relevant Text Context")
                        for i, result in enumerate(search_results['text_results'][:5], 1):
                            similarity = result.get('similarity_score', 0)
                            with st.expander(f"Text Result {i} (Similarity: {similarity:.3f})"):
                                metadata = result.get('metadata', {})
                                st.write(f"**📄 Document:** {metadata.get('document_name', 'Unknown')}")
                                st.write(f"**📍 Page:** {metadata.get('page_number', 'Unknown')}")
                                
                                # Display section information for text chunks
                                sections_str = metadata.get('all_sections', '')
                                if sections_str:
                                    sections = sections_str.split(',') if isinstance(sections_str, str) else []
                                    if sections:
                                        st.write(f"**📑 Sections:** {' → '.join(sections)}")
                                elif metadata.get('section_title'):
                                    st.write(f"**📑 Section:** {metadata.get('section_title')}")
                                
                                st.write(f"**📝 Content:**")
                                text_content = result.get('text', '')
                                display_text = text_content[:500] + "..." if len(text_content) > 500 else text_content
                                st.write(display_text)
                    
                    # Display image results with enhanced context
                    if search_results.get('image_results'):
                        st.subheader("🖼️ Contextually Relevant Images")
                        
                        # Prepare image data for display
                        image_data_for_display = []
                        for result in search_results['image_results']:
                            metadata = result.get('metadata', {})
                            img_display_data = {
                                'image_object': result.get('image_object'),
                                'document_name': metadata.get('document_name'),
                                'page_number': metadata.get('page_number'),
                                'caption': metadata.get('caption', ''),
                                'ocr_text': metadata.get('ocr_text', ''),
                                'similarity_score': result.get('similarity_score', 0),
                                'section_title': metadata.get('section_title', ''),
                                'surrounding_text': metadata.get('surrounding_text', ''),
                                'rich_context_text': metadata.get('rich_context_text', ''),
                                'context_boost': result.get('context_boost', 0)
                            }
                            image_data_for_display.append(img_display_data)
                        
                        display_images_grid(image_data_for_display, enhanced_mode=True)
                
                #print(f"-------{str(image_top_k)}----------")


                # Generate and display response for all modes
                with st.spinner("Generating response..."):
                    response_data = generator.generate_response(query, search_results['results'], max_images=image_top_k)
            
                # Display response
                display_response(response_data)
                
                # Display search results details
                display_search_results(search_results['results'])
            
            else:
                st.warning("No relevant information found for your query.")
    
    # Example queries
    if not all_documents:
        st.info("👆 Upload some documents first to start asking questions!")
    else:
        st.subheader("💡 Example Questions")
        example_queries = [
            "How do I get started?",
            "What are the system requirements?",
            "Show me the installation process",
            "What does the architecture diagram show?",
            "How do I troubleshoot common issues?"
        ]
        
        cols = st.columns(len(example_queries))
        for i, example in enumerate(example_queries):
            with cols[i]:
                if st.button(example, key=f"example_{i}"):
                    st.session_state.query_input = example

def process_enhanced_documents_unified(uploaded_files, retriever, chunking_strategy="page"):
    """Process uploaded files with enhanced context extraction using unified system."""
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    results = []
    
    for i, uploaded_file in enumerate(uploaded_files):
        strategy_emoji = "📄" if chunking_strategy == "page" else "📚"
        status_text.text(f"🚀 Processing ({chunking_strategy}): {uploaded_file.name}... {strategy_emoji}")
        
        # Save uploaded file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(uploaded_file.name)[1]) as tmp_file:
            tmp_file.write(uploaded_file.getvalue())
            tmp_file_path = tmp_file.name
        
        try:
            # Process the document with enhanced context
            result = retriever.ingest_document(tmp_file_path, chunking_strategy)
            results.append(result)
            
        except Exception as e:
            st.error(f"Error processing {uploaded_file.name}: {e}")
            results.append({
                'document_name': uploaded_file.name,
                'status': 'error',
                'error': str(e)
            })
        
        finally:
            # Clean up temporary file
            os.unlink(tmp_file_path)
        
        # Update progress
        progress_bar.progress((i + 1) / len(uploaded_files))
    
    # Display results
    status_text.empty()
    progress_bar.empty()
    
    success_count = sum(1 for r in results if r['status'] == 'success')
    error_count = len(results) - success_count
    
    if success_count > 0:
        strategy_label = "📄 page-based" if chunking_strategy == "page" else "📚 section-based"
        st.success(f"✅ Successfully processed {success_count} document(s) with {strategy_label} chunking")
        
        # Show processing details
        with st.expander("Processing Details"):
            for result in results:
                if result['status'] == 'success':
                    st.write(f"**{result['document_name']}**: "
                            f"{result['text_chunks']} text chunks ({chunking_strategy}), "
                            f"{result['images']} images with rich context")
    
    if error_count > 0:
        st.error(f"❌ Failed to process {error_count} document(s)")
        
        with st.expander("Error Details"):
            for result in results:
                if result['status'] == 'error':
                    st.write(f"**{result['document_name']}**: {result.get('error', 'Unknown error')}")

def process_uploaded_files(uploaded_files, retriever, chunking_strategy="page"):
    """Legacy function - redirects to unified processing."""
    return process_enhanced_documents_unified(uploaded_files, retriever, chunking_strategy)

def display_response(response_data: Dict[str, Any]):
    """Display the generated response with inline images."""
    st.subheader("🤖 Response")
    
    # Display confidence
    confidence = response_data.get('confidence', 0)
    confidence_color = "green" if confidence > 0.7 else "orange" if confidence > 0.4 else "red"
    st.markdown(f"**Confidence:** :{confidence_color}[{confidence:.0%}]")
    
    # Check if we have inline images
    inline_images = response_data.get('inline_images', [])
    response_text = response_data.get('response', '')
    
    if inline_images and '[IMAGE_' in response_text:
        # Display response with inline images
        display_response_with_inline_images(response_text, inline_images)
    else:
        # Fallback to original method
        st.markdown(response_text)
        
        # Display images at bottom if no inline placement
        images = response_data.get('images', [])
        if images:
            st.subheader("🖼️ Relevant Images")
            display_images_grid(images)
    
    # Display sources
    sources = response_data.get('sources', [])
    if sources:
        with st.expander("📚 Sources"):
            st.markdown(format_sources(sources))

def display_search_results(results: List[Dict[str, Any]]):
    """Display detailed search results."""
    with st.expander(f"🔍 Search Results ({len(results)} items)"):
        
        for i, result in enumerate(results):
            st.markdown(f"### Result {i+1}")
            
            col1, col2 = st.columns([3, 1])
            
            with col1:
                content_type = result.get('content_type', 'unknown')
                st.markdown(f"**Type:** {content_type.title()}")
                
                metadata = result.get('metadata', {})
                st.markdown(f"**Document:** {metadata.get('document_name', 'Unknown')}")
                st.markdown(f"**Page:** {metadata.get('page_number', 'Unknown')}")
                
                # Display section information for both text and images
                if content_type == 'text':
                    # Check for all_sections (text chunks)
                    sections_str = metadata.get('all_sections', '')
                    if sections_str:
                        sections = sections_str.split(',') if isinstance(sections_str, str) else []
                        if sections:
                            st.markdown(f"**📑 Sections:** {' → '.join(sections)}")
                    elif metadata.get('section_title'):
                        st.markdown(f"**📑 Section:** {metadata.get('section_title')}")
                    
                    st.markdown("**Content:**")
                    st.text(result.get('text', metadata.get('text', ''))[:500] + "...")
                else:
                    # For images, also show section if available
                    if metadata.get('section_title'):
                        st.markdown(f"**📑 Section:** {metadata.get('section_title')}")
                    
                    st.markdown(f"**Caption:** {metadata.get('caption', 'No caption')}")
                    if metadata.get('ocr_text'):
                        st.markdown(f"**OCR Text:** {metadata.get('ocr_text', '')[:200]}...")
            
            with col2:
                similarity = result.get('similarity_score', 0)
                st.metric("Similarity", f"{similarity:.2f}")
                
                if content_type == 'image' and 'image_object' in result:
                    display_image(result['image_object'], "", max_width=150)
            
            st.divider()

if __name__ == "__main__":
    main()