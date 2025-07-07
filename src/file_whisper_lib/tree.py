import hashlib
import magic
import uuid
import os
import chardet
from typing import Optional
from .dt import Node, Meta, File, Data

from .flavors import Flavors
from .extractor import Extractor

from snowflake import SnowflakeGenerator
snowflakegen = SnowflakeGenerator(42)

class Tree:
    def __init__(self):
        self.root: Optional[Node] = None
        self.extractor = Extractor()
        self.flavors = Flavors(self.extractor)
    
    def clear_state(self):
        """清除Tree的状态，用于在处理完一个请求后重置"""
        self.root = None

    def meta_detect_encoding(self, meta: Meta, data: bytes):
        if not isinstance(data, bytes):
            meta.map_string["encoding"] = "NONE"
            meta.map_string["encoding_detect_msg"] = "Input data is not bytes type"
            return
            
        try:
            if len(data) == 0:
                meta.map_string["encoding"] = "NONE" 
                meta.map_string["encoding_detect_msg"] = "Empty data"
                return
                
            results = chardet.detect(data)
            if results is None or results.get('encoding') is None:
                meta.map_string["encoding"] = "NONE"
                meta.map_string["encoding_detect_msg"] = "Could not detect encoding"
                return
                
            meta.map_string["encoding"] = results['encoding']
            meta.map_number["encoding_confidence"] = int(results['confidence'] * 100)
        except Exception as e:
            meta.map_string["encoding"] = "NONE"
            meta.map_string["encoding_detect_msg"] = f"Detection error: {str(e)}"
            return

        # for idx, tmp in enumerate(results):
        #     if idx == 0:
        #         meta.map_string["encoding"] = tmp['encoding']
        #         meta.map_number["encoding_confidence"] = int(tmp['confidence'] * 100)
        #     if idx > 3:
        #         break
        #     else:
        #         meta.map_string[f"encoding{idx+1}"] = tmp['encoding']
        #         meta.map_number[f"encoding_confidence{idx+1}"] = int(tmp['confidence'] * 100)

    def digest(self, node: Node):
        extracted_nodes = []
        
        if self.root is None:
            self.root = node

        node.uuid = str(uuid.uuid4())
        
        if node.id == 0:
            # Use a snowflake-like ID generator or similar
            # node.id = int(uuid.uuid4().int & (1<<63)-1)
            node.id = next(snowflakegen)

        meta = Meta()

        if isinstance(node.content, File):
            file = node.content
            file.size = len(file.content)
            # file.mime_type = mimetypes.guess_type(file.name)[0] or ""
            file.mime_type = get_mime_type(file.content)
            # Implement these hash functions as needed
            file.extension = get_extension(file.name)
            file.md5 = calculate_md5(file.content)
            file.sha256 = calculate_sha256(file.content)
            file.sha1 = calculate_sha1(file.content)
            node.set_type(file.mime_type, file.extension)
            # File 不探测编码, 费时
            # self.meta_detect_encoding(meta, file.content)
        
        elif isinstance(node.content, Data):
            data = node.content
            self.meta_detect_encoding(meta, data.content)
            node.set_type(data.type)

        node.meta = meta

        # Implement these functions as needed
        node.meta.map_string["error_message"] = ""
        self.flavors.analyze(node)
        nodes = self.flavors.extract(node)
        extracted_nodes.extend(nodes)

        node.children = extracted_nodes

        for child_node in extracted_nodes:
            self.digest(child_node)


# Helper functions to be implemented
def calculate_md5(data: bytes) -> str:
    return hashlib.md5(data).hexdigest()

def calculate_sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def calculate_sha1(data: bytes) -> str:
    return hashlib.sha1(data).hexdigest()

def get_mime_type(data: bytes):
    # text/x-makefile
    return magic.from_buffer(data, mime=True)

def get_mime_type_desc(data: bytes):
    # makefile script, ASCII text
    return magic.from_buffer(data)

def get_extension(filename):
    extension = os.path.splitext(filename)[1]
    extension = extension[1:]
    return extension
