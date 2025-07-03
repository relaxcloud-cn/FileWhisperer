"""
URL提取功能模块
"""
import re
from typing import List
from loguru import logger

from ..dt import Node, File, Data
from .utils import encode_binary, decode_binary


class URLExtractor:
    
    @staticmethod
    def extract_urls(node: Node) -> List[Node]:
        nodes = []
        text = ""
        
        try:
            if isinstance(node.content, File):
                logger.debug(f"Node[{node.id}] file {node.content.mime_type}")
                text = decode_binary(node.content.content)
            elif isinstance(node.content, Data):
                logger.debug(f"Node[{node.id}] data {node.content.type}")
                text = decode_binary(node.content.content)
            
            urls = URLExtractor.extract_urls_from_text(text)
            logger.debug(f"Node[{node.id}] Number of urls: {len(urls)}")
            
            for url in urls:
                t_node = Node()
                t_node.id = 0
                t_node.content = Data(type="URL", content=encode_binary(url))
                t_node.prev = node
                t_node.inherit_limits(node)
                nodes.append(t_node)
                
        except Exception as e:
            logger.error(f"Error extracting URLs: {str(e)}")
            
        return nodes

    @staticmethod
    def extract_urls_from_text(text: str) -> List[str]:
        url_pattern = r"https?://(?:[-\w.])+(?::[0-9]+)?(?:/(?:[\w/_.])*(?:\?(?:[\w&=%.])*)?(?:#(?:[\w.])*)?)?(?![,\u3001\uff0c])"
        urls = re.findall(url_pattern, text)
        return list(set(urls))