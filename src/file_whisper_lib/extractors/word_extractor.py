"""
Word文档处理模块
"""
import os
import uuid
import zipfile
import traceback
import subprocess
from typing import List
from loguru import logger
import docx

from ..dt import Node, File, Data
from ..types import Types
from .utils import encode_binary

try:
    import msoffcrypto
    MSOFFCRYPTO_AVAILABLE = True
except ImportError:
    MSOFFCRYPTO_AVAILABLE = False
    logger.warning("msoffcrypto-tool not available, password-protected files may not be supported")

try:
    import olefile
    OLEFILE_AVAILABLE = True
except ImportError:
    OLEFILE_AVAILABLE = False
    logger.debug("olefile not available, some DOC file features may be limited")


class WordExtractor:
    
    @staticmethod
    def _convert_doc_to_docx(doc_path: str) -> str:
        """Convert DOC file to DOCX using LibreOffice if available"""
        try:
            # Try using LibreOffice to convert DOC to DOCX
            output_dir = os.path.dirname(doc_path)
            docx_filename = os.path.splitext(os.path.basename(doc_path))[0] + '.docx'
            docx_path = os.path.join(output_dir, docx_filename)
            
            # Try different LibreOffice command names
            commands = ['libreoffice', 'soffice']
            for cmd in commands:
                try:
                    result = subprocess.run([
                        cmd, '--headless', '--convert-to', 'docx',
                        '--outdir', output_dir, doc_path
                    ], capture_output=True, text=True, timeout=30)
                    break
                except FileNotFoundError:
                    if cmd == commands[-1]:  # Last command failed
                        raise
                    continue
            
            if result.returncode == 0 and os.path.exists(docx_path):
                logger.info("Successfully converted DOC to DOCX using LibreOffice")
                return docx_path
            else:
                logger.warning(f"LibreOffice conversion failed: {result.stderr}")
                return doc_path
        except (subprocess.TimeoutExpired, FileNotFoundError):
            logger.warning("LibreOffice not available for DOC conversion")
            return doc_path
    
    @staticmethod
    def _decrypt_file(file_path: str, passwords: List[str]) -> str:
        """Decrypt password-protected Office file"""
        if not MSOFFCRYPTO_AVAILABLE:
            logger.error("msoffcrypto-tool not available for password-protected files")
            return file_path
        
        decrypted_path = file_path + '.decrypted'
        
        for password in passwords:
            try:
                with open(file_path, 'rb') as f:
                    office_file = msoffcrypto.OfficeFile(f)
                    office_file.load_key(password=password)
                    
                    with open(decrypted_path, 'wb') as decrypted_f:
                        office_file.decrypt(decrypted_f)
                    
                    logger.info(f"Successfully decrypted file with password")
                    return decrypted_path
            except Exception as e:
                logger.debug(f"Failed to decrypt with password: {e}")
                continue
        
        logger.error("Failed to decrypt file with any provided password")
        return file_path
    
    @staticmethod
    def _extract_docx_content(docx_path: str, node: Node) -> List[Node]:
        """Extract content from DOCX file"""
        nodes = []
        
        try:
            doc = docx.Document(docx_path)
            text_content = []
            
            # 限制处理的段落数量，根据页数估算
            # 假设每页约有20个段落
            max_paragraphs = node.word_max_pages * 20
            for i, para in enumerate(doc.paragraphs):
                if i >= max_paragraphs:
                    break
                text_content.append(para.text)
            
            # Extract text content
            separator = "\n"
            joined_text_content = separator.join(text_content)
            if joined_text_content.strip():
                t_node = Node()
                t_node.id = 0
                t_node.content = Data(type="TEXT", content=encode_binary(joined_text_content))
                t_node.prev = node
                t_node.inherit_limits(node)
                nodes.append(t_node)
            
            # Extract media files from DOCX
            try:
                with zipfile.ZipFile(docx_path, 'r') as docx_zip:
                    all_files = docx_zip.namelist()
                    for file1 in all_files:
                        if file1.startswith('word/media/') and not file1.__eq__('word/media/'):
                            t_node = Node()
                            file_name = os.path.basename(file1)
                            file_byte = docx_zip.read(file1)
                            t_node.content = File(
                                path=file_name,
                                name=file_name,
                                content=file_byte
                            )
                            t_node.prev = node
                            t_node.inherit_limits(node)
                            nodes.append(t_node)
            except Exception as e:
                logger.warning(f"Failed to extract media files: {e}")
            
        except Exception as e:
            logger.error(f"Failed to extract DOCX content: {e}")
            traceback.print_exc()
        
        return nodes
    
    @staticmethod
    def _extract_doc_content(doc_path: str, node: Node) -> List[Node]:
        """Extract content from DOC file using olefile or other methods"""
        nodes = []
        converted_docx_path = None
        
        try:
            # First try to convert DOC to DOCX
            docx_path = WordExtractor._convert_doc_to_docx(doc_path)
            if docx_path != doc_path and os.path.exists(docx_path):
                converted_docx_path = docx_path
                return WordExtractor._extract_docx_content(docx_path, node)
        finally:
            # Clean up converted file
            if converted_docx_path and os.path.exists(converted_docx_path):
                try:
                    os.remove(converted_docx_path)
                except Exception as e:
                    logger.warning(f"Failed to remove converted DOCX file: {e}")
        
        # If conversion failed, try to extract text using olefile
        if OLEFILE_AVAILABLE:
            try:
                # This is a basic implementation - olefile can read OLE structure
                # but text extraction from DOC is complex
                if olefile.isOleFile(doc_path):
                    logger.info("DOC file detected, but text extraction is limited")
                    # For now, just create a placeholder indicating the file type
                    t_node = Node()
                    t_node.id = 0
                    t_node.content = Data(type="TEXT", content=encode_binary("[DOC file detected - content extraction requires conversion]"))
                    t_node.prev = node
                    t_node.inherit_limits(node)
                    nodes.append(t_node)
            except Exception as e:
                logger.error(f"Failed to process DOC file: {e}")
        
        return nodes
    
    @staticmethod
    def extract_word_file(node: Node) -> List[Node]:
        node.meta.map_bool["is_encrypted"] = False
        nodes = []
        
        if isinstance(node.content, File):
            file = node.content
        elif isinstance(node.content, Data):
            logger.error("extract_word_file enter Data type")
            return nodes
        else:
            return nodes
        
        tmp_files = []
        
        try:
            # Create temporary file
            file_path = '/tmp/' + uuid.uuid4().__str__()
            with open(file_path, 'wb') as f:
                f.write(file.content)
            tmp_files.append(file_path)
            
            current_file_path = file_path
            
            # Check if file is encrypted by trying to open it
            is_encrypted = False
            try:
                if node.type == Types.DOCX:
                    # Try to open DOCX file
                    with zipfile.ZipFile(current_file_path, 'r'):
                        pass  # If this succeeds, file is not encrypted
                elif node.type == Types.DOC:
                    # For DOC files, try to check if it's encrypted
                    # This is a simplified check
                    pass
            except (zipfile.BadZipFile, zipfile.LargeZipFile):
                is_encrypted = True
            except Exception as e:
                logger.debug(f"File check exception: {e}")
                is_encrypted = True
            
            # Try to decrypt if passwords are provided and file seems encrypted
            if is_encrypted and node.passwords:
                node.meta.map_bool["is_encrypted"] = True
                decrypted_path = WordExtractor._decrypt_file(current_file_path, node.passwords)
                if decrypted_path != current_file_path:
                    tmp_files.append(decrypted_path)
                    current_file_path = decrypted_path
                    is_encrypted = False
            
            # If still encrypted and no passwords work, return empty
            if is_encrypted:
                logger.warning("File appears to be encrypted but no valid password provided")
                return nodes
            
            # Extract content based on file type
            if node.type == Types.DOCX:
                nodes = WordExtractor._extract_docx_content(current_file_path, node)
            elif node.type == Types.DOC:
                nodes = WordExtractor._extract_doc_content(current_file_path, node)
            
        except Exception as e:
            logger.error(f"Failed to extract Word file: {e}")
            traceback.print_exc()
        finally:
            # Clean up temporary files
            for tmp_file in tmp_files:
                if os.path.exists(tmp_file):
                    try:
                        os.remove(tmp_file)
                    except Exception as e:
                        logger.warning(f"Failed to remove temp file {tmp_file}: {e}")
        
        return nodes