from dataclasses import dataclass
from typing import Dict, List, Optional, Union, TypeVar, Generic, Any
import uuid
from weakref import ref
# import mimetypes
import hashlib
import magic
from .types import Types, Types__1

@dataclass
class File:
    path: str = ""
    name: str = ""
    size: int = 0
    mime_type: str = ""
    extension: str = ""
    md5: str = ""
    sha256: str = ""
    sha1: str = ""
    content: bytes = b""

@dataclass
class Data:
    type: str = ""
    content: bytes = b""

@dataclass
class Meta:
    map_string: Dict[str, str] = None
    map_number: Dict[str, int] = None
    map_bool: Dict[str, bool] = None

    def __post_init__(self):
        if self.map_string is None:
            self.map_string = {}
        if self.map_number is None:
            self.map_number = {}
        if self.map_bool is None:
            self.map_bool = {}

class Node:
    def __init__(self):
        self.id: int = 0
        self.uuid: str = ""
        self.prev = None  # WeakRef to parent Node
        self.children: List['Node'] = []
        self.content: Union[File, Data] = None
        self.passwords: List[str] = []
        self.type: Types = Types.OTHER
        self.meta: Meta = Meta()

    def add_child(self, child: 'Node'):
        self.children.append(child)

    def set_type(self, key: str):
        self.type = Types__1.get(key, Types.OTHER)

class Tree:
    def __init__(self):
        self.root: Optional[Node] = None

    def meta_detect_encoding(self, meta: Meta, data: bytes):
        # Simplified encoding detection - you might want to use chardet or similar
        try:
            encodings = ['utf-8', 'ascii', 'iso-8859-1']
            for idx, encoding in enumerate(encodings):
                try:
                    data.decode(encoding)
                    if idx == 0:
                        meta.map_string["encoding"] = encoding
                        meta.map_number["encoding_confidence"] = 100
                    else:
                        meta.map_string[f"encoding{idx+1}"] = encoding
                        meta.map_number[f"encoding_confidence{idx+1}"] = 90
                except:
                    continue
        except:
            pass

    def digest(self, node: Node):
        extracted_nodes = []
        
        if self.root is None:
            self.root = node

        node.uuid = str(uuid.uuid4())
        
        if node.id == 0:
            # Use a snowflake-like ID generator or similar
            node.id = int(uuid.uuid4().int & (1<<63)-1)

        meta = Meta()

        if isinstance(node.content, File):
            file = node.content
            file.size = len(file.content)
            # file.mime_type = mimetypes.guess_type(file.name)[0] or ""
            file.mime_type = get_mime_type(file.content)
            # Implement these hash functions as needed
            file.md5 = calculate_md5(file.content)
            file.sha256 = calculate_sha256(file.content)
            file.sha1 = calculate_sha1(file.content)
            node.set_type(file.mime_type)
            self.meta_detect_encoding(meta, file.content)
        
        elif isinstance(node.content, Data):
            data = node.content
            self.meta_detect_encoding(meta, data.content)
            node.set_type(data.type)

        node.meta = meta

        # Implement these functions as needed
        # flavors.analyze(node)
        # nodes = flavors.extract(node)
        # extracted_nodes.extend(nodes)

        node.children = extracted_nodes

        for child_node in extracted_nodes:
            self.digest(child_node)

# Helper functions to be implemented
def calculate_md5(data: bytes) -> str:
    return hashlib.md5(data).hexdigest()

def calculate_sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def calculate_sha1(data: bytes) -> str:
    return hashlib.sha1(data).hexdigest()

def get_mime_type(data: bytes):
    # text/x-makefile
    return magic.from_buffer(data, mime=True)

def get_mime_type_desc(data: bytes):
    # makefile script, ASCII text
    return magic.from_buffer(data)
