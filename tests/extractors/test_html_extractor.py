"""
Tests for HTML extractor
"""
import unittest
import sys
import os
from unittest.mock import Mock, patch

# Add the project root to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from src.file_whisper_lib.extractors.html_extractor import HTMLExtractor
from src.file_whisper_lib.dt import Node, File, Data


class TestHTMLExtractor(unittest.TestCase):
    
    def test_extract_text_from_html_simple(self):
        """Test extracting text from simple HTML"""
        html = "<p>Hello <strong>World</strong></p>"
        result = HTMLExtractor.extract_text_from_html(html)
        self.assertEqual(result, "Hello World")
    
    def test_extract_text_from_html_complex(self):
        """Test extracting text from complex HTML"""
        html = """
        <html>
            <head><title>Test Title</title></head>
            <body>
                <h1>Header</h1>
                <p>Paragraph with <a href="#">link</a> inside.</p>
                <div>
                    <p>Another paragraph.</p>
                </div>
            </body>
        </html>
        """
        result = HTMLExtractor.extract_text_from_html(html)
        self.assertIn("Test Title", result)
        self.assertIn("Header", result)
        self.assertIn("Paragraph with link inside.", result)
    
    def test_extract_text_from_html_empty(self):
        """Test extracting text from empty HTML"""
        html = ""
        result = HTMLExtractor.extract_text_from_html(html)
        self.assertEqual(result, "")
    
    def test_extract_urls_from_html_basic(self):
        """Test extracting URLs from basic HTML tags"""
        html = '''
        <a href="https://example.com">Link</a>
        <img src="image.jpg" alt="Image">
        <script src="script.js"></script>
        '''
        urls = HTMLExtractor.extract_urls_from_html(html)
        
        expected_urls = ["https://example.com", "image.jpg", "script.js"]
        for url in expected_urls:
            self.assertIn(url, urls)
    
    def test_extract_urls_from_html_srcset(self):
        """Test extracting URLs from srcset attribute"""
        html = '<img srcset="image1.jpg 1x, image2.jpg 2x" alt="Image">'
        urls = HTMLExtractor.extract_urls_from_html(html)
        
        self.assertIn("image1.jpg", urls)
        self.assertIn("image2.jpg", urls)
    
    def test_extract_urls_from_html_meta_tags(self):
        """Test extracting URLs from meta tags"""
        html = '''
        <meta property="og:image" content="social-image.jpg">
        <meta http-equiv="refresh" content="5;url=redirect.html">
        '''
        urls = HTMLExtractor.extract_urls_from_html(html)
        
        self.assertIn("social-image.jpg", urls)
        self.assertIn("redirect.html", urls)
    
    def test_extract_urls_from_html_data_src(self):
        """Test extracting URLs from data-src attributes (lazy loading)"""
        html = '<img data-src="lazy-image.jpg" alt="Lazy Image">'
        urls = HTMLExtractor.extract_urls_from_html(html)
        
        self.assertIn("lazy-image.jpg", urls)
    
    def test_extract_urls_from_html_svg(self):
        """Test extracting URLs from SVG image tags"""
        html = '''
        <svg>
            <image xlink:href="svg-image.jpg" />
            <image href="svg-image2.jpg" />
        </svg>
        '''
        urls = HTMLExtractor.extract_urls_from_html(html)
        
        self.assertIn("svg-image.jpg", urls)
        self.assertIn("svg-image2.jpg", urls)
    
    def test_extract_urls_from_html_css_inline(self):
        """Test extracting URLs from inline CSS"""
        html = '''
        <div style="background-image: url('bg-image.jpg');">Content</div>
        <style>
            .bg { background: url("css-bg.png"); }
        </style>
        '''
        urls = HTMLExtractor.extract_urls_from_html(html)
        
        self.assertIn("bg-image.jpg", urls)
        self.assertIn("css-bg.png", urls)
    
    def test_extract_img_from_html_base64(self):
        """Test extracting base64 images from HTML"""
        base64_data = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg=="
        html = f'<img src="data:image/png;base64,{base64_data}" alt="Base64 Image">'
        
        images = HTMLExtractor.extract_img_from_html(html)
        
        self.assertEqual(len(images), 1)
        self.assertIsInstance(images[0], bytes)
    
    def test_extract_img_from_html_no_base64(self):
        """Test that non-base64 images are ignored"""
        html = '<img src="regular-image.jpg" alt="Regular Image">'
        
        images = HTMLExtractor.extract_img_from_html(html)
        
        self.assertEqual(len(images), 0)
    
    def test_extract_img_from_html_invalid_base64(self):
        """Test handling of invalid base64 data"""
        html = '<img src="data:image/png;base64,invalid-data" alt="Invalid Base64">'
        
        images = HTMLExtractor.extract_img_from_html(html)
        
        self.assertEqual(len(images), 0)
    
    @patch('src.file_whisper_lib.extractors.utils.decode_binary')
    @patch('src.file_whisper_lib.extractors.utils.encode_binary')
    def test_extract_html_with_file_node(self, mock_encode, mock_decode):
        """Test extracting HTML from a File node"""
        mock_decode.return_value = "<p>Test HTML content</p>"
        mock_encode.side_effect = lambda x: x.encode('utf-8')
        
        # Create a File node
        node = Node()
        node.content = File(content=b"<p>Test HTML content</p>")
        node.pdf_max_pages = 10
        node.word_max_pages = 10
        
        result_nodes = HTMLExtractor.extract_html(node)
        
        # Should create at least one text node
        self.assertGreater(len(result_nodes), 0)
        
        # First node should contain extracted text
        text_node = result_nodes[0]
        self.assertIsInstance(text_node.content, Data)
        self.assertEqual(text_node.content.type, "TEXT")
        self.assertEqual(text_node.prev, node)
    
    @patch('src.file_whisper_lib.extractors.utils.decode_binary')
    @patch('src.file_whisper_lib.extractors.utils.encode_binary')
    def test_extract_html_with_data_node(self, mock_encode, mock_decode):
        """Test extracting HTML from a Data node"""
        mock_decode.return_value = "<p>Test HTML content</p>"
        mock_encode.side_effect = lambda x: x.encode('utf-8')
        
        # Create a Data node
        node = Node()
        node.content = Data(type="HTML", content=b"<p>Test HTML content</p>")
        node.pdf_max_pages = 10
        node.word_max_pages = 10
        
        result_nodes = HTMLExtractor.extract_html(node)
        
        # Should create at least one text node
        self.assertGreater(len(result_nodes), 0)
        
        # Check that limits are inherited
        for result_node in result_nodes:
            self.assertEqual(result_node.pdf_max_pages, 10)
            self.assertEqual(result_node.word_max_pages, 10)
    
    @patch('src.file_whisper_lib.extractors.utils.decode_binary')
    @patch('src.file_whisper_lib.extractors.utils.encode_binary')
    def test_extract_html_with_urls_and_images(self, mock_encode, mock_decode):
        """Test extracting HTML with URLs and base64 images"""
        html_content = '''
        <html>
            <body>
                <p>Test content</p>
                <a href="https://example.com">Link</a>
                <img src="data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg==" alt="Test">
            </body>
        </html>
        '''
        mock_decode.return_value = html_content
        mock_encode.side_effect = lambda x: x.encode('utf-8')
        
        node = Node()
        node.content = File(content=html_content.encode('utf-8'))
        node.pdf_max_pages = 10
        node.word_max_pages = 10
        
        result_nodes = HTMLExtractor.extract_html(node)
        
        # Should have text node, URL node, and image node
        self.assertGreaterEqual(len(result_nodes), 3)
        
        # Check for different types of nodes
        node_types = [type(node.content).__name__ for node in result_nodes]
        self.assertIn('Data', node_types)  # Text and URL nodes
        self.assertIn('File', node_types)  # Image nodes
    
    @patch('src.file_whisper_lib.extractors.html_extractor.logger')
    def test_extract_html_error_handling(self, mock_logger):
        """Test error handling in extract_html"""
        # Create a node that will cause an error
        node = Node()
        node.content = File(content=None)  # This should cause an error
        
        result_nodes = HTMLExtractor.extract_html(node)
        
        # Should return empty list on error
        self.assertEqual(len(result_nodes), 0)
        
        # Should log the error
        mock_logger.error.assert_called()


if __name__ == '__main__':
    unittest.main()