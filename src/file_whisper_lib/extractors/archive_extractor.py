"""
压缩文件处理模块
"""
from typing import List, Dict
from loguru import logger
import pybit7z

from ..dt import Node, File, Data


class ArchiveExtractor:
    
    @staticmethod
    def extract_compressed_file(node: Node) -> List[Node]:
        nodes = []
        data = None
        
        try:
            if isinstance(node.content, File):
                data = node.content.content
            elif isinstance(node.content, Data):
                logger.debug("extract_compressed_file enter Data type")
                return nodes
            
            extracted = False
            files = {}
            
            if not node.passwords:
                try:
                    files = ArchiveExtractor.extract_files_from_data(data)
                    extracted = True
                except Exception as e:
                    raise e

            if not extracted and node.passwords:
                for password in node.passwords:
                    try:
                        files = ArchiveExtractor.extract_files_from_data(data, password)
                        extracted = True
                        node.meta.map_string["correct_password"] = password
                        break
                    except Exception as e:
                        if "Wrong password" in str(e):
                            logger.error(f"Password error: {e}")
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
                t_node.inherit_limits(node)
                nodes.append(t_node)

        except Exception as e:
            logger.error(f"Error extracting compressed file: {str(e)}")
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
            logger.error(f"Error in extract_files_from_data: {str(e)}")
            raise e
            
        return files_map