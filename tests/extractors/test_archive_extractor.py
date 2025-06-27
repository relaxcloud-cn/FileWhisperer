"""
Tests for Archive extractor
"""
import unittest
import sys
import os
from unittest.mock import Mock, patch, MagicMock

# Add the project root to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from src.file_whisper_lib.extractors.archive_extractor import ArchiveExtractor
from src.file_whisper_lib.dt import Node, File, Data


class TestArchiveExtractor(unittest.TestCase):
    
    def setUp(self):
        """Set up test fixtures"""
        self.test_archive_data = b"test_archive_content"
        self.test_extracted_files = {
            "file1.txt": b"content1",
            "file2.txt": b"content2",
            "folder/file3.txt": b"content3"
        }
    
    @patch('src.file_whisper_lib.extractors.archive_extractor.ArchiveExtractor.extract_files_from_data')
    def test_extract_compressed_file_success(self, mock_extract):
        """Test successful extraction of compressed file without password"""
        mock_extract.return_value = self.test_extracted_files
        
        # Create a File node
        node = Node()
        node.content = File(content=self.test_archive_data)
        node.passwords = []
        
        result_nodes = ArchiveExtractor.extract_compressed_file(node)
        
        # Should create one node per extracted file
        self.assertEqual(len(result_nodes), 3)
        
        # Check that extract_files_from_data was called correctly
        mock_extract.assert_called_once_with(self.test_archive_data)
        
        # Verify each result node
        for i, result_node in enumerate(result_nodes):
            self.assertIsInstance(result_node.content, File)
            self.assertEqual(result_node.prev, node)
            self.assertIn(result_node.content.content, self.test_extracted_files.values())
    
    @patch('src.file_whisper_lib.extractors.archive_extractor.ArchiveExtractor.extract_files_from_data')
    def test_extract_compressed_file_with_password(self, mock_extract):
        """Test extraction of password-protected compressed file"""
        # First call (no password) raises exception, second call (with password) succeeds
        mock_extract.side_effect = [
            RuntimeError("Wrong password"),
            self.test_extracted_files
        ]
        
        node = Node()
        node.content = File(content=self.test_archive_data)
        node.passwords = ["wrong_password", "correct_password"]
        
        result_nodes = ArchiveExtractor.extract_compressed_file(node)
        
        # Should create nodes for extracted files
        self.assertEqual(len(result_nodes), 3)
        
        # Should have tried with the correct password
        self.assertEqual(mock_extract.call_count, 2)
        mock_extract.assert_any_call(self.test_archive_data, "wrong_password")
        mock_extract.assert_any_call(self.test_archive_data, "correct_password")
        
        # Should record the correct password
        self.assertEqual(node.meta.map_string["correct_password"], "correct_password")
    
    @patch('src.file_whisper_lib.extractors.archive_extractor.ArchiveExtractor.extract_files_from_data')
    def test_extract_compressed_file_all_passwords_fail(self, mock_extract):
        """Test extraction when all passwords are wrong"""
        mock_extract.side_effect = RuntimeError("Wrong password")
        
        node = Node()
        node.content = File(content=self.test_archive_data)
        node.passwords = ["password1", "password2"]
        
        with self.assertRaises(RuntimeError) as context:
            ArchiveExtractor.extract_compressed_file(node)
        
        self.assertIn("Failed to extract compressed file", str(context.exception))
    
    @patch('src.file_whisper_lib.extractors.archive_extractor.ArchiveExtractor.extract_files_from_data')
    def test_extract_compressed_file_no_password_needed_fails(self, mock_extract):
        """Test extraction when no password is provided but one is needed"""
        mock_extract.side_effect = RuntimeError("Wrong password")
        
        node = Node()
        node.content = File(content=self.test_archive_data)
        node.passwords = []
        
        with self.assertRaises(RuntimeError):
            ArchiveExtractor.extract_compressed_file(node)
    
    def test_extract_compressed_file_data_node_returns_empty(self):
        """Test that Data node returns empty list"""
        node = Node()
        node.content = Data(type="TEXT", content=b"some text")
        
        result_nodes = ArchiveExtractor.extract_compressed_file(node)
        
        self.assertEqual(len(result_nodes), 0)
    
    @patch('src.file_whisper_lib.extractors.archive_extractor.logger')
    @patch('src.file_whisper_lib.extractors.archive_extractor.ArchiveExtractor.extract_files_from_data')
    def test_extract_compressed_file_general_error(self, mock_extract, mock_logger):
        """Test handling of general errors during extraction"""
        mock_extract.side_effect = Exception("Some other error")
        
        node = Node()
        node.content = File(content=self.test_archive_data)
        node.passwords = []
        
        with self.assertRaises(Exception):
            ArchiveExtractor.extract_compressed_file(node)
        
        mock_logger.error.assert_called()
    
    @patch('src.file_whisper_lib.extractors.archive_extractor.pybit7z')
    def test_extract_files_from_data_success(self, mock_pybit7z):
        """Test successful file extraction from data"""
        # Mock the pybit7z context and extractor
        mock_context = MagicMock()
        mock_extractor = MagicMock()
        mock_extractor.extract.return_value = self.test_extracted_files
        
        mock_pybit7z.lib7zip_context.return_value.__enter__.return_value = mock_context
        mock_pybit7z.BitMemExtractor.return_value = mock_extractor
        mock_pybit7z.FormatAuto = "FormatAuto"
        
        result = ArchiveExtractor.extract_files_from_data(self.test_archive_data)
        
        self.assertEqual(result, self.test_extracted_files)
        mock_pybit7z.BitMemExtractor.assert_called_once_with(mock_context, "FormatAuto")
        mock_extractor.extract.assert_called_once_with(self.test_archive_data)
    
    @patch('src.file_whisper_lib.extractors.archive_extractor.pybit7z')
    def test_extract_files_from_data_with_password(self, mock_pybit7z):
        """Test file extraction with password"""
        mock_context = MagicMock()
        mock_extractor = MagicMock()
        mock_extractor.extract.return_value = self.test_extracted_files
        
        mock_pybit7z.lib7zip_context.return_value.__enter__.return_value = mock_context
        mock_pybit7z.BitMemExtractor.return_value = mock_extractor
        mock_pybit7z.FormatAuto = "FormatAuto"
        
        password = "test_password"
        result = ArchiveExtractor.extract_files_from_data(self.test_archive_data, password)
        
        self.assertEqual(result, self.test_extracted_files)
        mock_extractor.set_password.assert_called_once_with(password)
        mock_extractor.extract.assert_called_once_with(self.test_archive_data)
    
    @patch('src.file_whisper_lib.extractors.archive_extractor.logger')
    @patch('src.file_whisper_lib.extractors.archive_extractor.pybit7z')
    def test_extract_files_from_data_error(self, mock_pybit7z, mock_logger):
        """Test error handling in extract_files_from_data"""
        mock_pybit7z.lib7zip_context.side_effect = Exception("Extraction error")
        
        with self.assertRaises(Exception):
            ArchiveExtractor.extract_files_from_data(self.test_archive_data)
        
        mock_logger.error.assert_called()
    
    def test_inherit_limits_called(self):
        """Test that inherit_limits is called on created nodes"""
        with patch('src.file_whisper_lib.extractors.archive_extractor.ArchiveExtractor.extract_files_from_data') as mock_extract:
            mock_extract.return_value = {"test.txt": b"content"}
            
            node = Node()
            node.content = File(content=self.test_archive_data)
            node.passwords = []
            
            # Mock the inherit_limits method
            with patch.object(Node, 'inherit_limits') as mock_inherit:
                result_nodes = ArchiveExtractor.extract_compressed_file(node)
                
                # Should call inherit_limits for each created node
                self.assertEqual(len(result_nodes), 1)
                mock_inherit.assert_called_once_with(node)


if __name__ == '__main__':
    unittest.main()