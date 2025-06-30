import hashlib
import magic
import uuid
import os
import chardet
from typing import Optional, List, Dict, Any
from collections import defaultdict
from .dt import Node, Meta, File, Data

from .flavors import Flavors
from .batch_processor import BatchProcessor
from .types import Types

from snowflake import SnowflakeGenerator
snowflakegen = SnowflakeGenerator(42)

class Tree:
    def __init__(self):
        self.root: Optional[Node] = None
        self.batch_processor = BatchProcessor()
        self.batch_enabled_types = {Types.IMAGE, Types.DOC, Types.DOCX, Types.PDF}  # 支持批量处理的类型

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
        """处理节点，支持批量并行处理"""
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
        Flavors.analyze(node)
        nodes = Flavors.extract(node)
        extracted_nodes.extend(nodes)

        node.children = extracted_nodes

        # 先处理所有子节点的基本信息（但不执行extractor）
        for child_node in extracted_nodes:
            self._initialize_child_node(child_node)
        
        # 批量处理支持的类型（在执行单个extractor之前）
        self._process_children_in_batches(node)
        
        # 继续处理剩余的子节点
        for child_node in extracted_nodes:
            if not child_node.children:  # 如果没有通过批量处理添加子节点，则进行常规处理
                self.digest(child_node)
    
    def _initialize_child_node(self, node: Node):
        """初始化子节点的基本信息，但不执行extractor"""
        if node.id == 0:
            node.id = next(snowflakegen)
        
        node.uuid = str(uuid.uuid4())
        
        meta = Meta()
        
        if isinstance(node.content, File):
            file = node.content
            file.size = len(file.content)
            file.mime_type = get_mime_type(file.content)
            file.extension = get_extension(file.name)
            file.md5 = calculate_md5(file.content)
            file.sha256 = calculate_sha256(file.content)
            file.sha1 = calculate_sha1(file.content)
            node.set_type(file.mime_type, file.extension)
        
        elif isinstance(node.content, Data):
            data = node.content
            self.meta_detect_encoding(meta, data.content)
            node.set_type(data.type)
        
        node.meta = meta
        node.meta.map_string["error_message"] = ""
    
    def _process_children_in_batches(self, parent_node: Node):
        """对子节点进行批量处理"""
        if not parent_node.children:
            return
        
        # 按类型分组收集子节点
        nodes_by_type = defaultdict(list)
        for child in parent_node.children:
            if child.type in self.batch_enabled_types:
                nodes_by_type[child.type].append(child)
        
        # 批量处理每种类型
        batch_results = {}
        for node_type, nodes in nodes_by_type.items():
            if len(nodes) > 1:  # 只有多个同类型文件才进行批量处理
                from loguru import logger
                logger.info(f"Starting batch processing for {len(nodes)} nodes of type {node_type.name}")
                
                batch_result = self.batch_processor.collect_and_process_batch(nodes, node_type)
                batch_results.update(batch_result)
        
        # 将批量处理的结果添加到对应的节点
        for child in parent_node.children:
            if child.id in batch_results:
                new_children = batch_results[child.id]
                child.children.extend(new_children)
                
                # 继续递归处理新添加的子节点
                for new_child in new_children:
                    self.digest(new_child)


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
