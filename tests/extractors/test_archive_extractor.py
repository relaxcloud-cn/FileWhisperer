"""
Archive Extractor 单元测试
"""
import unittest
import os
from src.file_whisper_lib.extractors.archive_extractor import ArchiveExtractor


class TestArchiveExtractor(unittest.TestCase):
    
    def setUp(self):
        """测试前准备"""
        self.test_fixtures_dir = os.path.join(os.path.dirname(__file__), '..', 'fixtures')
        self.test_zip_path = os.path.join(self.test_fixtures_dir, 'test.zip')
        self.test_pwd_zip_path = os.path.join(self.test_fixtures_dir, 'test_with_pwd_abcd.zip')
    
    def test_extract_files_from_data_no_password(self):
        """测试无密码ZIP文件解压"""
        # 读取测试ZIP文件
        with open(self.test_zip_path, 'rb') as f:
            zip_data = f.read()
        
        # 调用被测试函数
        result = ArchiveExtractor.extract_files_from_data(zip_data)
        
        # 验证结果
        self.assertIsInstance(result, dict)
        self.assertGreater(len(result), 0, "应该至少解压出一个文件")
        
        # 验证每个解压出的文件都有内容
        for filename, content in result.items():
            self.assertIsInstance(filename, str, "文件名应该是字符串")
            self.assertIsInstance(content, bytes, "文件内容应该是字节")
            self.assertGreater(len(content), 0, f"文件 {filename} 不应该为空")
    
    def test_extract_files_from_data_with_password(self):
        """测试带密码ZIP文件解压"""
        # 读取测试ZIP文件
        with open(self.test_pwd_zip_path, 'rb') as f:
            zip_data = f.read()
        
        # 使用正确密码解压
        correct_password = "abcd"
        result = ArchiveExtractor.extract_files_from_data(zip_data, correct_password)
        
        # 验证结果
        self.assertIsInstance(result, dict)
        self.assertGreater(len(result), 0, "应该至少解压出一个文件")
        
        # 验证每个解压出的文件都有内容
        for filename, content in result.items():
            self.assertIsInstance(filename, str, "文件名应该是字符串")
            self.assertIsInstance(content, bytes, "文件内容应该是字节")
    
    def test_extract_files_from_data_wrong_password(self):
        """测试错误密码的情况"""
        # 读取测试ZIP文件
        with open(self.test_pwd_zip_path, 'rb') as f:
            zip_data = f.read()
        
        # 使用错误密码应该抛出异常
        wrong_password = "wrong_password"
        with self.assertRaises(Exception) as context:
            ArchiveExtractor.extract_files_from_data(zip_data, wrong_password)
        
        # 验证异常信息包含密码错误相关内容
        self.assertIn("Wrong password", str(context.exception))
    
    def test_extract_files_from_data_no_password_for_protected_zip(self):
        """测试受密码保护的ZIP文件不提供密码的情况"""
        # 读取测试ZIP文件
        with open(self.test_pwd_zip_path, 'rb') as f:
            zip_data = f.read()
        
        # 不提供密码应该抛出异常
        with self.assertRaises(Exception):
            ArchiveExtractor.extract_files_from_data(zip_data)
    
    def test_extract_files_from_data_invalid_data(self):
        """测试无效数据的情况"""
        # 使用无效的ZIP数据
        invalid_data = b"This is not a valid ZIP file"
        
        # 应该抛出异常
        with self.assertRaises(Exception):
            ArchiveExtractor.extract_files_from_data(invalid_data)
    
    def test_extract_files_from_data_empty_data(self):
        """测试空数据的情况"""
        # 使用空数据
        empty_data = b""
        
        # 应该抛出异常
        with self.assertRaises(Exception):
            ArchiveExtractor.extract_files_from_data(empty_data)
    
    def test_extract_files_from_data_return_type(self):
        """测试返回值类型"""
        # 读取测试ZIP文件
        with open(self.test_zip_path, 'rb') as f:
            zip_data = f.read()
        
        # 调用被测试函数
        result = ArchiveExtractor.extract_files_from_data(zip_data)
        
        # 验证返回值类型
        self.assertIsInstance(result, dict)
        # 验证字典的键值类型
        for key, value in result.items():
            self.assertIsInstance(key, str, "文件名必须是字符串类型")
            self.assertIsInstance(value, bytes, "文件内容必须是字节类型")


if __name__ == '__main__':
    unittest.main()