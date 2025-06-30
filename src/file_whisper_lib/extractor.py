"""
文件提取器主模块 - 统一入口点
"""
from typing import List

from .extractors.url_extractor import URLExtractor
from .extractors.qrcode_extractor import QRCodeExtractor
from .extractors.ocr_extractor import OCRExtractor
from .extractors.html_extractor import HTMLExtractor
from .extractors.archive_extractor import ArchiveExtractor
from .extractors.word_extractor import WordExtractor
from .extractors.pdf_extractor import PDFExtractor
from .extractors.email_extractor import EmailExtractor
from .dt import Node


class Extractor:
    """
    主提取器类，提供统一的接口访问所有提取功能
    """
    
    # URL提取
    @staticmethod
    def extract_urls(node: Node) -> List[Node]:
        return URLExtractor.extract_urls(node)
    
    @staticmethod
    def extract_urls_from_text(text: str) -> List[str]:
        return URLExtractor.extract_urls_from_text(text)
    
    # 二维码提取
    @staticmethod
    def extract_qrcode(node: Node) -> List[Node]:
        return QRCodeExtractor.extract_qrcode(node)
    
    # OCR提取
    @staticmethod
    def extract_ocr(node: Node) -> List[Node]:
        return OCRExtractor.extract_ocr(node)
    
    # HTML处理
    @staticmethod
    def extract_html(node: Node) -> List[Node]:
        return HTMLExtractor.extract_html(node)
    
    @staticmethod
    def extract_text_from_html(html: str) -> str:
        return HTMLExtractor.extract_text_from_html(html)
    
    @staticmethod
    def extract_urls_from_html(html: str) -> list:
        return HTMLExtractor.extract_urls_from_html(html)
    
    @staticmethod
    def extract_img_from_html(html: str) -> list:
        return HTMLExtractor.extract_img_from_html(html)
    
    # 压缩文件处理
    @staticmethod
    def extract_compressed_file(node: Node) -> List[Node]:
        return ArchiveExtractor.extract_compressed_file(node)
    
    @staticmethod
    def extract_files_from_data(data: bytes, password: str = ""):
        return ArchiveExtractor.extract_files_from_data(data, password)
    
    # Word文档处理
    @staticmethod
    def extract_word_file(node: Node) -> List[Node]:
        return WordExtractor.extract_word_file(node)
    
    # PDF文档处理
    @staticmethod
    def extract_pdf_file(node: Node) -> List[Node]:
        return PDFExtractor.extract_pdf_file(node)
    
    # 邮件处理
    @staticmethod
    def extract_email_file(node: Node) -> List[Node]:
        return EmailExtractor.extract_email_file(node)