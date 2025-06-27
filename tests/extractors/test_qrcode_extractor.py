"""
Tests for QR Code extractor
"""
import unittest
import sys
import os
from unittest.mock import Mock, patch, MagicMock
import numpy as np

# Add the project root to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from src.file_whisper_lib.extractors.qrcode_extractor import QRCodeExtractor
from src.file_whisper_lib.dt import Node, File, Data


class TestQRCodeExtractor(unittest.TestCase):
    
    def setUp(self):
        """Set up test fixtures"""
        # Create sample image data (this would normally be actual image bytes)
        self.test_image_data = b"fake_image_data"
        self.test_qr_text = "https://example.com"
    
    @patch('src.file_whisper_lib.extractors.qrcode_extractor.zxingcpp')
    @patch('src.file_whisper_lib.extractors.qrcode_extractor.cv2')
    @patch('src.file_whisper_lib.extractors.qrcode_extractor.np')
    @patch('src.file_whisper_lib.extractors.utils.encode_binary')
    def test_extract_qrcode_success(self, mock_encode, mock_np, mock_cv2, mock_zxing):
        """Test successful QR code extraction"""
        # Mock the barcode result
        mock_barcode = MagicMock()
        mock_barcode.text = self.test_qr_text
        mock_zxing.read_barcodes.return_value = [mock_barcode]
        
        # Mock numpy and cv2 operations
        mock_np.asarray.return_value = np.array([1, 2, 3], dtype=np.uint8)
        mock_cv2.imdecode.return_value = np.array([[1, 2, 3]])
        mock_cv2.IMREAD_COLOR = 1
        
        # Mock encode_binary
        mock_encode.return_value = self.test_qr_text.encode('utf-8')
        
        # Create a File node
        node = Node()
        node.content = File(content=self.test_image_data)
        
        result_nodes = QRCodeExtractor.extract_qrcode(node)
        
        # Should create one node for the QR code
        self.assertEqual(len(result_nodes), 1)
        
        result_node = result_nodes[0]
        self.assertIsInstance(result_node.content, Data)
        self.assertEqual(result_node.content.type, "QRCODE")
        self.assertEqual(result_node.prev, node)
        
        # Verify the extraction pipeline was called correctly
        mock_np.asarray.assert_called_once()
        mock_cv2.imdecode.assert_called_once()
        mock_zxing.read_barcodes.assert_called_once()
        mock_encode.assert_called_once_with(self.test_qr_text)
    
    @patch('src.file_whisper_lib.extractors.qrcode_extractor.zxingcpp')
    @patch('src.file_whisper_lib.extractors.qrcode_extractor.cv2')
    @patch('src.file_whisper_lib.extractors.qrcode_extractor.np')
    @patch('src.file_whisper_lib.extractors.utils.encode_binary')
    def test_extract_qrcode_multiple_codes(self, mock_encode, mock_np, mock_cv2, mock_zxing):
        """Test extraction of multiple QR codes from single image"""
        # Mock multiple barcode results
        mock_barcode1 = MagicMock()
        mock_barcode1.text = "https://example.com"
        mock_barcode2 = MagicMock()
        mock_barcode2.text = "Contact info: John Doe"
        
        mock_zxing.read_barcodes.return_value = [mock_barcode1, mock_barcode2]
        
        # Mock numpy and cv2 operations
        mock_np.asarray.return_value = np.array([1, 2, 3], dtype=np.uint8)
        mock_cv2.imdecode.return_value = np.array([[1, 2, 3]])
        mock_cv2.IMREAD_COLOR = 1
        
        # Mock encode_binary
        mock_encode.side_effect = lambda x: x.encode('utf-8')
        
        node = Node()
        node.content = File(content=self.test_image_data)
        
        result_nodes = QRCodeExtractor.extract_qrcode(node)
        
        # Should create two nodes for the two QR codes
        self.assertEqual(len(result_nodes), 2)
        
        # Check both nodes
        for result_node in result_nodes:
            self.assertIsInstance(result_node.content, Data)
            self.assertEqual(result_node.content.type, "QRCODE")
            self.assertEqual(result_node.prev, node)
        
        # Verify encode_binary was called for both texts
        self.assertEqual(mock_encode.call_count, 2)
    
    @patch('src.file_whisper_lib.extractors.qrcode_extractor.zxingcpp')
    @patch('src.file_whisper_lib.extractors.qrcode_extractor.cv2')
    @patch('src.file_whisper_lib.extractors.qrcode_extractor.np')
    def test_extract_qrcode_no_codes_found(self, mock_np, mock_cv2, mock_zxing):
        """Test when no QR codes are found in the image"""
        # Mock empty barcode result
        mock_zxing.read_barcodes.return_value = []
        
        # Mock numpy and cv2 operations
        mock_np.asarray.return_value = np.array([1, 2, 3], dtype=np.uint8)
        mock_cv2.imdecode.return_value = np.array([[1, 2, 3]])
        mock_cv2.IMREAD_COLOR = 1
        
        node = Node()
        node.content = File(content=self.test_image_data)
        
        result_nodes = QRCodeExtractor.extract_qrcode(node)
        
        # Should return empty list
        self.assertEqual(len(result_nodes), 0)
    
    def test_extract_qrcode_data_node_returns_empty(self):
        """Test that Data node returns empty list"""
        node = Node()
        node.content = Data(type="TEXT", content=b"some text")
        
        result_nodes = QRCodeExtractor.extract_qrcode(node)
        
        self.assertEqual(len(result_nodes), 0)
    
    @patch('src.file_whisper_lib.extractors.qrcode_extractor.logger')
    @patch('src.file_whisper_lib.extractors.qrcode_extractor.cv2')
    def test_extract_qrcode_cv2_error(self, mock_cv2, mock_logger):
        """Test error handling when cv2 operations fail"""
        mock_cv2.imdecode.side_effect = Exception("CV2 decode error")
        
        node = Node()
        node.content = File(content=self.test_image_data)
        
        result_nodes = QRCodeExtractor.extract_qrcode(node)
        
        # Should return empty list on error
        self.assertEqual(len(result_nodes), 0)
        
        # Should log the error
        mock_logger.error.assert_called()
    
    @patch('src.file_whisper_lib.extractors.qrcode_extractor.logger')
    @patch('src.file_whisper_lib.extractors.qrcode_extractor.zxingcpp')
    @patch('src.file_whisper_lib.extractors.qrcode_extractor.cv2')
    @patch('src.file_whisper_lib.extractors.qrcode_extractor.np')
    def test_extract_qrcode_zxing_error(self, mock_np, mock_cv2, mock_zxing, mock_logger):
        """Test error handling when zxingcpp operations fail"""
        # Mock successful cv2 operations
        mock_np.asarray.return_value = np.array([1, 2, 3], dtype=np.uint8)
        mock_cv2.imdecode.return_value = np.array([[1, 2, 3]])
        mock_cv2.IMREAD_COLOR = 1
        
        # Mock zxingcpp error
        mock_zxing.read_barcodes.side_effect = Exception("ZXing decode error")
        
        node = Node()
        node.content = File(content=self.test_image_data)
        
        result_nodes = QRCodeExtractor.extract_qrcode(node)
        
        # Should return empty list on error
        self.assertEqual(len(result_nodes), 0)
        
        # Should log the error
        mock_logger.error.assert_called()
    
    def test_inherit_limits_called(self):
        """Test that inherit_limits is called on created nodes"""
        with patch('src.file_whisper_lib.extractors.qrcode_extractor.zxingcpp') as mock_zxing, \
             patch('src.file_whisper_lib.extractors.qrcode_extractor.cv2') as mock_cv2, \
             patch('src.file_whisper_lib.extractors.qrcode_extractor.np') as mock_np, \
             patch('src.file_whisper_lib.extractors.utils.encode_binary') as mock_encode:
            
            # Mock successful QR code detection
            mock_barcode = MagicMock()
            mock_barcode.text = "test text"
            mock_zxing.read_barcodes.return_value = [mock_barcode]
            
            mock_np.asarray.return_value = np.array([1, 2, 3], dtype=np.uint8)
            mock_cv2.imdecode.return_value = np.array([[1, 2, 3]])
            mock_cv2.IMREAD_COLOR = 1
            mock_encode.return_value = b"test text"
            
            node = Node()
            node.content = File(content=self.test_image_data)
            
            # Mock the inherit_limits method
            with patch.object(Node, 'inherit_limits') as mock_inherit:
                result_nodes = QRCodeExtractor.extract_qrcode(node)
                
                # Should call inherit_limits for each created node
                self.assertEqual(len(result_nodes), 1)
                mock_inherit.assert_called_once_with(node)


if __name__ == '__main__':
    unittest.main()