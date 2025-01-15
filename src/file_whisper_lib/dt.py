from dataclasses import dataclass
from typing import Dict, List, Union
# import mimetypes
from .types import Types, Types__1, Extension_Types

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

    def set_type(self, key: str, ext: str = None):
        # 根据后缀归类
        if ext is not None:
            tmp = Extension_Types.get(ext, None)
            if tmp is not None:
                self.type = tmp
                return
        self.type = Types__1.get(key, Types.OTHER)
