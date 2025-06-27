"""
Tests for utils module
"""
import unittest
import sys
import os

# Add the project root to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from src.file_whisper_lib.extractors.utils import encode_binary, decode_binary


class TestUtils(unittest.TestCase):
    
    def test_encode_decode_roundtrip(self):
        """Test that encode and decode are inverse operations"""
        original_texts = [
            "Simple ASCII text",
            "Unicode text with emojis",
            "",  # Empty string
        ]
        
        for original in original_texts:
            with self.subTest(text=original):
                # Encode then decode
                encoded = encode_binary(original)
                decoded = decode_binary(encoded)
                
                # Should get back the original
                self.assertEqual(decoded, original)


if __name__ == '__main__':
    unittest.main()