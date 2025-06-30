"""
OCR文字识别模块
"""
from io import BytesIO
import cv2
import numpy as np
from typing import List
from loguru import logger
from PIL import Image
from paddleocr import PaddleOCR
import traceback
import os
import logging

from ..dt import Node, File, Data
from .utils import encode_binary

# 环境变量和日志设置
os.environ["TOKENIZERS_PARALLELISM"] = "false"  
logging.getLogger("transformers").setLevel(logging.ERROR)
logging.getLogger("transformers.modeling_utils").setLevel(logging.ERROR)
logging.getLogger("transformers.configuration_utils").setLevel(logging.ERROR)
logging.getLogger("PIL.TiffImagePlugin").setLevel(logging.ERROR)


class OCRExtractor:
    paddle_ocr = None
    
    @staticmethod
    def _initialize_paddle_ocr():
        """初始化OCR模型（仅在第一次需要时加载）"""
        if OCRExtractor.paddle_ocr is None:
            try:
                logger.info("Initializing PaddleOCR model (first time only)...")
                OCRExtractor.paddle_ocr = PaddleOCR(use_textline_orientation=True, lang='ch', use_gpu=False, 
                                          model_dir="/root/.paddleocr")
                logger.info("PaddleOCR model initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize PaddleOCR: {e}")
                logger.error(traceback.format_exc())
                return False
        
        return True

    @staticmethod
    def _recognize_text_from_image(image_data: bytes) -> str:
        """从图像数据中识别文本"""
        try:
            # 初始化PaddleOCR模型（仅在首次调用时）
            initialization_success = OCRExtractor._initialize_paddle_ocr()
            if not initialization_success:
                logger.error("Failed to initialize OCR model")
                return ""
            
            # 打开图像
            image = Image.open(BytesIO(image_data))
            
            # 转换图像为numpy数组，PaddleOCR需要numpy数组
            image_np = np.array(image)
            
            # 检查图像是否为RGBA并转换为RGB
            if len(image_np.shape) == 3 and image_np.shape[-1] == 4:
                image_np = cv2.cvtColor(image_np, cv2.COLOR_RGBA2RGB)
            
            # 执行OCR识别
            result = OCRExtractor.paddle_ocr.ocr(image_np, cls=True)
            
            if result:
                text_results = []
                for line in result:
                    if line:  # 检查line不为None
                        for item in line:
                            if len(item) >= 2:
                                text_results.append(item[1][0])
                
                if text_results:
                    extracted_text = '\n'.join(text_results)
                    logger.info(f"OCR completed successfully, extracted {len(text_results)} text items")
                    return extracted_text
            
            return ""
            
        except Exception as e:
            logger.error(f"OCR text recognition failed: {str(e)}")
            logger.error(traceback.format_exc())
            return ""

    @staticmethod
    def _create_ocr_node(extracted_text: str, parent_node: Node) -> Node:
        """创建包含OCR结果的节点"""
        t_node = Node()
        t_node.id = 0
        t_node.content = Data(type="OCR", content=encode_binary(extracted_text))
        t_node.prev = parent_node
        t_node.inherit_limits(parent_node)
        return t_node

    @staticmethod
    def extract_ocr(node: Node) -> List[Node]:
        """从节点中提取OCR文本并创建新节点"""
        nodes = []
        
        try:
            if isinstance(node.content, File):
                data = node.content.content
                
                # 识别图像中的文本
                extracted_text = OCRExtractor._recognize_text_from_image(data)
                
                if extracted_text:
                    # 创建包含OCR结果的节点
                    ocr_node = OCRExtractor._create_ocr_node(extracted_text, node)
                    nodes.append(ocr_node)
                    
            elif isinstance(node.content, Data):
                logger.debug("extract_ocr enter Data type")
                
        except Exception as e:
            logger.error(f"OCR processing failed: {str(e)}")
            logger.error(traceback.format_exc())
            
        return nodes