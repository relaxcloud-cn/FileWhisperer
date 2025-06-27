"""
Tests for OCR extractor
"""
import unittest
import sys
import os
from unittest.mock import Mock, patch, MagicMock
import numpy as np
from io import BytesIO

# Add the project root to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from src.file_whisper_lib.extractors.ocr_extractor import OCRExtractor
from src.file_whisper_lib.dt import Node, File, Data


class TestOCRExtractor(unittest.TestCase):
    
    def setUp(self):
        """Set up test fixtures"""
        self.test_image_data = b"fake_image_data"
        self.test_extracted_text = "识别出的中文文本\nRecognized English text"
        
        # Reset class variables before each test
        OCRExtractor.paddle_ocr_gpu = None
        OCRExtractor.paddle_ocr_cpu = None
        OCRExtractor.gpu_available = None
    
    @patch('src.file_whisper_lib.extractors.ocr_extractor.paddle')
    @patch('src.file_whisper_lib.extractors.ocr_extractor.torch')
    def test_initialize_paddle_ocr_gpu_available(self, mock_torch, mock_paddle):
        """Test OCR initialization with GPU available"""
        # Mock GPU detection
        mock_paddle.device.get_device_count.return_value = 1
        mock_paddle.device.get_device.return_value = "gpu:0"
        
        # Mock PaddleOCR initialization
        mock_gpu_ocr = MagicMock()
        mock_cpu_ocr = MagicMock()
        
        with patch('src.file_whisper_lib.extractors.ocr_extractor.PaddleOCR') as mock_paddle_ocr:
            mock_paddle_ocr.side_effect = [mock_gpu_ocr, mock_cpu_ocr]
            
            result = OCRExtractor._initialize_paddle_ocr()
            
            self.assertTrue(result)
            self.assertTrue(OCRExtractor.gpu_available)
            self.assertEqual(OCRExtractor.paddle_ocr_gpu, mock_gpu_ocr)
            self.assertEqual(OCRExtractor.paddle_ocr_cpu, mock_cpu_ocr)
            
            # Verify GPU OCR was initialized first
            self.assertEqual(mock_paddle_ocr.call_count, 2)
            mock_paddle.device.set_device.assert_any_call('gpu:0')
            mock_paddle.device.set_device.assert_any_call('cpu')
    
    @patch('src.file_whisper_lib.extractors.ocr_extractor.paddle')
    @patch('src.file_whisper_lib.extractors.ocr_extractor.torch')
    def test_initialize_paddle_ocr_gpu_unavailable(self, mock_torch, mock_paddle):
        """Test OCR initialization with GPU unavailable"""
        # Mock no GPU available
        mock_paddle.device.get_device_count.return_value = 0
        mock_torch.cuda.is_available.return_value = False
        
        # Mock PaddleOCR initialization
        mock_cpu_ocr = MagicMock()
        
        with patch('src.file_whisper_lib.extractors.ocr_extractor.PaddleOCR') as mock_paddle_ocr:
            mock_paddle_ocr.return_value = mock_cpu_ocr
            
            result = OCRExtractor._initialize_paddle_ocr()
            
            self.assertTrue(result)
            self.assertFalse(OCRExtractor.gpu_available)
            self.assertIsNone(OCRExtractor.paddle_ocr_gpu)
            self.assertEqual(OCRExtractor.paddle_ocr_cpu, mock_cpu_ocr)
    
    @patch('src.file_whisper_lib.extractors.ocr_extractor.paddle')
    @patch('src.file_whisper_lib.extractors.ocr_extractor.torch')
    def test_initialize_paddle_ocr_gpu_init_fails(self, mock_torch, mock_paddle):
        """Test OCR initialization when GPU init fails"""
        # Mock GPU available but initialization fails
        mock_paddle.device.get_device_count.return_value = 1
        mock_torch.cuda.is_available.return_value = True
        
        mock_cpu_ocr = MagicMock()
        
        with patch('src.file_whisper_lib.extractors.ocr_extractor.PaddleOCR') as mock_paddle_ocr:
            # GPU init fails, CPU succeeds
            mock_paddle_ocr.side_effect = [Exception("GPU init failed"), mock_cpu_ocr]
            
            result = OCRExtractor._initialize_paddle_ocr()
            
            self.assertTrue(result)
            self.assertFalse(OCRExtractor.gpu_available)  # Should be set to False after failure
            self.assertIsNone(OCRExtractor.paddle_ocr_gpu)
            self.assertEqual(OCRExtractor.paddle_ocr_cpu, mock_cpu_ocr)
    
    @patch('src.file_whisper_lib.extractors.ocr_extractor.paddle')
    def test_initialize_paddle_ocr_cpu_init_fails(self, mock_paddle):
        """Test OCR initialization when CPU init fails"""
        # Mock no GPU available and CPU init fails
        mock_paddle.device.get_device_count.return_value = 0
        
        with patch('src.file_whisper_lib.extractors.ocr_extractor.PaddleOCR') as mock_paddle_ocr:
            mock_paddle_ocr.side_effect = Exception("CPU init failed")
            
            result = OCRExtractor._initialize_paddle_ocr()
            
            self.assertFalse(result)
            self.assertIsNone(OCRExtractor.paddle_ocr_cpu)
    
    @patch('src.file_whisper_lib.extractors.ocr_extractor.OCRExtractor._initialize_paddle_ocr')
    @patch('src.file_whisper_lib.extractors.ocr_extractor.paddle')
    @patch('src.file_whisper_lib.extractors.ocr_extractor.cv2')
    @patch('src.file_whisper_lib.extractors.ocr_extractor.np')
    @patch('src.file_whisper_lib.extractors.ocr_extractor.Image')
    @patch('src.file_whisper_lib.extractors.utils.encode_binary')
    def test_extract_ocr_gpu_success(self, mock_encode, mock_image, mock_np, mock_cv2, 
                                   mock_paddle, mock_init):
        """Test successful OCR extraction using GPU"""
        # Mock initialization success
        mock_init.return_value = True
        
        # Mock GPU OCR
        mock_gpu_ocr = MagicMock()
        OCRExtractor.gpu_available = True
        OCRExtractor.paddle_ocr_gpu = mock_gpu_ocr
        
        # Mock OCR result
        mock_ocr_result = [
            [
                [[[100, 100], [200, 100], [200, 150], [100, 150]], ["识别文本", 0.95]],
                [[[100, 200], [300, 200], [300, 250], [100, 250]], ["English text", 0.90]]
            ]
        ]
        mock_gpu_ocr.ocr.return_value = mock_ocr_result
        
        # Mock image processing
        mock_pil_image = MagicMock()
        mock_image.open.return_value = mock_pil_image
        mock_np.array.return_value = np.array([[[255, 255, 255]]])
        
        # Mock encode_binary
        mock_encode.return_value = b"识别文本\nEnglish text"
        
        # Create a File node
        node = Node()
        node.content = File(content=self.test_image_data)
        
        result_nodes = OCRExtractor.extract_ocr(node)
        
        # Should create one OCR result node
        self.assertEqual(len(result_nodes), 1)
        
        result_node = result_nodes[0]
        self.assertIsInstance(result_node.content, Data)
        self.assertEqual(result_node.content.type, "OCR")
        self.assertEqual(result_node.prev, node)
        
        # Verify GPU OCR was used
        mock_gpu_ocr.ocr.assert_called_once()
        mock_paddle.device.set_device.assert_any_call('gpu:0')
        mock_encode.assert_called_once_with("识别文本\nEnglish text")
    
    @patch('src.file_whisper_lib.extractors.ocr_extractor.OCRExtractor._initialize_paddle_ocr')
    @patch('src.file_whisper_lib.extractors.ocr_extractor.paddle')
    @patch('src.file_whisper_lib.extractors.ocr_extractor.cv2')
    @patch('src.file_whisper_lib.extractors.ocr_extractor.np')
    @patch('src.file_whisper_lib.extractors.ocr_extractor.Image')
    @patch('src.file_whisper_lib.extractors.utils.encode_binary')
    def test_extract_ocr_cpu_fallback(self, mock_encode, mock_image, mock_np, mock_cv2, 
                                    mock_paddle, mock_init):
        """Test OCR extraction fallback to CPU when GPU fails"""
        # Mock initialization success
        mock_init.return_value = True
        
        # Mock GPU and CPU OCR
        mock_gpu_ocr = MagicMock()
        mock_cpu_ocr = MagicMock()
        OCRExtractor.gpu_available = True
        OCRExtractor.paddle_ocr_gpu = mock_gpu_ocr
        OCRExtractor.paddle_ocr_cpu = mock_cpu_ocr
        
        # GPU OCR fails, CPU succeeds
        mock_gpu_ocr.ocr.side_effect = Exception("GPU OCR failed")
        mock_cpu_ocr.ocr.return_value = [
            [
                [[[100, 100], [200, 100], [200, 150], [100, 150]], ["CPU识别", 0.95]]
            ]
        ]
        
        # Mock image processing
        mock_pil_image = MagicMock()
        mock_image.open.return_value = mock_pil_image
        mock_np.array.return_value = np.array([[[255, 255, 255]]])
        
        # Mock encode_binary
        mock_encode.return_value = b"CPU识别"
        
        node = Node()
        node.content = File(content=self.test_image_data)
        
        result_nodes = OCRExtractor.extract_ocr(node)
        
        # Should still create one OCR result node
        self.assertEqual(len(result_nodes), 1)
        
        # Verify both GPU and CPU were attempted
        mock_gpu_ocr.ocr.assert_called_once()
        mock_cpu_ocr.ocr.assert_called_once()
        mock_encode.assert_called_once_with("CPU识别")
    
    @patch('src.file_whisper_lib.extractors.ocr_extractor.OCRExtractor._initialize_paddle_ocr')
    @patch('src.file_whisper_lib.extractors.ocr_extractor.paddle')
    @patch('src.file_whisper_lib.extractors.ocr_extractor.cv2')
    @patch('src.file_whisper_lib.extractors.ocr_extractor.np')
    @patch('src.file_whisper_lib.extractors.ocr_extractor.Image')
    def test_extract_ocr_cpu_only(self, mock_image, mock_np, mock_cv2, mock_paddle, mock_init):
        """Test OCR extraction with CPU only"""
        # Mock initialization success
        mock_init.return_value = True
        
        # Mock CPU-only setup
        mock_cpu_ocr = MagicMock()
        OCRExtractor.gpu_available = False
        OCRExtractor.paddle_ocr_gpu = None
        OCRExtractor.paddle_ocr_cpu = mock_cpu_ocr
        
        # Mock OCR result
        mock_cpu_ocr.ocr.return_value = [
            [
                [[[100, 100], [200, 100], [200, 150], [100, 150]], ["CPU only", 0.95]]
            ]
        ]
        
        # Mock image processing
        mock_pil_image = MagicMock()
        mock_image.open.return_value = mock_pil_image
        mock_np.array.return_value = np.array([[[255, 255, 255]]])
        
        node = Node()
        node.content = File(content=self.test_image_data)
        
        with patch('src.file_whisper_lib.extractors.utils.encode_binary') as mock_encode:
            mock_encode.return_value = b"CPU only"
            result_nodes = OCRExtractor.extract_ocr(node)
        
        # Should create one OCR result node
        self.assertEqual(len(result_nodes), 1)
        
        # Verify only CPU OCR was used
        mock_cpu_ocr.ocr.assert_called_once()
        mock_paddle.device.set_device.assert_called_with('cpu')
    
    @patch('src.file_whisper_lib.extractors.ocr_extractor.OCRExtractor._initialize_paddle_ocr')
    @patch('src.file_whisper_lib.extractors.ocr_extractor.cv2')
    @patch('src.file_whisper_lib.extractors.ocr_extractor.np')
    @patch('src.file_whisper_lib.extractors.ocr_extractor.Image')
    def test_extract_ocr_rgba_conversion(self, mock_image, mock_np, mock_cv2, mock_init):
        """Test RGBA to RGB conversion"""
        # Mock initialization success
        mock_init.return_value = True
        
        # Mock CPU OCR
        mock_cpu_ocr = MagicMock()
        OCRExtractor.paddle_ocr_cpu = mock_cpu_ocr
        OCRExtractor.gpu_available = False
        mock_cpu_ocr.ocr.return_value = []
        
        # Mock RGBA image
        mock_pil_image = MagicMock()
        mock_image.open.return_value = mock_pil_image
        mock_np.array.return_value = np.array([[[255, 255, 255, 255]]])  # RGBA
        
        node = Node()
        node.content = File(content=self.test_image_data)
        
        OCRExtractor.extract_ocr(node)
        
        # Verify RGBA to RGB conversion was called
        mock_cv2.cvtColor.assert_called_once()
    
    @patch('src.file_whisper_lib.extractors.ocr_extractor.OCRExtractor._initialize_paddle_ocr')
    def test_extract_ocr_initialization_failure(self, mock_init):
        """Test OCR extraction when initialization fails"""
        # Mock initialization failure
        mock_init.return_value = False
        
        node = Node()
        node.content = File(content=self.test_image_data)
        
        result_nodes = OCRExtractor.extract_ocr(node)
        
        # Should return empty list when initialization fails
        self.assertEqual(len(result_nodes), 0)
    
    def test_extract_ocr_data_node_returns_empty(self):
        """Test that Data node returns empty list"""
        node = Node()
        node.content = Data(type="TEXT", content=b"some text")
        
        result_nodes = OCRExtractor.extract_ocr(node)
        
        self.assertEqual(len(result_nodes), 0)
    
    @patch('src.file_whisper_lib.extractors.ocr_extractor.logger')
    @patch('src.file_whisper_lib.extractors.ocr_extractor.OCRExtractor._initialize_paddle_ocr')
    def test_extract_ocr_error_handling(self, mock_init, mock_logger):
        """Test error handling in extract_ocr"""
        # Mock initialization success but image processing fails
        mock_init.return_value = True
        
        node = Node()
        node.content = File(content=None)  # This should cause an error
        
        result_nodes = OCRExtractor.extract_ocr(node)
        
        # Should return empty list on error
        self.assertEqual(len(result_nodes), 0)
        
        # Should log the error
        mock_logger.error.assert_called()
    
    @patch('src.file_whisper_lib.extractors.ocr_extractor.OCRExtractor._initialize_paddle_ocr')
    @patch('src.file_whisper_lib.extractors.ocr_extractor.paddle')
    @patch('src.file_whisper_lib.extractors.ocr_extractor.cv2')
    @patch('src.file_whisper_lib.extractors.ocr_extractor.np')
    @patch('src.file_whisper_lib.extractors.ocr_extractor.Image')
    def test_extract_ocr_no_text_found(self, mock_image, mock_np, mock_cv2, mock_paddle, mock_init):
        """Test OCR extraction when no text is found"""
        # Mock initialization success
        mock_init.return_value = True
        
        # Mock CPU OCR with empty result
        mock_cpu_ocr = MagicMock()
        OCRExtractor.paddle_ocr_cpu = mock_cpu_ocr
        OCRExtractor.gpu_available = False
        mock_cpu_ocr.ocr.return_value = []  # No text found
        
        # Mock image processing
        mock_pil_image = MagicMock()
        mock_image.open.return_value = mock_pil_image
        mock_np.array.return_value = np.array([[[255, 255, 255]]])
        
        node = Node()
        node.content = File(content=self.test_image_data)
        
        result_nodes = OCRExtractor.extract_ocr(node)
        
        # Should return empty list when no text is found
        self.assertEqual(len(result_nodes), 0)
    
    def test_inherit_limits_called(self):
        """Test that inherit_limits is called on created nodes"""
        with patch('src.file_whisper_lib.extractors.ocr_extractor.OCRExtractor._initialize_paddle_ocr') as mock_init, \
             patch('src.file_whisper_lib.extractors.ocr_extractor.paddle') as mock_paddle, \
             patch('src.file_whisper_lib.extractors.ocr_extractor.cv2') as mock_cv2, \
             patch('src.file_whisper_lib.extractors.ocr_extractor.np') as mock_np, \
             patch('src.file_whisper_lib.extractors.ocr_extractor.Image') as mock_image, \
             patch('src.file_whisper_lib.extractors.utils.encode_binary') as mock_encode:
            
            # Mock successful OCR
            mock_init.return_value = True
            mock_cpu_ocr = MagicMock()
            OCRExtractor.paddle_ocr_cpu = mock_cpu_ocr
            OCRExtractor.gpu_available = False
            
            mock_cpu_ocr.ocr.return_value = [
                [
                    [[[100, 100], [200, 100], [200, 150], [100, 150]], ["test text", 0.95]]
                ]
            ]
            
            mock_pil_image = MagicMock()
            mock_image.open.return_value = mock_pil_image
            mock_np.array.return_value = np.array([[[255, 255, 255]]])
            mock_encode.return_value = b"test text"
            
            node = Node()
            node.content = File(content=self.test_image_data)
            
            # Mock the inherit_limits method
            with patch.object(Node, 'inherit_limits') as mock_inherit:
                result_nodes = OCRExtractor.extract_ocr(node)
                
                # Should call inherit_limits for each created node
                self.assertEqual(len(result_nodes), 1)
                mock_inherit.assert_called_once_with(node)


if __name__ == '__main__':
    unittest.main()