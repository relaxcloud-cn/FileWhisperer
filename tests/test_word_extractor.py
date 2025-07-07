#!/usr/bin/env python3
"""
Test script for the refactored word extractor
"""

import os
import sys
sys.path.insert(0, 'src')

from file_whisper_lib.extractors.word_extractor import WordExtractor
from file_whisper_lib.dt import Node, File, Data, Meta
from file_whisper_lib.types import Types


def test_word_extractor():
    """Test the refactored word extractor with password-protected files"""
    
    # Test files
    test_files = [
        {
            'path': 'tests/fixtures/docx_pwd_123456.docx',
            'type': Types.DOCX,
            'passwords': ['123456', 'wrong_password']
        },
        {
            'path': 'tests/fixtures/doc_pwd_123456.doc',
            'type': Types.DOC,
            'passwords': ['123456', 'wrong_password']
        }
    ]
    
    for test_file in test_files:
        print(f"\n--- Testing {test_file['path']} ---")
        
        # Check if file exists
        if not os.path.exists(test_file['path']):
            print(f"❌ File not found: {test_file['path']}")
            continue
        
        # Read file content
        with open(test_file['path'], 'rb') as f:
            file_content = f.read()
        
        # Create node
        node = Node()
        node.type = test_file['type']
        node.passwords = test_file['passwords']
        node.word_max_pages = 10
        node.meta = Meta()
        
        # Create file object
        file_obj = File(
            path=test_file['path'],
            name=os.path.basename(test_file['path']),
            content=file_content
        )
        node.content = file_obj
        
        try:
            # Extract content
            result_nodes = WordExtractor.extract_word_file(node)
            
            print(f"✅ Successfully processed {test_file['path']}")
            print(f"   Extracted {len(result_nodes)} nodes")
            print(f"   Is encrypted: {node.meta.map_bool.get('is_encrypted', False)}")
            
            # Print extracted content
            for i, result_node in enumerate(result_nodes):
                if isinstance(result_node.content, Data):
                    content = result_node.content.content.decode('utf-8') if result_node.content.content else ''
                    print(f"   Node {i}: {result_node.content.type} - {len(content)} chars")
                    if content and len(content) > 0:
                        preview = content[:100].replace('\n', ' ')
                        print(f"   Preview: {preview}...")
                elif isinstance(result_node.content, File):
                    print(f"   Node {i}: FILE - {result_node.content.name} ({len(result_node.content.content)} bytes)")
                    # Print content preview if it's text-like
                    try:
                        content_text = result_node.content.content.decode('utf-8')
                        if content_text and len(content_text) > 0:
                            preview = content_text[:100].replace('\n', ' ')
                            print(f"   File Content Preview: {preview}...")
                    except (UnicodeDecodeError, AttributeError):
                        print(f"   File Content: Binary data, not displayable as text")
                    
        except Exception as e:
            print(f"❌ Error processing {test_file['path']}: {str(e)}")
            import traceback
            traceback.print_exc()


if __name__ == "__main__":
    test_word_extractor()