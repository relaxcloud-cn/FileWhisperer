import time
from typing import List
import traceback
from .dt import Node
from .types import Types 
from .extractor import Extractor
from .analyzer import Analyzer

class Flavors:
    def __init__(self, extractor: Extractor):
        self.extractor = extractor
        
        self.flavor_extractors = {
            Types.TEXT_PLAIN: [
                ("url_extractor", self.extractor.extract_urls)
            ],
            Types.IMAGE: [
                ("qrcode_extractor", self.extractor.extract_qrcode),
                ("ocr_extractor", self.extractor.extract_ocr)
            ],
            Types.TEXT_HTML: [
                ("html_extractor", self.extractor.extract_html)
            ],
            Types.COMPRESSED_FILE: [
                ("compressed_file_extractor", self.extractor.extract_compressed_file) 
            ],
            Types.DOC: [
                ("word_file_extractor", self.extractor.extract_word_file) 
            ],
            Types.DOCX: [
                ("word_file_extractor", self.extractor.extract_word_file) 
            ],
            Types.PDF: [
                ("pdf_extractor", self.extractor.extract_pdf_file) 
            ],
            Types.EMAIL: [
                ("email_extractor", self.extractor.extract_email_file)
            ]
        }

        self.flavor_analyzers = {
            Types.COMPRESSED_FILE: [
                ("compressed_file_analyzer", Analyzer.analyze_compressed_file)
            ]
        }
    
    def extract(self, node: Node) -> List[Node]:
        nodes = []
        
        if not node:
            return nodes
            
        extractors = self.flavor_extractors.get(node.type, [])
        
        for name, extractor in extractors:
            start = time.time()
            try:
                extracted = extractor(node)
                nodes.extend(extracted) 
            except Exception as e:
                traceback.print_exc()
                node.meta.map_string["error_message"] += f"{name}: {str(e)};"
            duration = int((time.time() - start) * 1_000_000)
            node.meta.map_number[f"microsecond_{name}"] = duration
            
        return nodes
    
    def analyze(self, node: Node):
        if not node:
            return
            
        analyzers = self.flavor_analyzers.get(node.type, [])
        
        for name, analyzer in analyzers:
            start = time.time()
            try:
                analyzer(node)
            except Exception as e:
                traceback.print_exc()
                node.meta.map_string["error_message"] += f"{name}: {str(e)};"
            duration = int((time.time() - start) * 1_000_000)
            node.meta.map_number[f"microsecond_{name}"] = duration
            