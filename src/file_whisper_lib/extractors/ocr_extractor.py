"""
OCR文字识别模块
"""
from typing import List
from loguru import logger
import easyocr
import traceback
import os
import logging
import tempfile
import uuid
import hashlib
import threading

# 修复 Pillow 10.0.0+ 兼容性问题
try:
    from PIL import Image
    if not hasattr(Image, 'ANTIALIAS'):
        Image.ANTIALIAS = Image.LANCZOS
except ImportError:
    pass

from ..dt import Node, File, Data
from .utils import encode_binary

# 全局实例计数器，用于在同一进程中分配不同的GPU/CPU
_instance_counter = 0
_counter_lock = threading.Lock()

# 环境变量和日志设置
os.environ["TOKENIZERS_PARALLELISM"] = "false"  
logging.getLogger("transformers").setLevel(logging.ERROR)
logging.getLogger("transformers.modeling_utils").setLevel(logging.ERROR)
logging.getLogger("transformers.configuration_utils").setLevel(logging.ERROR)
logging.getLogger("PIL.TiffImagePlugin").setLevel(logging.ERROR)


def _should_use_gpu() -> tuple[bool, int]:
    """
    根据环境变量决定是否使用GPU
    支持完全控制和基于进程百分比的部分控制
    返回 (是否使用GPU, 实例编号)
    """
    global _instance_counter
    
    # 获取当前实例编号
    with _counter_lock:
        current_instance = _instance_counter
        _instance_counter += 1
    
    # 检查是否强制使用CPU
    if os.environ.get("OCR_FORCE_CPU", "false").lower() == "true":
        return False, current_instance
    
    # 检查是否启用GPU
    gpu_enabled = os.environ.get("OCR_GPU_ENABLED", "false").lower() == "true"
    if not gpu_enabled:
        return False, current_instance
    
    # 检查GPU百分比设置
    gpu_percentage = float(os.environ.get("OCR_GPU_PERCENTAGE", "0"))
    if gpu_percentage <= 0:
        return False, current_instance
    elif gpu_percentage >= 100:
        return True, current_instance
    
    # 基于实例编号和TREE_POOL_SIZE进行百分比分配
    tree_pool_size = int(os.environ.get("TREE_POOL_SIZE", "1"))
    
    # 计算应该使用GPU的实例数量
    gpu_instance_count = max(1, int(tree_pool_size * gpu_percentage / 100))
    
    # 基于实例编号确定当前实例是否应该使用GPU
    should_use_gpu = current_instance < gpu_instance_count
    
    return should_use_gpu, current_instance


class OCRExtractor:
    def __init__(self):
        self.easy_ocr = None
        self.use_gpu, self.instance_id = _should_use_gpu()
        self._initialize_easy_ocr()
    
    def _initialize_easy_ocr(self):
        """初始化EasyOCR模型（仅在第一次需要时加载）"""
        if self.easy_ocr is None:
            try:
                device_type = "GPU" if self.use_gpu else "CPU"
                logger.info(f"Initializing EasyOCR model using {device_type} (Instance: {self.instance_id}, PID: {os.getpid()})...")
                
                # 支持中文和英文识别，根据use_gpu标志决定是否使用GPU
                self.easy_ocr = easyocr.Reader(['ch_sim', 'en'], gpu=self.use_gpu)
                
                logger.info(f"EasyOCR model initialized successfully using {device_type} (Instance: {self.instance_id})")
            except Exception as e:
                logger.error(f"Failed to initialize EasyOCR with {device_type} (Instance: {self.instance_id}): {e}")
                logger.error(traceback.format_exc())
                
                # 如果GPU初始化失败，尝试使用CPU
                if self.use_gpu:
                    logger.warning(f"GPU initialization failed for Instance {self.instance_id}, falling back to CPU...")
                    try:
                        self.use_gpu = False
                        self.easy_ocr = easyocr.Reader(['ch_sim', 'en'], gpu=False)
                        logger.info(f"EasyOCR model initialized successfully using CPU (fallback, Instance: {self.instance_id})")
                    except Exception as fallback_e:
                        logger.error(f"Failed to initialize EasyOCR with CPU fallback (Instance: {self.instance_id}): {fallback_e}")
                        logger.error(traceback.format_exc())
                        return False
                else:
                    return False
        
        return True

    def _recognize_text_from_image(self, image_data: bytes) -> str:
        """从图像数据中识别文本"""
        temp_file_path = None
        try:
            # 初始化EasyOCR模型（仅在首次调用时）
            initialization_success = self._initialize_easy_ocr()
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
            
            # 使用EasyOCR的readtext方法处理图像文件
            device_type = "GPU" if self.use_gpu else "CPU"
            logger.debug(f"Running OCR text recognition using {device_type} (Instance: {self.instance_id})...")
            result = self.easy_ocr.readtext(temp_file_path)
            
            if result:
                text_results = []
                for detection in result:
                    # EasyOCR返回格式: [bbox, text, confidence]
                    # 我们只需要文本部分（索引1）
                    if len(detection) >= 2:
                        text = detection[1]
                        if text.strip():  # 只添加非空文本
                            text_results.append(text.strip())
                
                if text_results:
                    extracted_text = '\n'.join(text_results)
                    logger.info(f"OCR completed successfully using {device_type} (Instance: {self.instance_id}), extracted {len(text_results)} text items")
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