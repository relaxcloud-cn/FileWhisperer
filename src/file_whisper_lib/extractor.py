from io import BytesIO
import re
import cv2
import numpy as np
from typing import List, Dict, Optional, Union, Tuple
import logging
from PIL import Image
import pytesseract
import zxingcpp
import pybit7z
from bs4 import BeautifulSoup
from .dt import Node, File, Data

# Helper functions
def encode_binary(text: str) -> bytes:
    return text.encode('utf-8')

def decode_binary(data: bytes) -> str:
    return data.decode('utf-8')

class Extractor:
    @staticmethod
    def extract_urls(node: Node) -> List[Node]:
        nodes = []
        text = ""
        
        try:
            if isinstance(node.content, File):
                logging.debug(f"Node[{node.id}] file {node.content.mime_type}")
                text = decode_binary(node.content.content)
            elif isinstance(node.content, Data):
                logging.debug(f"Node[{node.id}] data {node.content.type}")
                text = decode_binary(node.content.content)
            
            urls = Extractor.extract_urls_from_text(text)
            logging.debug(f"Node[{node.id}] Number of urls: {len(urls)}")
            
            for url in urls:
                t_node = Node()
                t_node.id = 0
                t_node.content = Data(type="URL", content=encode_binary(url))
                t_node.prev = node
                nodes.append(t_node)
                
        except Exception as e:
            logging.error(f"Error extracting URLs: {str(e)}")
            
        return nodes

    @staticmethod
    def extract_urls_from_text(text: str) -> List[str]:
        url_pattern = r"(https?://[^\s\"<>{}]+)"
        return re.findall(url_pattern, text)

    @staticmethod
    def extract_qrcode(node: Node) -> List[Node]:
        nodes = []
        
        try:
            if isinstance(node.content, File):
                data = node.content.content
                bytes_io = BytesIO(data)
                file_bytes = np.asarray(bytearray(bytes_io.read()), dtype=np.uint8)
                img = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)
                # img = cv2.imread('test.png')
                barcodes = zxingcpp.read_barcodes(img)
                for barcode in barcodes:
                    # print('Found barcode:'
                    #     f'\n Text:    "{barcode.text}"'
                    #     f'\n Format:   {barcode.format}'
                    #     f'\n Content:  {barcode.content_type}'
                    #     f'\n Position: {barcode.position}')
                
                # reader = zxingcpp.BarCodeReader()
                # image = Image.open(BytesIO(data))
                # result = reader.decode(image)
                
                # if result and result.raw:
                    t_node = Node()
                    t_node.id = 0
                    t_node.content = Data(type="QRCODE", content=encode_binary(barcode.text))
                    t_node.prev = node
                    nodes.append(t_node)
                    
            elif isinstance(node.content, Data):
                logging.debug("extract_qrcode enter Data type")
                
        except Exception as e:
            logging.error(f"Error extracting QR code: {str(e)}")
            
        return nodes

    @staticmethod
    def extract_ocr(node: Node) -> List[Node]:
        nodes = []
        
        try:
            if isinstance(node.content, File):
                data = node.content.content
                
                image = Image.open(BytesIO(data))
                
                result = pytesseract.image_to_string(image, lang='chi_tra+eng')
                
                if result:
                    t_node = Node()
                    t_node.id = 0
                    t_node.content = Data(type="OCR", content=encode_binary(result))
                    t_node.prev = node
                    nodes.append(t_node)
                    
            elif isinstance(node.content, Data):
                logging.debug("extract_ocr enter Data type")
                
        except Exception as e:
            logging.error(f"OCR processing failed: {str(e)}")
            
        return nodes

    @staticmethod
    def extract_html(node: Node) -> List[Node]:
        nodes = []
        text = ""
        
        try:
            if isinstance(node.content, File):
                logging.debug(f"Node[{node.id}] file {node.content.mime_type}")
                text = decode_binary(node.content.content)
            elif isinstance(node.content, Data):
                logging.debug(f"Node[{node.id}] data {node.content.type}")
                text = decode_binary(node.content.content)
            
            soup = BeautifulSoup(text, 'html.parser')
            html_text = soup.get_text(separator=' ', strip=True)
            
            t_node = Node()
            t_node.id = 0
            t_node.content = Data(type="TEXT", content=encode_binary(html_text))
            t_node.prev = node
            nodes.append(t_node)
            
        except Exception as e:
            logging.error(f"Error extracting HTML: {str(e)}")
            
        return nodes

    @staticmethod
    def extract_compressed_file(node: Node) -> List[Node]:
        nodes = []
        data = None
        
        try:
            if isinstance(node.content, File):
                data = node.content.content
            elif isinstance(node.content, Data):
                logging.debug("extract_compressed_file enter Data type")
                return nodes
            
            extracted = False
            files = {}
            
            if not node.passwords:
                try:
                    files = Extractor.extract_files_from_data(data)
                    extracted = True
                except Exception as e:
                    # if "password is required" not in str(e).lower():
                    # 需要密码的报错
                    # Failed to extract the archive: A password is required but none was provided.
                    raise e

            if not extracted and node.passwords:
                for password in node.passwords:
                    try:
                        files = Extractor.extract_files_from_data(data, password)
                        extracted = True
                        node.meta.map_string["correct_password"] = password
                        break
                    except Exception as e:
                        if "Wrong password" in str(e):
                            logging.error(f"Password error: {e}")
                            continue
                        raise e

            if not extracted:
                raise RuntimeError("Failed to extract compressed file")

            for filename, content in files.items():
                t_node = Node()
                t_node.content = File(
                    path=filename,
                    name=filename,
                    content=content
                )
                t_node.prev = node
                nodes.append(t_node)

        except Exception as e:
            logging.error(f"Error extracting compressed file: {str(e)}")
            raise e

        return nodes

    @staticmethod
    def extract_files_from_data(data: bytes, password: str = "") -> Dict[str, bytes]:
        files_map = {}
        
        try:
            with pybit7z.lib7zip_context() as lib:
                extractor = pybit7z.BitMemExtractor(lib, pybit7z.FormatAuto)
                if password:
                    extractor.set_password(password)
                files_map = extractor.extract(data)
                                
        except Exception as e:
            logging.error(f"Error in extract_files_from_data: {str(e)}")
            raise e
            
        return files_map