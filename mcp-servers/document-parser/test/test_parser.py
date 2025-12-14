#!/usr/bin/env python3
"""
Test script for Document Parser MCP
"""

import sys
import json
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'backend'))

from python.document_parser import DocumentParser


def test_parse_document():
    """Test basic document parsing"""
    print("=" * 60)
    print("TEST: Parse Document")
    print("=" * 60)
    
    parser = DocumentParser()
    
    # Find a test document
    test_file = Path(__file__).parent.parent.parent / 'backend' / 'uploads' / 'archive' / '2025' / '12' / 'proposal'
    docs = list(test_file.glob('*.docx'))
    
    if not docs:
        print("❌ No test documents found")
        return False
    
    doc_path = str(docs[0])
    print(f"📄 Testing with: {doc_path}\n")
    
    try:
        result = parser.parse_document(
            doc_path,
            extract_chapters=True,
            extract_images=False
        )
        
        print(f"✅ Filename: {result['filename']}")
        print(f"✅ Content length: {result['content_length']} chars")
        print(f"✅ Chapters found: {result.get('chapter_count', 0)}")
        print(f"✅ File size: {result['metadata']['size_mb']} MB")
        
        if result.get('chapters'):
            print(f"\n📚 First 3 chapters:")
            for ch in result['chapters'][:3]:
                print(f"   {ch['chapter_number']}. {ch['chapter_title']}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def test_extract_chapters():
    """Test chapter extraction from text"""
    print("\n" + "=" * 60)
    print("TEST: Extract Chapters from Text")
    print("=" * 60)
    
    test_content = """
第一章 项目概述

本项目旨在提供优质服务。

1.1 项目背景

项目背景说明...

1.2 项目目标

1.2.1 总体目标

总体目标说明...

1.2.2 具体目标

具体目标说明...

第二章 技术方案

技术方案详细说明。
"""
    
    parser = DocumentParser()
    
    try:
        chapters = parser.extract_chapters(test_content)
        
        print(f"✅ Extracted {len(chapters)} chapters\n")
        for ch in chapters:
            print(f"   [{ch['chapter_level']}] {ch['chapter_number']} - {ch['chapter_title']}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def test_get_document_info():
    """Test getting document info"""
    print("\n" + "=" * 60)
    print("TEST: Get Document Info")
    print("=" * 60)
    
    parser = DocumentParser()
    
    test_file = Path(__file__).parent.parent.parent / 'backend' / 'uploads' / 'archive' / '2025' / '12' / 'proposal'
    docs = list(test_file.glob('*.docx'))
    
    if not docs:
        print("❌ No test documents found")
        return False
    
    doc_path = str(docs[0])
    
    try:
        info = parser.get_document_info(doc_path)
        
        print(f"✅ Filename: {info['filename']}")
        print(f"✅ File type: {info['file_type']}")
        print(f"✅ Size: {info['size_mb']} MB")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def main():
    """Run all tests"""
    print("\n🧪 Document Parser MCP Test Suite\n")
    
    results = []
    
    results.append(("Parse Document", test_parse_document()))
    results.append(("Extract Chapters", test_extract_chapters()))
    results.append(("Get Document Info", test_get_document_info()))
    
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    for test_name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status}: {test_name}")
    
    total = len(results)
    passed = sum(1 for _, p in results if p)
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    return all(p for _, p in results)


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
