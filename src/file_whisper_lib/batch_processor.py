"""
批量并行处理器 - 实现同类型文件的批量并行处理
"""
import time
from typing import List, Dict, Any, Tuple, Optional
from concurrent.futures import Future, as_completed
from loguru import logger

from .dt import Node, Data
from .process_pool import get_process_pool
from .process_workers import process_ocr_task, process_word_task, process_pdf_task
from .types import Types
from .extractors.utils import encode_binary


class BatchProcessor:
    """批量处理器 - 负责收集同类型文件并批量提交到进程池"""
    
    def __init__(self):
        self.process_pool = get_process_pool()
        
    def collect_and_process_batch(self, nodes: List[Node], node_type: Types) -> Dict[int, List[Node]]:
        """
        收集指定类型的节点，批量提交处理，返回处理结果
        """
        # 筛选出指定类型的节点
        target_nodes = [node for node in nodes if node.type == node_type]
        
        if not target_nodes:
            return {}
        
        logger.info(f"Found {len(target_nodes)} nodes of type {node_type.name} for batch processing")
        
        if node_type == Types.IMAGE:
            return self._batch_process_ocr(target_nodes)
        elif node_type in [Types.DOC, Types.DOCX]:
            return self._batch_process_word(target_nodes)
        elif node_type == Types.PDF:
            return self._batch_process_pdf(target_nodes)
        else:
            logger.warning(f"Batch processing not implemented for type {node_type.name}")
            return {}
    
    def _batch_process_ocr(self, image_nodes: List[Node]) -> Dict[int, List[Node]]:
        """批量处理OCR任务"""
        if not self.process_pool.is_pool_enabled("ocr"):
            logger.info("OCR process pool not enabled, skipping batch processing")
            return {}
        
        results = {}
        futures_to_nodes = {}
        
        logger.info(f"Submitting {len(image_nodes)} OCR tasks to process pool")
        start_time = time.time()
        
        # 批量提交OCR任务
        for node in image_nodes:
            if hasattr(node.content, 'content'):
                future = self.process_pool.submit_task("ocr", process_ocr_task, node.content.content)
                if future:
                    futures_to_nodes[future] = node
                else:
                    logger.warning(f"Failed to submit OCR task for node {node.id}")
        
        # 收集结果
        completed_count = 0
        for future in as_completed(futures_to_nodes.keys(), timeout=120):  # 2分钟总超时
            node = futures_to_nodes[future]
            try:
                extracted_text = future.result()
                if extracted_text:
                    # 创建OCR结果节点
                    result_nodes = self._create_ocr_result_nodes(extracted_text, node)
                    results[node.id] = result_nodes
                    completed_count += 1
                    logger.debug(f"OCR completed for node {node.id}")
                else:
                    logger.warning(f"OCR returned empty result for node {node.id}")
                    results[node.id] = []
            except Exception as e:
                logger.error(f"OCR processing failed for node {node.id}: {e}")
                results[node.id] = []
        
        processing_time = time.time() - start_time
        logger.info(f"Batch OCR processing completed: {completed_count}/{len(image_nodes)} successful in {processing_time:.2f}s")
        
        return results
    
    def _batch_process_word(self, word_nodes: List[Node]) -> Dict[int, List[Node]]:
        """批量处理Word文档"""
        if not self.process_pool.is_pool_enabled("word"):
            logger.info("Word process pool not enabled, skipping batch processing")
            return {}
        
        results = {}
        futures_to_nodes = {}
        
        logger.info(f"Submitting {len(word_nodes)} Word processing tasks to process pool")
        start_time = time.time()
        
        # 批量提交Word处理任务
        for node in word_nodes:
            if hasattr(node.content, 'content'):
                max_pages = getattr(node, 'word_max_pages', 10)
                future = self.process_pool.submit_task("word", process_word_task, node.content.content, max_pages)
                if future:
                    futures_to_nodes[future] = node
                else:
                    logger.warning(f"Failed to submit Word task for node {node.id}")
        
        # 收集结果
        completed_count = 0
        for future in as_completed(futures_to_nodes.keys(), timeout=300):  # 5分钟总超时
            node = futures_to_nodes[future]
            try:
                content, metadata = future.result()
                if content:
                    # 创建Word处理结果节点
                    result_nodes = self._create_word_result_nodes(content, metadata, node)
                    results[node.id] = result_nodes
                    completed_count += 1
                    logger.debug(f"Word processing completed for node {node.id}")
                else:
                    logger.warning(f"Word processing returned empty result for node {node.id}")
                    results[node.id] = []
            except Exception as e:
                logger.error(f"Word processing failed for node {node.id}: {e}")
                results[node.id] = []
        
        processing_time = time.time() - start_time
        logger.info(f"Batch Word processing completed: {completed_count}/{len(word_nodes)} successful in {processing_time:.2f}s")
        
        return results
    
    def _batch_process_pdf(self, pdf_nodes: List[Node]) -> Dict[int, List[Node]]:
        """批量处理PDF文档"""
        if not self.process_pool.is_pool_enabled("pdf"):
            logger.info("PDF process pool not enabled, skipping batch processing")
            return {}
        
        results = {}
        futures_to_nodes = {}
        
        logger.info(f"Submitting {len(pdf_nodes)} PDF processing tasks to process pool")
        start_time = time.time()
        
        # 批量提交PDF处理任务
        for node in pdf_nodes:
            if hasattr(node.content, 'content'):
                max_pages = getattr(node, 'pdf_max_pages', 10)
                future = self.process_pool.submit_task("pdf", process_pdf_task, node.content.content, max_pages)
                if future:
                    futures_to_nodes[future] = node
                else:
                    logger.warning(f"Failed to submit PDF task for node {node.id}")
        
        # 收集结果
        completed_count = 0
        for future in as_completed(futures_to_nodes.keys(), timeout=300):  # 5分钟总超时
            node = futures_to_nodes[future]
            try:
                content, metadata = future.result()
                if content:
                    # 创建PDF处理结果节点
                    result_nodes = self._create_pdf_result_nodes(content, metadata, node)
                    results[node.id] = result_nodes
                    completed_count += 1
                    logger.debug(f"PDF processing completed for node {node.id}")
                else:
                    logger.warning(f"PDF processing returned empty result for node {node.id}")
                    results[node.id] = []
            except Exception as e:
                logger.error(f"PDF processing failed for node {node.id}: {e}")
                results[node.id] = []
        
        processing_time = time.time() - start_time
        logger.info(f"Batch PDF processing completed: {completed_count}/{len(pdf_nodes)} successful in {processing_time:.2f}s")
        
        return results
    
    def _create_ocr_result_nodes(self, extracted_text: str, parent_node: Node) -> List[Node]:
        """创建OCR结果节点"""
        from .dt import Node, Data
        
        nodes = []
        if extracted_text.strip():
            ocr_node = Node()
            ocr_node.id = 0
            ocr_node.content = Data(type="OCR", content=encode_binary(extracted_text))
            ocr_node.prev = parent_node
            ocr_node.inherit_limits(parent_node)
            nodes.append(ocr_node)
        
        return nodes
    
    def _create_word_result_nodes(self, content: str, metadata: Dict[str, Any], parent_node: Node) -> List[Node]:
        """创建Word处理结果节点"""
        from .dt import Node, Data
        
        nodes = []
        if content.strip():
            text_node = Node()
            text_node.id = 0
            text_node.content = Data(type="TEXT", content=encode_binary(content))
            text_node.prev = parent_node
            text_node.inherit_limits(parent_node)
            
            # 添加元数据
            for key, value in metadata.items():
                if isinstance(value, str):
                    text_node.meta.map_string[key] = value
                elif isinstance(value, (int, float)):
                    text_node.meta.map_number[key] = value
                elif isinstance(value, bool):
                    text_node.meta.map_bool[key] = value
            
            nodes.append(text_node)
        
        return nodes
    
    def _create_pdf_result_nodes(self, content: str, metadata: Dict[str, Any], parent_node: Node) -> List[Node]:
        """创建PDF处理结果节点"""
        from .dt import Node, Data
        
        nodes = []
        if content.strip():
            text_node = Node()
            text_node.id = 0
            text_node.content = Data(type="TEXT", content=encode_binary(content))
            text_node.prev = parent_node
            text_node.inherit_limits(parent_node)
            
            # 添加元数据
            for key, value in metadata.items():
                if isinstance(value, str):
                    text_node.meta.map_string[key] = value
                elif isinstance(value, (int, float)):
                    text_node.meta.map_number[key] = value
                elif isinstance(value, bool):
                    text_node.meta.map_bool[key] = value
            
            nodes.append(text_node)
        
        return nodes
    
    def get_batch_status(self) -> Dict[str, Any]:
        """获取批量处理状态"""
        return {
            "process_pool_status": self.process_pool.get_pool_status(),
            "batch_processor_active": True
        }