import unittest
import os
from unittest.mock import patch
from src.file_whisper_lib.extractors.ocr_extractor import OCRExtractor


class TestOCRExtractor(unittest.TestCase):
    """测试 OCRExtractor 类的 _recognize_text_from_image 方法"""
    
    @classmethod
    def setUpClass(cls):
        """设置测试类，加载测试图片数据"""
        cls.test_fixtures_path = os.path.join(os.path.dirname(__file__), '..', 'fixtures')
        
        # 加载英文测试图片
        cls.english_image_path = os.path.join(cls.test_fixtures_path, 'test_ocr.jpg')
        with open(cls.english_image_path, 'rb') as f:
            cls.english_image_data = f.read()
            
        # 加载中文测试图片
        cls.chinese_image_path = os.path.join(cls.test_fixtures_path, 'image_cn.png')
        with open(cls.chinese_image_path, 'rb') as f:
            cls.chinese_image_data = f.read()
    
    def setUp(self):
        """每个测试前重置OCR模型实例"""
        OCRExtractor.paddle_ocr = None

    @patch('src.file_whisper_lib.extractors.ocr_extractor.PaddleOCR')
    def test_recognize_text_from_english_image(self, mock_paddle_ocr_class):
        """测试从英文图片中识别文本"""
        # 模拟PaddleOCR实例和识别结果
        mock_paddle_ocr_instance = mock_paddle_ocr_class.return_value
        mock_ocr_result = [
            [
                [[[0, 0], [100, 0], [100, 30], [0, 30]], ('Basics:', 0.95)],
                [[[0, 40], [200, 40], [200, 70], [0, 70]], ('anatomy of a URL', 0.90)],
                [[[0, 80], [150, 80], [150, 110], [0, 110]], ('Here are some', 0.85)]
            ]
        ]
        mock_paddle_ocr_instance.ocr.return_value = mock_ocr_result
        
        result = OCRExtractor._recognize_text_from_image(self.english_image_data)
        
        # 验证返回的是字符串
        self.assertIsInstance(result, str)
        # 验证结果不为空
        self.assertTrue(len(result) > 0)
        # 验证包含预期的英文文本片段
        self.assertIn("Basics:", result)
        self.assertIn("anatomy of a URL", result)
        self.assertIn("Here are some", result)

    @patch('src.file_whisper_lib.extractors.ocr_extractor.PaddleOCR')
    def test_recognize_text_from_chinese_image(self, mock_paddle_ocr_class):
        """测试从中文图片中识别文本"""
        # 模拟PaddleOCR实例和识别结果
        mock_paddle_ocr_instance = mock_paddle_ocr_class.return_value
        mock_ocr_result = [
            [
                [[[0, 0], [100, 0], [100, 30], [0, 30]], ('第二部分', 0.95)],
                [[[100, 0], [300, 0], [300, 30], [100, 30]], ('AI赋能网络安全思想与实践', 0.90)]
            ]
        ]
        mock_paddle_ocr_instance.ocr.return_value = mock_ocr_result
        
        result = OCRExtractor._recognize_text_from_image(self.chinese_image_data)
        
        # 验证返回的是字符串
        self.assertIsInstance(result, str)
        # 验证结果不为空
        self.assertTrue(len(result) > 0)
        # 验证包含预期的中文文本片段
        self.assertIn("第二部分", result)
        self.assertIn("AI", result)

    @patch('src.file_whisper_lib.extractors.ocr_extractor.PaddleOCR')
    def test_recognize_text_with_empty_data(self, _):
        """测试传入空数据时的处理"""
        result = OCRExtractor._recognize_text_from_image(b'')
        
        # 验证返回空字符串（因为无法创建图片对象）
        self.assertEqual(result, "")

    @patch('src.file_whisper_lib.extractors.ocr_extractor.PaddleOCR')
    def test_recognize_text_with_invalid_image_data(self, _):
        """测试传入无效图片数据时的处理"""
        invalid_data = b'not an image'
        result = OCRExtractor._recognize_text_from_image(invalid_data)
        
        # 验证返回空字符串（因为无法解析图片）
        self.assertEqual(result, "")

    @patch('src.file_whisper_lib.extractors.ocr_extractor.OCRExtractor._initialize_paddle_ocr')
    def test_recognize_text_when_ocr_initialization_fails(self, mock_init):
        """测试OCR初始化失败时的处理"""
        # 模拟初始化失败
        mock_init.return_value = False
        
        result = OCRExtractor._recognize_text_from_image(self.english_image_data)
        
        # 验证返回空字符串
        self.assertEqual(result, "")
        # 验证初始化方法被调用
        mock_init.assert_called_once()

    @patch('src.file_whisper_lib.extractors.ocr_extractor.OCRExtractor.paddle_ocr')
    @patch('src.file_whisper_lib.extractors.ocr_extractor.OCRExtractor._initialize_paddle_ocr')
    def test_recognize_text_when_ocr_returns_none(self, mock_init, mock_paddle_ocr):
        """测试OCR识别返回None时的处理"""
        # 模拟初始化成功
        mock_init.return_value = True
        # 模拟OCR返回None
        mock_paddle_ocr.ocr.return_value = None
        
        result = OCRExtractor._recognize_text_from_image(self.english_image_data)
        
        # 验证返回空字符串
        self.assertEqual(result, "")

    @patch('src.file_whisper_lib.extractors.ocr_extractor.OCRExtractor.paddle_ocr')
    @patch('src.file_whisper_lib.extractors.ocr_extractor.OCRExtractor._initialize_paddle_ocr')
    def test_recognize_text_with_empty_ocr_result(self, mock_init, mock_paddle_ocr):
        """测试OCR识别返回空结果时的处理"""
        # 模拟初始化成功
        mock_init.return_value = True
        # 模拟OCR返回空列表
        mock_paddle_ocr.ocr.return_value = [[]]
        
        result = OCRExtractor._recognize_text_from_image(self.english_image_data)
        
        # 验证返回空字符串
        self.assertEqual(result, "")

    @patch('src.file_whisper_lib.extractors.ocr_extractor.OCRExtractor.paddle_ocr')
    @patch('src.file_whisper_lib.extractors.ocr_extractor.OCRExtractor._initialize_paddle_ocr')
    def test_recognize_text_with_mock_ocr_result(self, mock_init, mock_paddle_ocr):
        """测试使用模拟OCR结果的正常流程"""
        # 模拟初始化成功
        mock_init.return_value = True
        
        # 模拟OCR返回结果的格式
        mock_ocr_result = [
            [
                [[[0, 0], [100, 0], [100, 30], [0, 30]], ('Hello', 0.95)],
                [[[0, 40], [100, 40], [100, 70], [0, 70]], ('World', 0.90)]
            ]
        ]
        mock_paddle_ocr.ocr.return_value = mock_ocr_result
        
        result = OCRExtractor._recognize_text_from_image(self.english_image_data)
        
        # 验证返回预期的文本
        self.assertEqual(result, "Hello\nWorld")


if __name__ == "__main__":
    unittest.main()