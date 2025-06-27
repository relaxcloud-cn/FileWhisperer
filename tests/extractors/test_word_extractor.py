"""
Tests for Word extractor
"""
import unittest
import sys
import os
from unittest.mock import Mock, patch, MagicMock, mock_open
import zipfile

# Add the project root to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from src.file_whisper_lib.extractors.word_extractor import WordExtractor
from src.file_whisper_lib.dt import Node, File, Data
from src.file_whisper_lib.types import Types


class TestWordExtractor(unittest.TestCase):
    
    def setUp(self):
        """Set up test fixtures"""
        self.test_word_data = b"fake_word_document_data"
        self.test_paragraph_texts = ["First paragraph", "Second paragraph", "Third paragraph"]
    
    @patch('src.file_whisper_lib.extractors.word_extractor.os.remove')
    @patch('src.file_whisper_lib.extractors.word_extractor.os.path.exists')
    @patch('src.file_whisper_lib.extractors.word_extractor.docx')
    @patch('src.file_whisper_lib.extractors.word_extractor.zipfile.ZipFile')
    @patch('builtins.open', new_callable=mock_open)
    @patch('src.file_whisper_lib.extractors.word_extractor.uuid.uuid4')
    @patch('src.file_whisper_lib.extractors.utils.encode_binary')
    def test_extract_word_file_docx_success(self, mock_encode, mock_uuid, mock_open_func, 
                                          mock_zipfile, mock_docx, mock_exists, mock_remove):
        """Test successful extraction of DOCX file"""
        # Mock UUID for temporary file path
        mock_uuid.return_value.return_value.__str__ = Mock(return_value="test-uuid")
        
        # Mock docx document
        mock_doc = MagicMock()
        mock_paragraphs = []
        for text in self.test_paragraph_texts:
            mock_para = MagicMock()
            mock_para.text = text
            mock_paragraphs.append(mock_para)
        mock_doc.paragraphs = mock_paragraphs
        mock_docx.Document.return_value = mock_doc
        
        # Mock zipfile for media extraction
        mock_zip = MagicMock()
        mock_zip.namelist.return_value = [
            'word/',
            'word/media/',
            'word/media/image1.png',
            'word/media/image2.jpg'
        ]
        mock_zip.read.side_effect = lambda x: b"fake_image_data"
        mock_zipfile.return_value.__enter__.return_value = mock_zip
        
        # Mock file operations
        mock_exists.return_value = True
        mock_encode.return_value = b"First paragraph\nSecond paragraph\nThird paragraph"
        
        # Create a File node
        node = Node()
        node.content = File(content=self.test_word_data)
        node.word_max_pages = 10
        node.type = Types.DOCX
        
        result_nodes = WordExtractor.extract_word_file(node)
        
        # Should create text node + media nodes
        self.assertGreaterEqual(len(result_nodes), 1)
        
        # Check text node
        text_nodes = [n for n in result_nodes if isinstance(n.content, Data)]
        self.assertEqual(len(text_nodes), 1)
        self.assertEqual(text_nodes[0].content.type, "TEXT")
        
        # Check media nodes
        media_nodes = [n for n in result_nodes if isinstance(n.content, File)]
        self.assertEqual(len(media_nodes), 2)  # image1.png and image2.jpg
        
        # Verify is_encrypted was set to False
        self.assertFalse(node.meta.map_bool["is_encrypted"])
        
        # Verify temporary file cleanup
        mock_remove.assert_called()
    
    @patch('src.file_whisper_lib.extractors.word_extractor.os.remove')
    @patch('src.file_whisper_lib.extractors.word_extractor.os.path.exists')
    @patch('src.file_whisper_lib.extractors.word_extractor.Document')
    @patch('src.file_whisper_lib.extractors.word_extractor.docx')
    @patch('src.file_whisper_lib.extractors.word_extractor.zipfile.ZipFile')
    @patch('builtins.open', new_callable=mock_open)
    @patch('src.file_whisper_lib.extractors.word_extractor.uuid.uuid4')
    def test_extract_word_file_doc_conversion(self, mock_uuid, mock_open_func, mock_zipfile, 
                                            mock_docx, mock_spire_doc, mock_exists, mock_remove):
        """Test conversion of DOC to DOCX"""
        # Mock UUID
        mock_uuid.return_value.__str__ = Mock(return_value="test-uuid")
        
        # Mock Spire Document for DOC conversion
        mock_doc_spire = MagicMock()
        mock_spire_doc.return_value = mock_doc_spire
        
        # Mock docx processing after conversion
        mock_doc = MagicMock()
        mock_doc.paragraphs = [Mock(text="Converted content")]
        mock_docx.Document.return_value = mock_doc
        
        # Mock zipfile
        mock_zip = MagicMock()
        mock_zip.namelist.return_value = ['word/']
        mock_zipfile.return_value.__enter__.return_value = mock_zip
        
        mock_exists.return_value = True
        
        # Create a File node for DOC
        node = Node()
        node.content = File(content=self.test_word_data)
        node.word_max_pages = 10
        node.type = Types.DOC
        
        with patch('src.file_whisper_lib.extractors.utils.encode_binary') as mock_encode:
            mock_encode.return_value = b"Converted content"
            result_nodes = WordExtractor.extract_word_file(node)
        
        # Should convert DOC to DOCX first
        mock_doc_spire.LoadFromFile.assert_called()
        mock_doc_spire.SaveToFile.assert_called()
        
        # Should process the converted file
        self.assertGreaterEqual(len(result_nodes), 1)
    
    @patch('src.file_whisper_lib.extractors.word_extractor.os.remove')
    @patch('src.file_whisper_lib.extractors.word_extractor.os.path.exists')
    @patch('src.file_whisper_lib.extractors.word_extractor.Document')
    @patch('src.file_whisper_lib.extractors.word_extractor.zipfile.ZipFile')
    @patch('builtins.open', new_callable=mock_open)
    @patch('src.file_whisper_lib.extractors.word_extractor.uuid.uuid4')
    def test_extract_word_file_encrypted_success(self, mock_uuid, mock_open_func, mock_zipfile, 
                                               mock_spire_doc, mock_exists, mock_remove):
        """Test extraction of encrypted Word file with correct password"""
        # Mock UUID
        mock_uuid.return_value.__str__ = Mock(return_value="test-uuid")
        
        # Mock zipfile to raise BadZipFile (indicating encryption)
        mock_zipfile.side_effect = zipfile.BadZipFile("Bad zip file")
        
        # Mock Spire Document for password handling
        mock_doc_spire = MagicMock()
        mock_spire_doc.return_value = mock_doc_spire
        
        # First password attempt fails, second succeeds
        mock_doc_spire.LoadFromFile.side_effect = [Exception("Wrong password"), None]
        
        mock_exists.return_value = True
        
        node = Node()
        node.content = File(content=self.test_word_data)
        node.word_max_pages = 10
        node.passwords = ["wrong_password", "correct_password"]
        node.type = Types.DOCX
        
        # Mock successful processing after decryption
        with patch('src.file_whisper_lib.extractors.word_extractor.docx') as mock_docx, \
             patch('src.file_whisper_lib.extractors.utils.encode_binary') as mock_encode:
            
            mock_doc = MagicMock()
            mock_doc.paragraphs = [Mock(text="Decrypted content")]
            mock_docx.Document.return_value = mock_doc
            mock_encode.return_value = b"Decrypted content"
            
            # Mock the second zipfile call (after decryption) to succeed
            with patch('src.file_whisper_lib.extractors.word_extractor.zipfile.ZipFile') as mock_zip2:
                mock_zip_obj = MagicMock()
                mock_zip_obj.namelist.return_value = ['word/']
                mock_zip2.return_value.__enter__.return_value = mock_zip_obj
                
                result_nodes = WordExtractor.extract_word_file(node)
        
        # Should mark as encrypted
        self.assertTrue(node.meta.map_bool["is_encrypted"])
        
        # Should try decryption with both passwords
        self.assertEqual(mock_doc_spire.LoadFromFile.call_count, 2)
        
        # Should successfully extract content
        self.assertGreaterEqual(len(result_nodes), 1)
    
    @patch('src.file_whisper_lib.extractors.word_extractor.os.remove')
    @patch('src.file_whisper_lib.extractors.word_extractor.os.path.exists')
    @patch('src.file_whisper_lib.extractors.word_extractor.Document')
    @patch('src.file_whisper_lib.extractors.word_extractor.zipfile.ZipFile')
    @patch('builtins.open', new_callable=mock_open)
    @patch('src.file_whisper_lib.extractors.word_extractor.uuid.uuid4')
    def test_extract_word_file_ole_objects(self, mock_uuid, mock_open_func, mock_zipfile, 
                                         mock_spire_doc, mock_exists, mock_remove):
        """Test extraction of OLE objects from Word file"""
        # Mock UUID
        mock_uuid.return_value.__str__ = Mock(return_value="test-uuid")
        
        # Mock docx processing
        with patch('src.file_whisper_lib.extractors.word_extractor.docx') as mock_docx:
            mock_doc = MagicMock()
            mock_doc.paragraphs = [Mock(text="Document with OLE")]
            mock_docx.Document.return_value = mock_doc
        
        # Mock zipfile with OLE embeddings
        mock_zip = MagicMock()
        mock_zip.namelist.return_value = [
            'word/',
            'word/embeddings/',
            'word/embeddings/oleObject1.bin'
        ]
        mock_zipfile.return_value.__enter__.return_value = mock_zip
        
        # Mock Spire Document for OLE processing
        mock_doc_spire = MagicMock()
        mock_spire_doc.return_value = mock_doc_spire
        
        # Mock document sections and OLE objects
        mock_section = MagicMock()
        mock_paragraph = MagicMock()
        mock_ole_object = MagicMock()
        mock_ole_object.DocumentObjectType = MagicMock()
        mock_ole_object.ObjectType = "AcroExch.Document.PDF"
        mock_ole_object.NativeData = b"ole_pdf_data"
        
        # Setup the document structure
        mock_doc_spire.Sections.Count = 1
        mock_doc_spire.Sections.get_Item.return_value = mock_section
        mock_section.Body.ChildObjects.Count = 1
        mock_section.Body.ChildObjects.get_Item.return_value = mock_paragraph
        mock_paragraph.ChildObjects.Count = 1
        mock_paragraph.ChildObjects.get_Item.return_value = mock_ole_object
        
        # Mock DocumentObjectType enum
        with patch('src.file_whisper_lib.extractors.word_extractor.DocumentObjectType') as mock_doc_type:
            mock_doc_type.OleObject = "OleObject"
            mock_ole_object.DocumentObjectType = "OleObject"
            
            mock_exists.return_value = True
            
            node = Node()
            node.content = File(content=self.test_word_data)
            node.word_max_pages = 10
            node.type = Types.DOCX
            
            with patch('src.file_whisper_lib.extractors.utils.encode_binary') as mock_encode:
                mock_encode.return_value = b"Document with OLE"
                result_nodes = WordExtractor.extract_word_file(node)
            
            # Should process OLE objects
            mock_doc_spire.LoadFromFile.assert_called()
            mock_doc_spire.Close.assert_called()
            
            # Should create nodes for text and OLE objects
            self.assertGreaterEqual(len(result_nodes), 1)
    
    def test_extract_word_file_data_node_error(self):
        """Test that Data node returns empty list"""
        node = Node()
        node.content = Data(type="TEXT", content=b"some text")
        
        result_nodes = WordExtractor.extract_word_file(node)
        
        # Should return empty list for Data node
        self.assertEqual(len(result_nodes), 0)
    
    @patch('src.file_whisper_lib.extractors.word_extractor.os.remove')
    @patch('src.file_whisper_lib.extractors.word_extractor.os.path.exists')
    @patch('src.file_whisper_lib.extractors.word_extractor.docx')
    @patch('builtins.open', new_callable=mock_open)
    @patch('src.file_whisper_lib.extractors.word_extractor.uuid.uuid4')
    def test_extract_word_file_page_limit(self, mock_uuid, mock_open_func, mock_docx, 
                                        mock_exists, mock_remove):
        """Test Word file extraction with page limit"""
        # Mock UUID
        mock_uuid.return_value.__str__ = Mock(return_value="test-uuid")
        
        # Create many paragraphs (more than page limit)
        mock_doc = MagicMock()
        mock_paragraphs = []
        for i in range(50):  # 50 paragraphs
            mock_para = MagicMock()
            mock_para.text = f"Paragraph {i+1}"
            mock_paragraphs.append(mock_para)
        mock_doc.paragraphs = mock_paragraphs
        mock_docx.Document.return_value = mock_doc
        
        # Mock zipfile
        with patch('src.file_whisper_lib.extractors.word_extractor.zipfile.ZipFile') as mock_zipfile:
            mock_zip = MagicMock()
            mock_zip.namelist.return_value = ['word/']
            mock_zipfile.return_value.__enter__.return_value = mock_zip
            
            mock_exists.return_value = True
            
            node = Node()
            node.content = File(content=self.test_word_data)
            node.word_max_pages = 2  # Limit to 2 pages (40 paragraphs max)
            node.type = Types.DOCX
            
            with patch('src.file_whisper_lib.extractors.utils.encode_binary') as mock_encode:
                # Should only process first 40 paragraphs (2 pages * 20 paragraphs/page)
                expected_text = "\n".join([f"Paragraph {i+1}" for i in range(40)])
                mock_encode.return_value = expected_text.encode('utf-8')
                
                result_nodes = WordExtractor.extract_word_file(node)
                
                # Verify only limited paragraphs were processed
                mock_encode.assert_called_once_with(expected_text)
    
    def test_inherit_limits_called(self):
        """Test that inherit_limits is called on created nodes"""
        with patch('src.file_whisper_lib.extractors.word_extractor.os.remove'), \
             patch('src.file_whisper_lib.extractors.word_extractor.os.path.exists') as mock_exists, \
             patch('src.file_whisper_lib.extractors.word_extractor.docx') as mock_docx, \
             patch('src.file_whisper_lib.extractors.word_extractor.zipfile.ZipFile') as mock_zipfile, \
             patch('builtins.open', new_callable=mock_open), \
             patch('src.file_whisper_lib.extractors.word_extractor.uuid.uuid4') as mock_uuid, \
             patch('src.file_whisper_lib.extractors.utils.encode_binary') as mock_encode:
            
            # Setup mocks
            mock_uuid.return_value.__str__ = Mock(return_value="test-uuid")
            mock_exists.return_value = True
            
            mock_doc = MagicMock()
            mock_doc.paragraphs = [Mock(text="Test content")]
            mock_docx.Document.return_value = mock_doc
            
            mock_zip = MagicMock()
            mock_zip.namelist.return_value = ['word/']
            mock_zipfile.return_value.__enter__.return_value = mock_zip
            
            mock_encode.return_value = b"Test content"
            
            node = Node()
            node.content = File(content=self.test_word_data)
            node.word_max_pages = 10
            node.type = Types.DOCX
            
            # Mock the inherit_limits method
            with patch.object(Node, 'inherit_limits') as mock_inherit:
                result_nodes = WordExtractor.extract_word_file(node)
                
                # Should call inherit_limits for each created node
                for _ in result_nodes:
                    mock_inherit.assert_any_call(node)


if __name__ == '__main__':
    unittest.main()