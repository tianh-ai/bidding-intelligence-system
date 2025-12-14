"""
Document Parser - Python Backend for MCP Server
Provides document parsing, chapter extraction, and image extraction
"""

import os
import sys
from pathlib import Path
from typing import Dict, List, Optional, Any
import json

# Import existing parsing engines
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'backend'))

from engines.parse_engine import ParseEngine
from engines.parse_engine_v2 import EnhancedChapterExtractor
from engines.image_extractor import ImageExtractor


class DocumentParser:
    """Main document parser class for MCP"""
    
    def __init__(self):
        self.parse_engine = ParseEngine()
        self.chapter_extractor = EnhancedChapterExtractor()
        self.image_extractor = ImageExtractor()
    
    def parse_document(
        self,
        file_path: str,
        extract_chapters: bool = True,
        extract_images: bool = False,
        ocr_enabled: bool = False
    ) -> Dict[str, Any]:
        """
        Parse a document and extract content, chapters, and optionally images
        
        Args:
            file_path: Path to PDF or DOCX file
            extract_chapters: Whether to extract chapter structure
            extract_images: Whether to extract images
            ocr_enabled: Enable OCR for scanned PDFs
            
        Returns:
            Dict containing:
                - filename: str
                - content: str (full text)
                - chapters: List[Dict] (if extract_chapters=True)
                - images: List[Dict] (if extract_images=True)
                - metadata: Dict
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
        
        file_ext = os.path.splitext(file_path)[1].lower()
        if file_ext not in ['.pdf', '.docx', '.doc']:
            raise ValueError(f"Unsupported file format: {file_ext}")
        
        # Extract text content
        if file_ext == '.pdf':
            content = self.parse_engine._parse_pdf(file_path)
        else:
            content = self.parse_engine._parse_docx(file_path)
        
        result = {
            'filename': os.path.basename(file_path),
            'file_path': file_path,
            'content': content,
            'content_length': len(content),
            'file_type': file_ext[1:],
        }
        
        # Extract chapters if requested
        if extract_chapters:
            chapters = self.chapter_extractor.extract_chapters(content)
            result['chapters'] = chapters
            result['chapter_count'] = len(chapters)
        
        # Extract images if requested
        if extract_images:
            import uuid
            file_id = str(uuid.uuid4())
            year = 2025  # Current year
            
            if file_ext == '.pdf':
                images = self.image_extractor.extract_from_pdf(file_path, file_id, year)
            else:
                images = self.image_extractor.extract_from_docx(file_path, file_id, year)
            
            result['images'] = images
            result['image_count'] = len(images)
        
        # Get file metadata
        file_stat = os.stat(file_path)
        result['metadata'] = {
            'size_bytes': file_stat.st_size,
            'size_mb': round(file_stat.st_size / 1024 / 1024, 2),
            'modified_time': file_stat.st_mtime,
        }
        
        return result
    
    def extract_chapters(
        self,
        content: str,
        patterns: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """
        Extract chapter structure from text content
        
        Args:
            content: Document text content
            patterns: Optional custom regex patterns
            
        Returns:
            List of chapter dictionaries
        """
        chapters = self.chapter_extractor.extract_chapters(content)
        
        return [
            {
                'chapter_number': ch.get('chapter_number', ''),
                'chapter_title': ch.get('chapter_title', ch.get('title', '')),
                'chapter_level': ch.get('chapter_level', ch.get('level', 1)),
                'content': ch.get('content', ''),
                'content_length': len(ch.get('content', '')),
                'position': ch.get('position_order', i),
            }
            for i, ch in enumerate(chapters, 1)
        ]
    
    def extract_images(
        self,
        file_path: str,
        output_dir: str,
        format: str = 'png'
    ) -> List[Dict[str, Any]]:
        """
        Extract all images from a document
        
        Args:
            file_path: Path to document
            output_dir: Directory to save images
            format: Output format (png/jpeg)
            
        Returns:
            List of extracted image information
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
        
        os.makedirs(output_dir, exist_ok=True)
        
        import uuid
        file_id = str(uuid.uuid4())
        year = 2025
        
        # Temporarily override storage base
        old_base = self.image_extractor.storage_base
        self.image_extractor.storage_base = Path(output_dir)
        
        try:
            file_ext = os.path.splitext(file_path)[1].lower()
            if file_ext == '.pdf':
                images = self.image_extractor.extract_from_pdf(file_path, file_id, year)
            else:
                images = self.image_extractor.extract_from_docx(file_path, file_id, year)
            
            return images
        finally:
            self.image_extractor.storage_base = old_base
    
    def get_document_info(self, file_path: str) -> Dict[str, Any]:
        """
        Get basic document information without parsing content
        
        Args:
            file_path: Path to document
            
        Returns:
            Document metadata
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
        
        file_stat = os.stat(file_path)
        file_ext = os.path.splitext(file_path)[1].lower()
        
        info = {
            'filename': os.path.basename(file_path),
            'file_path': file_path,
            'file_type': file_ext[1:],
            'size_bytes': file_stat.st_size,
            'size_mb': round(file_stat.st_size / 1024 / 1024, 2),
            'modified_time': file_stat.st_mtime,
        }
        
        # Get page count for PDF
        if file_ext == '.pdf':
            try:
                from pypdf import PdfReader
                reader = PdfReader(file_path)
                info['page_count'] = len(reader.pages)
            except Exception as e:
                info['page_count'] = None
                info['error'] = str(e)
        
        return info


# CLI interface for testing
if __name__ == '__main__':
    import argparse
    
    parser_cli = argparse.ArgumentParser(description='Document Parser CLI')
    parser_cli.add_argument('command', choices=['parse', 'chapters', 'images', 'info'])
    parser_cli.add_argument('file_path', help='Path to document file')
    parser_cli.add_argument('--output-dir', help='Output directory for images')
    parser_cli.add_argument('--ocr', action='store_true', help='Enable OCR')
    
    args = parser_cli.add_argument('--extract-images', action='store_true')
    
    args = parser_cli.parse_args()
    
    parser = DocumentParser()
    
    if args.command == 'parse':
        result = parser.parse_document(
            args.file_path,
            extract_chapters=True,
            extract_images=args.extract_images,
            ocr_enabled=args.ocr
        )
        print(json.dumps(result, ensure_ascii=False, indent=2))
    
    elif args.command == 'chapters':
        with open(args.file_path, 'r') as f:
            content = f.read()
        chapters = parser.extract_chapters(content)
        print(json.dumps(chapters, ensure_ascii=False, indent=2))
    
    elif args.command == 'images':
        if not args.output_dir:
            print("Error: --output-dir required for image extraction")
            sys.exit(1)
        images = parser.extract_images(args.file_path, args.output_dir)
        print(json.dumps(images, ensure_ascii=False, indent=2))
    
    elif args.command == 'info':
        info = parser.get_document_info(args.file_path)
        print(json.dumps(info, ensure_ascii=False, indent=2))
