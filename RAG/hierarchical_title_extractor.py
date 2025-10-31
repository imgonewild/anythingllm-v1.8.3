"""
Hierarchical Title Extractor for processing numbered section titles.
Extracts and manages document structure with numbered titles (1., 1.1, 1.1.1 format).
"""

import re
from typing import List, Dict, Any, Optional, Tuple
import fitz  # PyMuPDF


class HierarchicalTitleExtractor:
    """
    Extractor for numbered section titles in documents.
    
    Handles three levels of sections:
    - Major: 1. Introduction
    - Medium: 1.1 Background  
    - Minor: 1.1.1 Deep Learning Basics
    """
    
    def __init__(self):
        self.section_index = {}  # section_number -> section_info
        self.title_hierarchy = {
            'major': {},    # 1. -> section_info
            'medium': {},   # 1.1 -> section_info  
            'minor': {}     # 1.1.1 -> section_info
        }
        self.page_to_sections = {}  # page_number -> [section_info]
        
    def extract_numbered_title(self, text: str) -> Optional[Dict[str, Any]]:
        """
        Extract numbered section title from text line.
        
        Args:
            text: Text line potentially containing a numbered title
            
        Returns:
            Dictionary with title info or None if no title found
            
        Examples:
            "1. Introduction" -> {'number': '1', 'title': 'Introduction', 'level': 'major', 'full_title': '1.Introduction'}
            "1.1 Background" -> {'number': '1.1', 'title': 'Background', 'level': 'medium', 'full_title': '1.1.Background'}
        """
        text = text.strip()
        
        # Try minor sections first (most specific): "1.1.1 Title"
        minor_pattern = r'^(\d+)\.(\d+)\.(\d+)\.?\s+(.+?)(?:\n|$)'
        minor_match = re.match(minor_pattern, text)
        
        if minor_match:
            major_num = minor_match.group(1)
            medium_num = minor_match.group(2)
            minor_num = minor_match.group(3)
            title = minor_match.group(4).strip()
            
            number = f"{major_num}.{medium_num}.{minor_num}"
            return {
                'number': number,
                'title': title,
                'level': 'minor',
                'full_title': f"{number} {title}",  # Keep full text for context (e.g., "3.2.1 Enter output roll data")
                'hierarchy_path': [major_num, medium_num, minor_num]
            }
        
        # Try medium sections: "1.1 Title"  
        medium_pattern = r'^(\d+)\.(\d+)\.?\s+(.+?)(?:\n|$)'
        medium_match = re.match(medium_pattern, text)
        
        if medium_match:
            major_num = medium_match.group(1)
            minor_num = medium_match.group(2)
            title = medium_match.group(3).strip()
            
            number = f"{major_num}.{minor_num}"
            return {
                'number': number,
                'title': title,
                'level': 'medium',
                'full_title': f"{number} {title}",  # Keep full text for context (e.g., "3.2 Report New Roll")
                'hierarchy_path': [major_num, minor_num]
            }
        
        # Try major sections: "1. Title" or "1 Title"
        major_pattern = r'^(\d+)\.?\s+(.+?)(?:\n|$)'
        major_match = re.match(major_pattern, text)
        
        if major_match:
            number = major_match.group(1)
            title = major_match.group(2).strip()
            
            return {
                'number': number,
                'title': title,
                'level': 'major',
                'full_title': f"{number}. {title}",  # Include dot for major sections (e.g., "1. Application entry point")
                'hierarchy_path': [number]
            }
        
        return None
    
    def build_document_section_index(self, pdf_document) -> Dict[str, Any]:
        """
        Build complete section index for the document.
        
        Args:
            pdf_document: PyMuPDF document object
            
        Returns:
            Dictionary containing the complete section hierarchy
        """
        print("📚 Building document section index...")
        
        for page_num in range(len(pdf_document)):
            page = pdf_document[page_num]
            text_blocks = page.get_text("dict")
            
            page_sections = []
            
            for block in text_blocks.get("blocks", []):
                if "lines" in block:
                    for line in block["lines"]:
                        line_text = ""
                        for span in line.get("spans", []):
                            line_text += span.get("text", "")
                        
                        # Try to extract numbered title
                        title_info = self.extract_numbered_title(line_text)
                        if title_info:
                            # Add position information (convert to 1-based page numbering)
                            title_info['page_number'] = page_num + 1
                            title_info['y_position'] = block.get('bbox', [0,0,0,0])[1]
                            
                            # Store in hierarchy
                            level = title_info['level']
                            number = title_info['number']
                            full_title = title_info['full_title']
                            
                            self.title_hierarchy[level][number] = title_info
                            self.section_index[full_title] = title_info
                            page_sections.append(title_info)
                            
                            print(f"   📍 P{page_num}: [{level}] {full_title}")
            
            # Store page sections mapping (use 1-based page numbering)
            if page_sections:
                self.page_to_sections[page_num + 1] = page_sections
        
        # Build parent-child relationships
        self._build_section_relationships()
        
        print(f"✅ Built section index with {len(self.section_index)} sections")
        return self.title_hierarchy
    
    def _build_section_relationships(self):
        """Build parent-child relationships between sections."""
        # For medium sections, find their parent major sections
        for medium_num, medium_info in self.title_hierarchy['medium'].items():
            parent_num = medium_info['hierarchy_path'][0]
            parent_key = f"{parent_num}.{self.title_hierarchy['major'].get(parent_num, {}).get('title', '')}"
            
            if parent_key in self.section_index:
                medium_info['parent'] = parent_key
                # Add to parent's children
                if 'children' not in self.section_index[parent_key]:
                    self.section_index[parent_key]['children'] = []
                self.section_index[parent_key]['children'].append(medium_info['full_title'])
        
        # For minor sections, find their parent medium sections
        for minor_num, minor_info in self.title_hierarchy['minor'].items():
            path = minor_info['hierarchy_path']
            parent_num = f"{path[0]}.{path[1]}"
            
            # Find parent medium section
            parent_medium = self.title_hierarchy['medium'].get(parent_num)
            if parent_medium:
                parent_key = parent_medium['full_title']
                minor_info['parent'] = parent_key
                # Add to parent's children
                if 'children' not in self.section_index[parent_key]:
                    self.section_index[parent_key]['children'] = []
                self.section_index[parent_key]['children'].append(minor_info['full_title'])
    
    def analyze_chunk_sections(self, chunk_text: str, chunk_start_pos: int, 
                             previous_chunk_sections: List[str] = None) -> List[str]:
        """
        Analyze which sections a text chunk belongs to.
        
        Args:
            chunk_text: The text content of the chunk
            chunk_start_pos: Starting position in the document
            previous_chunk_sections: Sections from the previous chunk (optimization)
            
        Returns:
            List of section full_titles that this chunk belongs to
            
        Example:
            Returns: ['1.Introduction', '1.1.Background', '1.1.1.DeepLearning']
        """
        sections_found = []
        
        # Method 1: Check if chunk starts with a section title
        first_line = chunk_text.split('\n')[0].strip()
        title_info = self.extract_numbered_title(first_line)
        
        print(f"🔍 DEBUG: First line: '{first_line[:50]}...', title_info: {title_info}")
        
        if title_info:
            # Chunk starts with a section title
            starting_section = title_info['full_title']
            sections_found.append(starting_section)
            print(f"🔍 DEBUG: Method 1 - chunk starts with title: {starting_section}")
            
            # Find any additional sections in the chunk
            lines = chunk_text.split('\n')[1:]  # Skip first line
            for line in lines:
                additional_title = self.extract_numbered_title(line)
                if additional_title:
                    sections_found.append(additional_title['full_title'])
        else:
            # Method 2: Chunk doesn't start with section title
            print(f"🔍 DEBUG: Method 2 - chunk doesn't start with title")
            print(f"🔍 DEBUG: previous_chunk_sections: {previous_chunk_sections}")
            
            # Optimized: Use previous chunk's last section if available
            if previous_chunk_sections:
                prior_section = previous_chunk_sections[-1]  # Last section from previous chunk
                print(f"🔍 DEBUG: Using previous chunk's last section: {prior_section}")
                sections_found.append(prior_section)
            else:
                # Fallback: Find the most recent section before this chunk position
                print(f"🔍 DEBUG: Fallback to _find_prior_section")
                prior_section = self._find_prior_section(chunk_start_pos)
                if prior_section:
                    sections_found.append(prior_section)
            
            # Check for any section titles within the chunk
            for line in chunk_text.split('\n'):
                title_info = self.extract_numbered_title(line)
                if title_info:
                    sections_found.append(title_info['full_title'])
        
        # Remove duplicates while preserving order
        unique_sections = []
        for section in sections_found:
            if section not in unique_sections:
                unique_sections.append(section)
        
        print(f"🔍 DEBUG: analyze_chunk_sections found: {unique_sections}")
        return unique_sections
    
    def _find_prior_section(self, chunk_start_pos: int) -> Optional[str]:
        """
        Find the most recent section title before the given position.
        
        Args:
            chunk_start_pos: Position in document
            
        Returns:
            Full title of the most recent section, or None
        """
        # This is a simplified implementation
        # In practice, you'd need to maintain position information for sections
        # For now, we'll use a heuristic based on page numbers
        
        # Find all sections and their positions, return the closest one before chunk_start_pos
        prior_sections = []
        for section_title, section_info in self.section_index.items():
            # Approximate position based on page number and y_position
            page_num = section_info.get('page_number', 0)
            y_pos = section_info.get('y_position', 0)
            estimated_pos = page_num * 10000 + y_pos
            if estimated_pos < chunk_start_pos:
                prior_sections.append((estimated_pos, section_title))
        
        if prior_sections:
            # Return the section closest to (but before) the chunk
            prior_sections.sort(key=lambda x: x[0], reverse=True)
            return prior_sections[0][1]
        
        return None
    
    def get_section_info(self, section_full_title: str) -> Optional[Dict[str, Any]]:
        """
        Get detailed information about a section.
        
        Args:
            section_full_title: Full title like "1.Introduction"
            
        Returns:
            Section information dictionary or None
        """
        return self.section_index.get(section_full_title)
    
    def get_all_sections(self) -> List[str]:
        """
        Get all section full titles in the document.
        
        Returns:
            List of all section full titles
        """
        return list(self.section_index.keys())
    
    def get_image_section(self, page_number: int, image_y_position: Optional[float] = None) -> Optional[str]:
        """
        Get the single section that an image belongs to.
        
        Args:
            page_number: Page number (1-based)
            image_y_position: Y position of image on page (optional)
            
        Returns:
            Section full_title that this image belongs to, or None if no section found
        """
        # Method 1: Find sections on current page
        if page_number in self.page_to_sections:
            page_sections = self.page_to_sections[page_number]
            
            if image_y_position is not None:
                # Find the section above the image position
                best_section = None
                for section in page_sections:
                    section_y = section.get('y_position', 0)
                    if section_y <= image_y_position:
                        best_section = section
                    else:
                        break  # Section is below image
                
                if best_section:
                    return best_section['full_title']
                # If no section found above image, continue to check previous pages
            else:
                # If no y_position available, we cannot safely determine
                # which sections are above/below the image on current page
                # So skip to checking previous pages
                pass
        
        # Method 2: Look for sections on previous pages (only backwards)
        for prev_page in range(page_number - 1, -1, -1):
            if prev_page in self.page_to_sections:
                page_sections = self.page_to_sections[prev_page]
                if page_sections:
                    # Use the last section from the previous page
                    return page_sections[-1]['full_title']
        
        # No sections found - image is in document prologue
        print(f"⚠️ Image on page {page_number} has no preceding section")
        return None
    
    def _extract_section_title_from_page(self, page) -> str:
        """
        Legacy function for backward compatibility.
        Now uses the numbered title extraction.
        
        Args:
            page: PyMuPDF page object
            
        Returns:
            Section title found on the page
        """
        try:
            text_dict = page.get_text("dict")
            
            # Try numbered title extraction first
            for block in text_dict.get("blocks", []):
                if "lines" in block:
                    for line in block["lines"]:
                        line_text = ""
                        for span in line.get("spans", []):
                            line_text += span.get("text", "")
                        
                        title_info = self.extract_numbered_title(line_text)
                        if title_info:
                            return title_info['full_title']
            
            # Fallback to original logic
            for block in text_dict.get("blocks", []):
                if "lines" in block:
                    for line in block["lines"]:
                        for span in line.get("spans", []):
                            text = span.get("text", "").strip()
                            size = span.get("size", 0)
                            flags = span.get("flags", 0)
                            
                            if text and (size > 12 or flags & 16):
                                if len(text) < 100 and not text.endswith('.'):
                                    return text
            
            return ""
        except:
            return ""