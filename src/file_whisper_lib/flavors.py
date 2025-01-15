import time
from typing import List
from .dt import Node
from .types import Types 
from .extractor import Extractor

class Flavors:
    flavor_extractors = {
        Types.TEXT_PLAIN: [
            ("url_extractor", Extractor.extract_urls)
        ],
        Types.IMAGE: [
            ("qrcode_extractor", Extractor.extract_qrcode),
            ("ocr_extractor", Extractor.extract_ocr)
        ],
        Types.TEXT_HTML: [
            ("html_extractor", Extractor.extract_html)
        ],
        Types.COMPRESSED_FILE: [
            ("compressed_file_extractor", Extractor.extract_compressed_file) 
        ]
    }
    
    @staticmethod
    def extract(node: Node) -> List[Node]:
        nodes = []
        
        if not node:
            return nodes
            
        extractors = Flavors.flavor_extractors.get(node.type, [])
        
        for name, extractor in extractors:
            start = time.time()
            try:
                extracted = extractor(node)
                nodes.extend(extracted) 
            except Exception as e:
                node.meta.map_string["error_message"] = f"{name}: {str(e)};"
            duration = int((time.time() - start) * 1_000_000)
            node.meta.map_number[f"microsecond_{name}"] = duration
            
        return nodes