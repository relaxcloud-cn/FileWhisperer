"""
二维码/条形码处理模块
"""
from io import BytesIO
import cv2
import numpy as np
from typing import List
from loguru import logger
import zxingcpp

from ..dt import Node, File, Data
from .utils import encode_binary


class QRCodeExtractor:
    
    @staticmethod
    def extract_qrcode(node: Node) -> List[Node]:
        nodes = []
        
        try:
            if isinstance(node.content, File):
                data = node.content.content
                bytes_io = BytesIO(data)
                file_bytes = np.asarray(bytearray(bytes_io.read()), dtype=np.uint8)
                img = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)
                barcodes = zxingcpp.read_barcodes(img)
                for barcode in barcodes:
                    t_node = Node()
                    t_node.id = 0
                    t_node.content = Data(type="QRCODE", content=encode_binary(barcode.text))
                    t_node.prev = node
                    t_node.inherit_limits(node)
                    nodes.append(t_node)
                    
            elif isinstance(node.content, Data):
                logger.debug("extract_qrcode enter Data type")
                
        except Exception as e:
            logger.error(f"Error extracting QR code: {str(e)}")
            
        return nodes