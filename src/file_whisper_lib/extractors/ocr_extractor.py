"""
OCR文字识别模块
"""
from typing import List
from loguru import logger
from paddleocr import PaddleOCR
import traceback
import os
import logging
import tempfile
import uuid

from ..dt import Node, File, Data
from .utils import encode_binary

# 环境变量和日志设置
os.environ["TOKENIZERS_PARALLELISM"] = "false"  
logging.getLogger("transformers").setLevel(logging.ERROR)
logging.getLogger("transformers.modeling_utils").setLevel(logging.ERROR)
logging.getLogger("transformers.configuration_utils").setLevel(logging.ERROR)
logging.getLogger("PIL.TiffImagePlugin").setLevel(logging.ERROR)


class OCRExtractor:
    def __init__(self):
        self.paddle_ocr = None
        self._initialize_paddle_ocr()
    
    def _initialize_paddle_ocr(self):
        """初始化OCR模型（仅在第一次需要时加载）"""
        if self.paddle_ocr is None:
            try:
                logger.info("Initializing PaddleOCR model (first time only)...")
                self.paddle_ocr = PaddleOCR(
                                use_doc_orientation_classify=False,
                                use_doc_unwarping=False,
                                use_textline_orientation=False)
                logger.info("PaddleOCR model initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize PaddleOCR: {e}")
                logger.error(traceback.format_exc())
                return False
        
        return True

    def _recognize_text_from_image(self, image_data: bytes) -> str:
        """从图像数据中识别文本"""
        temp_file_path = None
        try:
            # 初始化PaddleOCR模型（仅在首次调用时）
            initialization_success = self._initialize_paddle_ocr()
            if not initialization_success:
                logger.error("Failed to initialize OCR model")
                return ""
            
            # 生成临时文件路径
            temp_file_name = f"ocr_temp_{uuid.uuid4().hex}.png"
            temp_file_path = os.path.join(tempfile.gettempdir(), temp_file_name)
            
            # 保存图像数据到临时文件
            with open(temp_file_path, 'wb') as f:
                f.write(image_data)
            
            logger.debug(f"Temporary image saved to: {temp_file_path}")
            
            # 使用PaddleOCR的predict方法处理图像文件
            result = self.paddle_ocr.predict(input=temp_file_path)
            
            if result:
                text_results = []
                for res in result:
                    # OCRResult对象可以像字典一样访问
                    if 'rec_texts' in res:
                        ocr_texts = res['rec_texts']
                        text_results.extend(ocr_texts)
                
                if text_results:
                    extracted_text = '\n'.join(text_results)
                    logger.info(f"OCR completed successfully, extracted {len(text_results)} text items")
                    return extracted_text
            
            return ""
            
        except Exception as e:
            logger.error(f"OCR text recognition failed: {str(e)}")
            logger.error(traceback.format_exc())
            return ""
        finally:
            # 清理临时文件
            if temp_file_path and os.path.exists(temp_file_path):
                try:
                    os.remove(temp_file_path)
                    logger.debug(f"Temporary file cleaned up: {temp_file_path}")
                except Exception as e:
                    logger.warning(f"Failed to cleanup temporary file {temp_file_path}: {e}")

    def _create_ocr_node(self, extracted_text: str, parent_node: Node) -> Node:
        """创建包含OCR结果的节点"""
        t_node = Node()
        t_node.id = 0
        t_node.content = Data(type="OCR", content=encode_binary(extracted_text))
        t_node.prev = parent_node
        t_node.inherit_limits(parent_node)
        return t_node

    def extract_ocr(self, node: Node) -> List[Node]:
        """从节点中提取OCR文本并创建新节点"""
        nodes = []
        
        try:
            if isinstance(node.content, File):
                data = node.content.content
                
                # 识别图像中的文本
                extracted_text = self._recognize_text_from_image(data)
                
                if extracted_text:
                    # 创建包含OCR结果的节点
                    ocr_node = self._create_ocr_node(extracted_text, node)
                    nodes.append(ocr_node)
                    
            elif isinstance(node.content, Data):
                logger.debug("extract_ocr enter Data type")
                
        except Exception as e:
            logger.error(f"OCR processing failed: {str(e)}")
            logger.error(traceback.format_exc())
            
        return nodes