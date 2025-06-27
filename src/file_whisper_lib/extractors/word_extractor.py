"""
Word文档处理模块
"""
import os
import uuid
import zipfile
import traceback
from typing import List
from loguru import logger
import docx
from spire.doc import *
from spire.doc.common import *

from ..dt import Node, File, Data
from ..types import Types
from .utils import encode_binary


class WordExtractor:
    
    @staticmethod
    def extract_word_file(node: Node) -> List[Node]:
        node.meta.map_bool["is_encrypted"] = False
        nodes = []
        file: File
        if isinstance(node.content, File):
            file = node.content
        elif isinstance(node.content, Data):
            logger.error("extract_word_file enter Data type")
            return nodes
        
        def analyze_docx_file(analyzed_path: str):
            ole_file_count = 0
            doc = docx.Document(analyzed_path)
            text_content = []
            
            # 限制处理的段落数量，根据页数估算
            # 假设每页约有20个段落
            max_paragraphs = node.word_max_pages * 20
            for i, para in enumerate(doc.paragraphs):
                if i >= max_paragraphs:
                    break
                text_content.append(para.text)

            separator = "\n"
            joined_text_content = separator.join(text_content)
            t_node = Node()
            t_node.id = 0
            t_node.content = Data(type="TEXT", content=encode_binary(joined_text_content))
            t_node.prev = node
            t_node.inherit_limits(node)
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
                        t_node.inherit_limits(node)
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
                                    t_node.inherit_limits(node)
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
            node.meta.map_bool["is_encrypted"] = True
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