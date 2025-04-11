import pybit7z
import logging
import tempfile
from typing import List, Dict
from .dt import Node, File, Data

class Analyzer:
    @staticmethod
    def analyze_compressed_file(node: Node):
        # data_stream = BytesIO()
        # if isinstance(node.content, File):
        #     data_stream = BytesIO(node.content.content)
        # elif isinstance(node.content, Data):
        #     logging.debug("analyze_compressed_file enter Data type")
        #     return
            
        # with pybit7z.lib7zip_context() as lib:
        #     arc = pybit7z.BitArchiveReader(lib, data_stream.getvalue(), pybit7z.FormatAuto)
        #     node.meta.map_number["items_count"] = arc.items_count()
        #     node.meta.map_number["folders_count"] = arc.folders_count()
        #     node.meta.map_number["files_count"] = arc.files_count()
        #     node.meta.map_number["size"] = arc.size()
        #     node.meta.map_number["pack_size"] = arc.pack_size()
        #     node.meta.map_bool["is_encrypted"] = arc.is_encrypted()
        #     node.meta.map_number["volumes_count"] = arc.volumes_count()
        #     node.meta.map_bool["is_multi_volume"] = arc.is_multi_volume()
    #         @typing.overload
    # def __init__(
    #     self,
    #     library: Bit7zLibrary,
    #     in_archive: bytes,
    #     format: BitInFormat = ...,
    #     password: str = "",
    # ) -> None: 不生效，只能生成临时文件来读取

        if isinstance(node.content, File):
            if not node.content.content:
                logging.error("Empty content")
                return
            node.meta.map_bool["is_encrypted"] = True
                
            try:
                with tempfile.NamedTemporaryFile(delete=True) as temp_file:
                    temp_file.write(node.content.content)
                    temp_file.flush()
                    
                    with pybit7z.lib7zip_context() as lib:
                        print(temp_file.name)
                        arc = pybit7z.BitArchiveReader(lib, temp_file.name, pybit7z.FormatAuto)
                        node.meta.map_number["items_count"] = arc.items_count()
                        node.meta.map_number["folders_count"] = arc.folders_count()
                        node.meta.map_number["files_count"] = arc.files_count() 
                        node.meta.map_number["size"] = arc.size()
                        node.meta.map_number["pack_size"] = arc.pack_size()
                        node.meta.map_bool["is_encrypted"] = arc.is_encrypted()
                        node.meta.map_number["volumes_count"] = arc.volumes_count()
                        node.meta.map_bool["is_multi_volume"] = arc.is_multi_volume()
                        
            except pybit7z.BitException as e:
                logging.error(f"Failed to analyze compressed file: {str(e)}")
                return
                
        elif isinstance(node.content, Data):
            logging.debug("analyze_compressed_file enter Data type")
            return
