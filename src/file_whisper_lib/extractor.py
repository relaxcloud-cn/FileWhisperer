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
    
    def __init__(self):
        self.ocr_extractor = OCRExtractor()
    
    # URL提取
    def extract_urls(self, node: Node) -> List[Node]:
        return URLExtractor.extract_urls(node)
    
    def extract_urls_from_text(self, text: str) -> List[str]:
        return URLExtractor.extract_urls_from_text(text)
    
    # 二维码提取
    def extract_qrcode(self, node: Node) -> List[Node]:
        return QRCodeExtractor.extract_qrcode(node)
    
    # OCR提取
    def extract_ocr(self, node: Node) -> List[Node]:
        return self.ocr_extractor.extract_ocr(node)
    
    # HTML处理
    def extract_html(self, node: Node) -> List[Node]:
        return HTMLExtractor.extract_html(node)
    
    def extract_text_from_html(self, html: str) -> str:
        return HTMLExtractor.extract_text_from_html(html)
    
    def extract_urls_from_html(self, html: str) -> list:
        return HTMLExtractor.extract_urls_from_html(html)
    
    def extract_img_from_html(self, html: str) -> list:
        return HTMLExtractor.extract_img_from_html(html)
    
    # 压缩文件处理
    def extract_compressed_file(self, node: Node) -> List[Node]:
        return ArchiveExtractor.extract_compressed_file(node)
    
    def extract_files_from_data(self, data: bytes, password: str = ""):
        return ArchiveExtractor.extract_files_from_data(data, password)
    
    # Word文档处理
    def extract_word_file(self, node: Node) -> List[Node]:
        return WordExtractor.extract_word_file(node)
    
    # PDF文档处理
    def extract_pdf_file(self, node: Node) -> List[Node]:
        return PDFExtractor.extract_pdf_file(node)
    
    # 邮件处理
    def extract_email_file(self, node: Node) -> List[Node]:
        return EmailExtractor.extract_email_file(node)