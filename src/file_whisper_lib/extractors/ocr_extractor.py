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
import torch
import paddle
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
    paddle_ocr_gpu = None
    paddle_ocr_cpu = None
    gpu_available = None
    
    @staticmethod
    def _initialize_paddle_ocr():
        """初始化OCR模型（仅在第一次需要时加载）"""
        if OCRExtractor.gpu_available is None:
            try:
                gpu_count = paddle.device.get_device_count("gpu")
                OCRExtractor.gpu_available = gpu_count > 0
                logger.info(f"PaddlePaddle detected {gpu_count} GPU(s), gpu_available={OCRExtractor.gpu_available}")
                
                if OCRExtractor.gpu_available:
                    device_info = paddle.device.get_device()
                    logger.info(f"PaddlePaddle using device: {device_info}")
            except Exception as e:
                logger.warning(f"Error checking GPU availability with Paddle: {e}")
                OCRExtractor.gpu_available = torch.cuda.is_available()
                logger.info(f"Falling back to PyTorch for GPU detection: {OCRExtractor.gpu_available}")
        
        # 初始化GPU版本的PaddleOCR
        if OCRExtractor.gpu_available and OCRExtractor.paddle_ocr_gpu is None:
            try:
                logger.info("Initializing GPU PaddleOCR model (first time only)...")
                paddle.device.set_device('gpu:0')
                OCRExtractor.paddle_ocr_gpu = PaddleOCR(use_angle_cls=True, lang='ch', use_gpu=True, 
                                               model_dir="/root/.paddleocr", show_log=True)
                logger.info("GPU PaddleOCR model initialized successfully")
            except Exception as e:
                logger.warning(f"Failed to initialize GPU PaddleOCR: {e}. Will use CPU version instead.")
                logger.error(traceback.format_exc())
                OCRExtractor.gpu_available = False
        
        # 初始化CPU版本的PaddleOCR
        if OCRExtractor.paddle_ocr_cpu is None:
            try:
                logger.info("Initializing CPU PaddleOCR model (first time only)...")
                paddle.device.set_device('cpu')
                OCRExtractor.paddle_ocr_cpu = PaddleOCR(use_angle_cls=True, lang='ch', use_gpu=False, 
                                              model_dir="/root/.paddleocr", show_log=False)
                logger.info("CPU PaddleOCR model initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize CPU PaddleOCR: {e}")
                logger.error(traceback.format_exc())
                return False
        
        return True

    @staticmethod
    def extract_ocr(node: Node) -> List[Node]:
        nodes = []
        
        try:
            if isinstance(node.content, File):
                data = node.content.content
                
                # 初始化PaddleOCR模型（仅在首次调用时）
                initialization_success = OCRExtractor._initialize_paddle_ocr()
                if not initialization_success:
                    logger.error("Failed to initialize any OCR models")
                    return nodes
                
                extracted_text = ""
                
                # 打开图像
                image = Image.open(BytesIO(data))
                
                # 转换图像为numpy数组，PaddleOCR需要numpy数组
                image_np = np.array(image)
                
                # 检查图像是否为RGBA并转换为RGB
                if len(image_np.shape) == 3 and image_np.shape[-1] == 4:
                    image_np = cv2.cvtColor(image_np, cv2.COLOR_RGBA2RGB)
                
                # 尝试使用GPU版本的PaddleOCR
                if OCRExtractor.gpu_available and OCRExtractor.paddle_ocr_gpu is not None:
                    try:
                        paddle.device.set_device('gpu:0')
                        logger.info("Using GPU PaddleOCR")
                        result = OCRExtractor.paddle_ocr_gpu.ocr(image_np, cls=True)
                        
                        if result:
                            text_results = []
                            for line in result:
                                for item in line:
                                    if len(item) >= 2:
                                        text_results.append(item[1][0])
                            
                            extracted_text = '\n'.join(text_results)
                            logger.info(f"GPU OCR completed successfully, extracted {len(text_results)} text items")
                    except Exception as e:
                        logger.warning(f"Error when using GPU PaddleOCR: {e}. Falling back to CPU PaddleOCR.")
                        logger.error(traceback.format_exc())
                
                # 如果GPU OCR失败或不可用，回退到CPU版本的PaddleOCR
                if not extracted_text and OCRExtractor.paddle_ocr_cpu is not None:
                    try:
                        paddle.device.set_device('cpu')
                        logger.info("Using CPU PaddleOCR")
                        result = OCRExtractor.paddle_ocr_cpu.ocr(image_np, cls=True)
                        
                        if result:
                            text_results = []
                            for line in result:
                                for item in line:
                                    if len(item) >= 2:
                                        text_results.append(item[1][0])
                            
                            extracted_text = '\n'.join(text_results)
                            logger.info(f"CPU OCR completed successfully, extracted {len(text_results)} text items")
                    except Exception as e:
                        logger.error(f"CPU PaddleOCR processing failed: {e}")
                        logger.error(traceback.format_exc())
                
                if extracted_text:
                    t_node = Node()
                    t_node.id = 0
                    t_node.content = Data(type="OCR", content=encode_binary(extracted_text))
                    t_node.prev = node
                    t_node.inherit_limits(node)
                    nodes.append(t_node)
                    
            elif isinstance(node.content, Data):
                logger.debug("extract_ocr enter Data type")
                
        except Exception as e:
            logger.error(f"OCR processing failed: {str(e)}")
            logger.error(traceback.format_exc())
            
        return nodes