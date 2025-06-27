"""
PDF文档处理模块
"""
from io import BytesIO
from typing import List
from loguru import logger
import fitz

from ..dt import Node, File, Data
from .utils import encode_binary


class PDFExtractor:
    
    @staticmethod
    def extract_pdf_file(node: Node) -> List[Node]:
        nodes = []
        file: File
        if isinstance(node.content, File):
            file = node.content
        elif isinstance(node.content, Data):
            logger.error("extract_pdf_file enter Data type")
            return nodes
        
        all_text = ""
        pdf = fitz.open(stream=BytesIO(file.content), filetype="pdf")
        if pdf.needs_pass:
            node.meta.map_bool["is_encrypted"] = True
            password_success = False
            for password in node.passwords:
                if pdf.authenticate(password):
                    password_success = True
                    node.meta.map_string["correct_password"] = password
                    break
    
            if not password_success:
                raise ValueError("PDF all passwords are invalid.")
        else:
            node.meta.map_bool["is_encrypted"] = False
            
        # 使用node.pdf_max_pages来限制处理的页数
        max_pages = min(node.pdf_max_pages, len(pdf))
        for page_number in range(max_pages):
            page = pdf.load_page(page_number)
            images = page.get_images(full=True)
            text = page.get_text()
            all_text += text

            for img_index, img in enumerate(images):
                xref = img[0]
                base_image = pdf.extract_image(xref)
                image_bytes = base_image["image"]
                image_filename = f"page_{page_number + 1}_image_{img_index + 1}.png"
                t_node = Node()
                t_node.content = File(
                    path=image_filename,
                    name=image_filename,
                    content=image_bytes
                )
                t_node.prev = node
                t_node.inherit_limits(node)
                nodes.append(t_node)

        t_node = Node()
        t_node.id = 0
        t_node.content = Data(type="TEXT", content=encode_binary(all_text))
        t_node.prev = node
        t_node.inherit_limits(node)
        nodes.append(t_node)

        return nodes