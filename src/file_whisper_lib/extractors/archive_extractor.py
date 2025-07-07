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
        """主要的压缩文件解压入口函数"""
        try:
            # 从Node中提取数据
            data = ArchiveExtractor._extract_data_from_node(node)
            if data is None:
                return []
            
            # 尝试解压缩文件
            files = ArchiveExtractor._try_extract_with_passwords(data, node)
            
            # 根据解压结果创建Node对象
            nodes = ArchiveExtractor._create_nodes_from_files(files, node)
            
            return nodes
            
        except Exception as e:
            logger.error(f"Error extracting compressed file: {str(e)}")
            raise e
    
    @staticmethod
    def _extract_data_from_node(node: Node) -> bytes:
        """从Node中提取二进制数据"""
        if isinstance(node.content, File):
            return node.content.content
        elif isinstance(node.content, Data):
            logger.debug("extract_compressed_file enter Data type")
            return None
        else:
            raise ValueError("Unsupported node content type")
    
    @staticmethod
    def _try_extract_with_passwords(data: bytes, node: Node) -> Dict[str, bytes]:
        """尝试使用密码解压缩文件"""
        extracted = False
        files = {}
        
        # 首先尝试无密码解压
        if not node.passwords:
            try:
                files = ArchiveExtractor.extract_files_from_data(data)
                extracted = True
            except Exception as e:
                raise e
        
        # 如果无密码解压失败或存在密码列表，尝试使用密码
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
        
        return files
    
    @staticmethod
    def _create_nodes_from_files(files: Dict[str, bytes], parent_node: Node) -> List[Node]:
        """根据解压后的文件创建Node对象列表"""
        nodes = []
        
        for filename, content in files.items():
            t_node = Node()
            t_node.content = File(
                path=filename,
                name=filename,
                content=content
            )
            t_node.prev = parent_node
            t_node.inherit_limits(parent_node)
            nodes.append(t_node)
        
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