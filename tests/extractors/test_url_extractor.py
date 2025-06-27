"""
Tests for URL extractor
"""
import unittest
import sys
import os

# Add the project root to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from src.file_whisper_lib.extractors.url_extractor import URLExtractor


class TestURLExtractor(unittest.TestCase):
    
    def test_extract_urls_from_text(self):
        """Test extracting URLs from text"""
        text = "Visit https://example.com or check http://test.org for more info"
        urls = URLExtractor.extract_urls_from_text(text)
        
        expected_urls = ["https://example.com", "http://test.org"]
        self.assertEqual(urls, expected_urls)
    
    def test_extract_urls_from_text_empty(self):
        """Test extracting URLs from empty text"""
        text = ""
        urls = URLExtractor.extract_urls_from_text(text)
        self.assertEqual(urls, [])


if __name__ == '__main__':
    unittest.main()