from io import BytesIO
import re
import cv2
import numpy as np
from typing import List, Dict
import logging
from PIL import Image
import pytesseract
import zxingcpp
import pybit7z
import uuid
import docx
import fitz
import traceback
import zipfile
from bs4 import BeautifulSoup
from spire.doc import *
from spire.doc.common import *
from .dt import Node, File, Data
from .types import Types

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

    @staticmethod
    def extract_word_file(node: Node) -> List[Node]:
        nodes = []
        file: File
        if isinstance(node.content, File):
            file = node.content
        elif isinstance(node.content, Data):
            logging.error("extract_word_file enter Data type")
            return nodes
        
        def analyze_docx_file(analyzed_path:str):
            ole_file_count = 0
            doc = docx.Document(analyzed_path)
            text_content = []
            
            for para in doc.paragraphs:
                text_content.append(para.text)

            separator = "\n"
            joined_text_content = separator.join(text_content)
            # 暂时保留下面的话 👇
            # if '此文件仅WPS能打开' not in text_content:
            t_node = Node()
            t_node.id = 0
            t_node.content = Data(type="TEXT", content=encode_binary(joined_text_content))
            t_node.prev = node
            nodes.append(t_node)

            with zipfile.ZipFile(analyzed_path, 'r') as docx_zip:
                all_files = docx_zip.namelist()
                for file1 in all_files:
                    if file1.startswith('word/embeddings/') and not file1.__eq__('word/embeddings/'):
                        ole_file_count += 1
                    elif file1.startswith('word/media/') and not file1.__eq__('word/media/'):
                        t_node = Node()
                        file_name = os.path.basename(file1)
                        file_byte = docx_zip.read(file1)
                        t_node.content = File(
                            path=file_name,
                            name=file_name,
                            content=file_byte
                        )
                        t_node.prev = node
                        nodes.append(t_node)

            if ole_file_count:
                doc = Document()
                doc.LoadFromFile(analyzed_path)

                i = 1 
                for k in range(doc.Sections.Count):
                    sec = doc.Sections.get_Item(k)
                    # Iterate through all child objects in the body of each section
                    for j in range(sec.Body.ChildObjects.Count):
                        obj = sec.Body.ChildObjects.get_Item(j)
                        # Check if the child object is a paragraph
                        if isinstance(obj, Paragraph):
                            par = obj if isinstance(obj, Paragraph) else None
                            # Iterate through the child objects in the paragraph
                            for m in range(par.ChildObjects.Count):
                                o = par.ChildObjects.get_Item(m)
                                # Check if the child object is an OLE object
                                if o.DocumentObjectType == DocumentObjectType.OleObject:
                                    ole = o if isinstance(o, DocOleObject) else None
                                    s = ole.ObjectType
                                    scanners = []
                                    # Check if the OLE object is a PDF file
                                    if s.startswith("AcroExch.Document"):
                                        ext = ".pdf"
                                        scanners.append("ScanPdf")
                                    # Check if the OLE object is an Excel spreadsheet
                                    elif s.startswith("Excel.Sheet"):
                                        ext = ".xlsx"
                                    # Check if the OLE object is a PowerPoint presentation
                                    elif s.startswith("PowerPoint.Show"):
                                        ext = ".pptx"
                                    elif s.startswith("Package"):
                                        ext = ""
                                        scanners.append("ScanCompressed")
                                    elif s.startswith("Word.Document.12"):
                                        ext = ".docx"
                                        scanners.append("ScanDocx")
                                    elif s.startswith("Word.Document.8"):
                                        ext = ".doc"
                                        scanners.append("ScanDoc")
                                    else:
                                        continue
                                    t_node = Node()
                                    t_node.content = File(
                                        path=f"Output/OLE{i}{ext}",
                                        name=f"Output/OLE{i}{ext}",
                                        content=ole.NativeData
                                    )
                                    t_node.prev = node
                                    nodes.append(t_node)                
                                    i += 1

                doc.Close()
        
        tmp_files = []

        current_file_path = ''
        file_path = '/tmp/' + uuid.uuid4().__str__()
        with open(file_path, 'wb') as f:
            f.write(file.content)
        tmp_files.append(file_path)
        current_file_path = file_path
        if node.type == Types.DOC:
            docx_path = file_path + 'x'
            document = Document()
            document.LoadFromFile(file_path)
            document.SaveToFile(docx_path, FileFormat.Docx)
            tmp_files.append(docx_path)
            current_file_path = docx_path

        try:
            analyze_docx_file(current_file_path)
        except zipfile.BadZipFile:
            stop = False
            for pwd in node.passwords:
                if stop: break
                try:
                    document = Document()
                    document.LoadFromFile(current_file_path, FileFormat.Docx, pwd)
                    document.RemoveEncryption()
                    document.SaveToFile(current_file_path)
                    stop = True
                except Exception as e:
                    pass
            if stop:
                analyze_docx_file(current_file_path)
        except Exception as e:
            traceback.print_exc()
        finally:
            for i in tmp_files:
                if os.path.exists(i):
                    os.remove(i)
        
        return nodes



            # for rel in doc.part.rels.values():
            #     if "image" in rel.reltype:
            #         image_path = rel.target_part.partname
            #         images.append(image_path)

            # print(text_content)
            # print(images)
            # if '此文件仅WPS能打开' not in text_content:
            #     file_name = ''
            #     if isinstance(file.original_filename, bytes):
            #         file_name = file.original_filename.decode()
            #     else:
            #         file_name = file.original_filename

            #     self.texts.append({file_name: ''.join(text_content)})
            #     extractor = URIExtractor()
            #     separator = "\n"
            #     joined_text_content = separator.join(text_content)

            #     uris:list = extractor.extracturis(' '.join(text_content))
            #     uris += extract_urls(' '.join(text_content))
            #     if set(uris):
            #         for i in uris:
            #             tmp_dict = {}
            #             tmp_dict["fileid"] = file.uid
            #             tmp_dict["string"] = i
            #             tmp_dict["flavors"] = copy.deepcopy(file.file_types)
            #             tmp_dict["from"] = "WORD-TEXT"

            #             self.urls.append(tmp_dict)
        
    @staticmethod
    def extract_pdf_file(node: Node) -> List[Node]:
        nodes = []
        file: File
        if isinstance(node.content, File):
            file = node.content
        elif isinstance(node.content, Data):
            logging.error("extract_pdf_file enter Data type")
            return nodes
        
        all_text = ""
        pdf = fitz.open(stream=BytesIO(file.content), filetype="pdf")
        if pdf.needs_pass:
            password_success = False
            for password in node.passwords:
                if pdf.authenticate(password):
                    password_success = True
                    node.meta.map_string["correct_password"] = password
                    break
    
            if not password_success:
                raise ValueError("PDF all passwords are invalid.")
            
        max_pages = min(10, len(pdf))
        for page_number in range(max_pages):
            page = pdf.load_page(page_number)
            images = page.get_images(full=True)
            text = page.get_text()
            all_text += text
            print(images)

            for img_index, img in enumerate(images):
                xref = img[0]
                base_image = pdf.extract_image(xref)
                image_bytes = base_image["image"]
                # image = Image.open(io.BytesIO(image_bytes))
                image_filename = f"page_{page_number + 1}_image_{img_index + 1}.png"
                t_node = Node()
                t_node.content = File(
                    path=image_filename,
                    name=image_filename,
                    content=image_bytes
                )
                t_node.prev = node
                nodes.append(t_node)

        t_node = Node()
        t_node.id = 0
        t_node.content = Data(type="TEXT", content=encode_binary(all_text))
        t_node.prev = node
        nodes.append(t_node)

        return nodes
