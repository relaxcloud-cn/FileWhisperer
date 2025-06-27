"""
Tests for PDF extractor
"""
import unittest
import sys
import os
from unittest.mock import Mock, patch, MagicMock
from io import BytesIO

# Add the project root to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from src.file_whisper_lib.extractors.pdf_extractor import PDFExtractor
from src.file_whisper_lib.dt import Node, File, Data


class TestPDFExtractor(unittest.TestCase):
    
    def setUp(self):
        """Set up test fixtures"""
        self.test_pdf_data = b"fake_pdf_data"
        self.test_page_text = "This is test page content"
        self.test_image_data = b"fake_image_data"
    
    @patch('src.file_whisper_lib.extractors.pdf_extractor.fitz')
    @patch('src.file_whisper_lib.extractors.utils.encode_binary')
    def test_extract_pdf_file_success(self, mock_encode, mock_fitz):
        """Test successful PDF extraction without password"""
        # Mock PDF document
        mock_pdf = MagicMock()
        mock_pdf.needs_pass = False
        mock_pdf.__len__ = Mock(return_value=2)  # 2 pages
        
        # Mock pages
        mock_page1 = MagicMock()
        mock_page1.get_text.return_value = "Page 1 content"
        mock_page1.get_images.return_value = []
        
        mock_page2 = MagicMock()
        mock_page2.get_text.return_value = "Page 2 content"
        mock_page2.get_images.return_value = []
        
        mock_pdf.load_page.side_effect = [mock_page1, mock_page2]
        mock_fitz.open.return_value = mock_pdf
        
        # Mock encode_binary
        mock_encode.return_value = b"Page 1 contentPage 2 content"
        
        # Create a File node
        node = Node()
        node.content = File(content=self.test_pdf_data)
        node.pdf_max_pages = 10
        node.passwords = []
        
        result_nodes = PDFExtractor.extract_pdf_file(node)
        
        # Should create one text node (no images in this test)
        self.assertEqual(len(result_nodes), 1)
        
        text_node = result_nodes[0]
        self.assertIsInstance(text_node.content, Data)
        self.assertEqual(text_node.content.type, "TEXT")
        self.assertEqual(text_node.prev, node)
        
        # Verify PDF was opened correctly
        mock_fitz.open.assert_called_once()
        
        # Verify both pages were processed
        self.assertEqual(mock_pdf.load_page.call_count, 2)
        
        # Verify is_encrypted meta was set
        self.assertFalse(node.meta.map_bool["is_encrypted"])
    
    @patch('src.file_whisper_lib.extractors.pdf_extractor.fitz')
    @patch('src.file_whisper_lib.extractors.utils.encode_binary')
    def test_extract_pdf_file_with_images(self, mock_encode, mock_fitz):
        """Test PDF extraction with images"""
        # Mock PDF document
        mock_pdf = MagicMock()
        mock_pdf.needs_pass = False
        mock_pdf.__len__ = Mock(return_value=1)
        
        # Mock image data
        mock_image_info = (123, 0, 0, 0, 0, 0, 0, 0)  # xref is the first element
        mock_base_image = {"image": self.test_image_data}
        mock_pdf.extract_image.return_value = mock_base_image
        
        # Mock page with images
        mock_page = MagicMock()
        mock_page.get_text.return_value = "Page with image"
        mock_page.get_images.return_value = [mock_image_info]
        
        mock_pdf.load_page.return_value = mock_page
        mock_fitz.open.return_value = mock_pdf
        
        # Mock encode_binary
        mock_encode.return_value = b"Page with image"
        
        node = Node()
        node.content = File(content=self.test_pdf_data)
        node.pdf_max_pages = 10
        node.passwords = []
        
        result_nodes = PDFExtractor.extract_pdf_file(node)
        
        # Should create text node + image node
        self.assertEqual(len(result_nodes), 2)
        
        # Check image node
        image_node = result_nodes[0]
        self.assertIsInstance(image_node.content, File)
        self.assertEqual(image_node.content.content, self.test_image_data)
        self.assertEqual(image_node.content.name, "page_1_image_1.png")
        
        # Check text node
        text_node = result_nodes[1]
        self.assertIsInstance(text_node.content, Data)
        self.assertEqual(text_node.content.type, "TEXT")
    
    @patch('src.file_whisper_lib.extractors.pdf_extractor.fitz')
    def test_extract_pdf_file_with_correct_password(self, mock_fitz):
        """Test PDF extraction with password protection"""
        # Mock PDF document that needs password
        mock_pdf = MagicMock()
        mock_pdf.needs_pass = True
        mock_pdf.authenticate.side_effect = [False, True]  # First password fails, second succeeds
        mock_pdf.__len__ = Mock(return_value=1)
        
        # Mock page
        mock_page = MagicMock()
        mock_page.get_text.return_value = "Protected content"
        mock_page.get_images.return_value = []
        mock_pdf.load_page.return_value = mock_page
        
        mock_fitz.open.return_value = mock_pdf
        
        node = Node()
        node.content = File(content=self.test_pdf_data)
        node.pdf_max_pages = 10
        node.passwords = ["wrong_password", "correct_password"]
        
        with patch('src.file_whisper_lib.extractors.utils.encode_binary') as mock_encode:
            mock_encode.return_value = b"Protected content"
            result_nodes = PDFExtractor.extract_pdf_file(node)
        
        # Should succeed with correct password
        self.assertEqual(len(result_nodes), 1)
        
        # Verify password attempts
        self.assertEqual(mock_pdf.authenticate.call_count, 2)
        mock_pdf.authenticate.assert_any_call("wrong_password")
        mock_pdf.authenticate.assert_any_call("correct_password")
        
        # Verify correct password was recorded
        self.assertEqual(node.meta.map_string["correct_password"], "correct_password")
        self.assertTrue(node.meta.map_bool["is_encrypted"])
    
    @patch('src.file_whisper_lib.extractors.pdf_extractor.fitz')
    def test_extract_pdf_file_wrong_password(self, mock_fitz):
        """Test PDF extraction with wrong passwords"""
        # Mock PDF document that needs password
        mock_pdf = MagicMock()
        mock_pdf.needs_pass = True
        mock_pdf.authenticate.return_value = False  # All passwords fail
        
        mock_fitz.open.return_value = mock_pdf
        
        node = Node()
        node.content = File(content=self.test_pdf_data)
        node.pdf_max_pages = 10
        node.passwords = ["wrong1", "wrong2"]
        
        with self.assertRaises(ValueError) as context:
            PDFExtractor.extract_pdf_file(node)
        
        self.assertIn("PDF all passwords are invalid", str(context.exception))
        self.assertTrue(node.meta.map_bool["is_encrypted"])
    
    @patch('src.file_whisper_lib.extractors.pdf_extractor.fitz')
    @patch('src.file_whisper_lib.extractors.utils.encode_binary')
    def test_extract_pdf_file_page_limit(self, mock_encode, mock_fitz):
        """Test PDF extraction with page limit"""
        # Mock PDF document with 5 pages
        mock_pdf = MagicMock()
        mock_pdf.needs_pass = False
        mock_pdf.__len__ = Mock(return_value=5)
        
        # Mock pages
        mock_pages = []
        for i in range(5):
            mock_page = MagicMock()
            mock_page.get_text.return_value = f"Page {i+1} content"
            mock_page.get_images.return_value = []
            mock_pages.append(mock_page)
        
        mock_pdf.load_page.side_effect = mock_pages
        mock_fitz.open.return_value = mock_pdf
        
        # Mock encode_binary
        mock_encode.return_value = b"combined text"
        
        node = Node()
        node.content = File(content=self.test_pdf_data)
        node.pdf_max_pages = 3  # Limit to 3 pages
        node.passwords = []
        
        result_nodes = PDFExtractor.extract_pdf_file(node)
        
        # Should only process 3 pages (due to limit)
        self.assertEqual(mock_pdf.load_page.call_count, 3)
        
        # Verify pages 0, 1, 2 were loaded
        for i in range(3):
            mock_pdf.load_page.assert_any_call(i)
    
    def test_extract_pdf_file_data_node_error(self):
        """Test that Data node raises error"""
        node = Node()
        node.content = Data(type="TEXT", content=b"some text")
        
        result_nodes = PDFExtractor.extract_pdf_file(node)
        
        # Should return empty list for Data node
        self.assertEqual(len(result_nodes), 0)
    
    def test_inherit_limits_called(self):
        """Test that inherit_limits is called on created nodes"""
        with patch('src.file_whisper_lib.extractors.pdf_extractor.fitz') as mock_fitz, \
             patch('src.file_whisper_lib.extractors.utils.encode_binary') as mock_encode:
            
            # Mock successful PDF processing
            mock_pdf = MagicMock()
            mock_pdf.needs_pass = False
            mock_pdf.__len__ = Mock(return_value=1)
            
            mock_page = MagicMock()
            mock_page.get_text.return_value = "Test content"
            mock_page.get_images.return_value = []
            mock_pdf.load_page.return_value = mock_page
            
            mock_fitz.open.return_value = mock_pdf
            mock_encode.return_value = b"Test content"
            
            node = Node()
            node.content = File(content=self.test_pdf_data)
            node.pdf_max_pages = 10
            node.passwords = []
            
            # Mock the inherit_limits method
            with patch.object(Node, 'inherit_limits') as mock_inherit:
                result_nodes = PDFExtractor.extract_pdf_file(node)
                
                # Should call inherit_limits for each created node
                self.assertEqual(len(result_nodes), 1)
                mock_inherit.assert_called_once_with(node)


if __name__ == '__main__':
    unittest.main()