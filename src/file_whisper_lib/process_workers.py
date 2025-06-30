"""
进程池工作器 - 重用现有extractor代码
"""
import os
import tempfile
from typing import Dict, Any, Tuple, List
from loguru import logger

# 全局工作器计数器
_worker_counters = {}

# OCR模型实例（进程级别）
_ocr_model = None

def initialize_ocr_worker():
    """OCR工作进程初始化函数 - 预加载模型"""
    global _ocr_model
    worker_id = _get_worker_id("ocr_init")
    
    try:
        logger.info(f"[{worker_id}] Process {os.getpid()}: Initializing OCR model...")
        
        # 设置环境变量
        os.environ["TOKENIZERS_PARALLELISM"] = "false"
        
        # 初始化PaddleOCR模型
        from paddleocr import PaddleOCR
        import logging
        
        # 设置日志级别
        logging.getLogger("transformers").setLevel(logging.ERROR)
        logging.getLogger("transformers.modeling_utils").setLevel(logging.ERROR)
        logging.getLogger("transformers.configuration_utils").setLevel(logging.ERROR)
        logging.getLogger("PIL.TiffImagePlugin").setLevel(logging.ERROR)
        
        _ocr_model = PaddleOCR(
            use_doc_orientation_classify=False,
            use_doc_unwarping=False,
            use_textline_orientation=False
        )
        
        logger.info(f"[{worker_id}] Process {os.getpid()}: OCR model initialized successfully")
        return True
        
    except Exception as e:
        logger.error(f"[{worker_id}] Process {os.getpid()}: Failed to initialize OCR model: {e}")
        return False

def _get_worker_id(worker_type: str) -> str:
    """获取工作器ID"""
    global _worker_counters
    pid = os.getpid()
    
    if worker_type not in _worker_counters:
        _worker_counters[worker_type] = 0
    _worker_counters[worker_type] += 1
    
    return f"{worker_type.upper()}-{_worker_counters[worker_type]}"


def process_ocr_task(image_data: bytes) -> str:
    """OCR进程任务入口 - 使用预加载的模型"""
    global _ocr_model
    worker_id = _get_worker_id("ocr")
    temp_file_path = None
    
    try:
        logger.info(f"[{worker_id}] Process {os.getpid()}: Starting OCR processing")
        
        # 确保模型已初始化
        if _ocr_model is None:
            logger.warning(f"[{worker_id}] Process {os.getpid()}: OCR model not initialized, initializing now...")
            if not initialize_ocr_worker():
                logger.error(f"[{worker_id}] Process {os.getpid()}: Failed to initialize OCR model")
                return ""
        
        # 生成临时文件路径
        import uuid
        temp_file_name = f"ocr_temp_{uuid.uuid4().hex}.png"
        temp_file_path = os.path.join(tempfile.gettempdir(), temp_file_name)
        
        # 保存图像数据到临时文件
        with open(temp_file_path, 'wb') as f:
            f.write(image_data)
        
        logger.debug(f"[{worker_id}] Temporary image saved to: {temp_file_path}")
        
        # 使用预加载的模型进行OCR处理
        result = _ocr_model.predict(input=temp_file_path)
        
        extracted_text = ""
        if result:
            text_results = []
            for res in result:
                # OCRResult对象可以像字典一样访问
                if 'rec_texts' in res:
                    ocr_texts = res['rec_texts']
                    text_results.extend(ocr_texts)
            
            if text_results:
                extracted_text = '\n'.join(text_results)
                logger.info(f"[{worker_id}] Process {os.getpid()}: OCR completed successfully, extracted {len(text_results)} text items")
        
        return extracted_text
        
    except Exception as e:
        logger.error(f"[{worker_id}] Process {os.getpid()}: OCR processing failed: {e}")
        return ""
    finally:
        # 清理临时文件
        try:
            if temp_file_path and os.path.exists(temp_file_path):
                os.remove(temp_file_path)
                logger.debug(f"[{worker_id}] Temporary file cleaned up: {temp_file_path}")
        except Exception as e:
            logger.warning(f"[{worker_id}] Process {os.getpid()}: Failed to cleanup temp file: {e}")


def process_word_task(file_data: bytes, max_pages: int = 10) -> Tuple[str, Dict[str, Any]]:
    """Word处理进程任务入口 - 重用现有WordExtractor代码"""
    worker_id = _get_worker_id("word")
    
    try:
        logger.info(f"[{worker_id}] Process {os.getpid()}: Starting Word processing")
        
        # 创建模拟的Node
        from file_whisper_lib.dt import Node, File
        node = Node()
        node.content = File(
            path="temp_word.docx",
            name="temp_word.docx", 
            content=file_data
        )
        node.word_max_pages = max_pages
        
        # 使用现有的WordExtractor
        from file_whisper_lib.extractors.word_extractor import WordExtractor
        result_nodes = WordExtractor.extract_word_file(node)
        
        # 提取文本内容
        content = ""
        metadata = {}
        
        for result_node in result_nodes:
            if hasattr(result_node.content, 'content'):
                try:
                    # 解码文本内容
                    from file_whisper_lib.extractors.utils import decode_binary
                    text_content = decode_binary(result_node.content.content)
                    content += text_content + "\n"
                except:
                    pass
        
        # 添加元数据
        metadata['processed_by'] = worker_id
        metadata['max_pages'] = max_pages
        
        logger.info(f"[{worker_id}] Process {os.getpid()}: Word processing completed")
        return content.strip(), metadata
        
    except Exception as e:
        logger.error(f"[{worker_id}] Process {os.getpid()}: Word processing failed: {e}")
        return "", {}


def process_pdf_task(file_data: bytes, max_pages: int = 10) -> Tuple[str, Dict[str, Any]]:
    """PDF处理进程任务入口 - 重用现有PDFExtractor代码"""
    worker_id = _get_worker_id("pdf") 
    
    try:
        logger.info(f"[{worker_id}] Process {os.getpid()}: Starting PDF processing")
        
        # 创建模拟的Node
        from file_whisper_lib.dt import Node, File
        node = Node()
        node.content = File(
            path="temp_pdf.pdf",
            name="temp_pdf.pdf",
            content=file_data
        )
        node.pdf_max_pages = max_pages
        node.passwords = []  # 空密码列表
        
        # 使用现有的PDFExtractor
        from file_whisper_lib.extractors.pdf_extractor import PDFExtractor
        result_nodes = PDFExtractor.extract_pdf_file(node)
        
        # 提取文本内容
        content = ""
        metadata = {}
        
        for result_node in result_nodes:
            if hasattr(result_node.content, 'content') and result_node.content.type == "TEXT":
                try:
                    # 解码文本内容
                    from file_whisper_lib.extractors.utils import decode_binary
                    text_content = decode_binary(result_node.content.content)
                    content += text_content + "\n"
                except:
                    pass
        
        # 从节点元数据中提取信息
        if hasattr(node, 'meta'):
            for key, value in node.meta.map_string.items():
                metadata[key] = value
            for key, value in node.meta.map_number.items():
                metadata[key] = value
            for key, value in node.meta.map_bool.items():
                metadata[key] = value
        
        # 添加处理元数据
        metadata['processed_by'] = worker_id
        metadata['max_pages'] = max_pages
        
        logger.info(f"[{worker_id}] Process {os.getpid()}: PDF processing completed")
        return content.strip(), metadata
        
    except Exception as e:
        logger.error(f"[{worker_id}] Process {os.getpid()}: PDF processing failed: {e}")
        return "", {}


def process_html_task(file_data: bytes) -> Tuple[str, Dict[str, Any]]:
    """HTML处理进程任务入口 - 重用现有HTMLExtractor代码"""
    worker_id = _get_worker_id("html")
    
    try:
        logger.info(f"[{worker_id}] Process {os.getpid()}: Starting HTML processing")
        
        # 创建模拟的Node
        from file_whisper_lib.dt import Node, File
        node = Node()
        node.content = File(
            path="temp_html.html",
            name="temp_html.html",
            content=file_data
        )
        
        # 使用现有的HTMLExtractor
        from file_whisper_lib.extractors.html_extractor import HTMLExtractor
        from file_whisper_lib.extractors.utils import decode_binary
        
        # 解码HTML内容
        html_content = decode_binary(file_data)
        
        # 提取文本和URL
        text_content = HTMLExtractor.extract_text_from_html(html_content)
        urls = HTMLExtractor.extract_urls_from_html(html_content)
        
        # 构建元数据
        metadata = {
            'processed_by': worker_id,
            'urls_found': len(urls),
            'urls': urls[:10] if len(urls) > 10 else urls  # 限制URL数量
        }
        
        logger.info(f"[{worker_id}] Process {os.getpid()}: HTML processing completed")
        return text_content, metadata
        
    except Exception as e:
        logger.error(f"[{worker_id}] Process {os.getpid()}: HTML processing failed: {e}")
        return "", {}


def process_archive_task(file_data: bytes, passwords: List[str] = None) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """Archive处理进程任务入口 - 重用现有ArchiveExtractor代码"""
    worker_id = _get_worker_id("archive")
    
    try:
        logger.info(f"[{worker_id}] Process {os.getpid()}: Starting Archive processing")
        
        # 创建模拟的Node
        from file_whisper_lib.dt import Node, File
        node = Node()
        node.content = File(
            path="temp_archive.zip",
            name="temp_archive.zip",
            content=file_data
        )
        node.passwords = passwords or []
        
        # 使用现有的ArchiveExtractor
        from file_whisper_lib.extractors.archive_extractor import ArchiveExtractor
        result_nodes = ArchiveExtractor.extract_compressed_file(node)
        
        # 整理提取的文件信息
        extracted_files = {}
        metadata = {'processed_by': worker_id, 'files_count': len(result_nodes)}
        
        for result_node in result_nodes:
            if hasattr(result_node.content, 'name'):
                file_name = result_node.content.name
                if hasattr(result_node.content, 'content'):
                    extracted_files[file_name] = result_node.content.content
        
        metadata['file_names'] = list(extracted_files.keys())
        
        logger.info(f"[{worker_id}] Process {os.getpid()}: Archive processing completed")
        return extracted_files, metadata
        
    except Exception as e:
        logger.error(f"[{worker_id}] Process {os.getpid()}: Archive processing failed: {e}")
        return {}, {}


def process_qrcode_task(image_data: bytes) -> Tuple[List[str], Dict[str, Any]]:
    """QRCode处理进程任务入口 - 重用现有QRCodeExtractor代码"""
    worker_id = _get_worker_id("qrcode")
    
    try:
        logger.info(f"[{worker_id}] Process {os.getpid()}: Starting QRCode processing")
        
        # 创建模拟的Node
        from file_whisper_lib.dt import Node, File
        node = Node()
        node.content = File(
            path="temp_image.png",
            name="temp_image.png",
            content=image_data
        )
        
        # 使用现有的QRCodeExtractor
        from file_whisper_lib.extractors.qrcode_extractor import QRCodeExtractor
        result_nodes = QRCodeExtractor.extract_qrcode(node)
        
        # 提取QR码内容
        qr_contents = []
        for result_node in result_nodes:
            if hasattr(result_node.content, 'content'):
                try:
                    from file_whisper_lib.extractors.utils import decode_binary
                    content = decode_binary(result_node.content.content)
                    qr_contents.append(content)
                except:
                    pass
        
        metadata = {
            'processed_by': worker_id,
            'qrcodes_found': len(qr_contents)
        }
        
        logger.info(f"[{worker_id}] Process {os.getpid()}: QRCode processing completed")
        return qr_contents, metadata
        
    except Exception as e:
        logger.error(f"[{worker_id}] Process {os.getpid()}: QRCode processing failed: {e}")
        return [], {}


def process_email_task(file_data: bytes) -> Tuple[str, Dict[str, Any]]:
    """Email处理进程任务入口 - 重用现有EmailExtractor代码"""
    worker_id = _get_worker_id("email")
    
    try:
        logger.info(f"[{worker_id}] Process {os.getpid()}: Starting Email processing")
        
        # 创建模拟的Node
        from file_whisper_lib.dt import Node, File
        node = Node()
        node.content = File(
            path="temp_email.eml",
            name="temp_email.eml",
            content=file_data
        )
        
        # 使用现有的EmailExtractor
        from file_whisper_lib.extractors.email_extractor import EmailExtractor
        result_nodes = EmailExtractor.extract_email_file(node)
        
        # 提取邮件内容
        content = ""
        metadata = {}
        
        for result_node in result_nodes:
            if hasattr(result_node.content, 'content'):
                try:
                    from file_whisper_lib.extractors.utils import decode_binary
                    text_content = decode_binary(result_node.content.content)
                    content += text_content + "\n"
                except:
                    pass
        
        # 添加处理元数据
        metadata['processed_by'] = worker_id
        metadata['email_parts'] = len(result_nodes)
        
        logger.info(f"[{worker_id}] Process {os.getpid()}: Email processing completed")
        return content.strip(), metadata
        
    except Exception as e:
        logger.error(f"[{worker_id}] Process {os.getpid()}: Email processing failed: {e}")
        return "", {}


def process_url_task(url: str) -> Tuple[str, Dict[str, Any]]:
    """URL处理进程任务入口 - 重用现有URLExtractor代码"""
    worker_id = _get_worker_id("url")
    
    try:
        logger.info(f"[{worker_id}] Process {os.getpid()}: Starting URL processing")
        
        # 创建模拟的Node
        from file_whisper_lib.dt import Node, Data
        node = Node()
        node.content = Data(
            type="URL",
            content=url.encode('utf-8')
        )
        
        # 使用现有的URLExtractor
        from file_whisper_lib.extractors.url_extractor import URLExtractor
        result_nodes = URLExtractor.extract_url_content(node)
        
        # 提取URL内容
        content = ""
        metadata = {}
        
        for result_node in result_nodes:
            if hasattr(result_node.content, 'content'):
                try:
                    from file_whisper_lib.extractors.utils import decode_binary
                    text_content = decode_binary(result_node.content.content)
                    content += text_content + "\n"
                except:
                    pass
        
        # 添加处理元数据
        metadata['processed_by'] = worker_id
        metadata['source_url'] = url
        
        logger.info(f"[{worker_id}] Process {os.getpid()}: URL processing completed")
        return content.strip(), metadata
        
    except Exception as e:
        logger.error(f"[{worker_id}] Process {os.getpid()}: URL processing failed: {e}")
        return "", {}