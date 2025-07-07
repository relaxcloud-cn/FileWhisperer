"""
通用辅助功能模块
"""

def encode_binary(text: str) -> bytes:
    """将字符串编码为字节"""
    return text.encode('utf-8')

def decode_binary(data: bytes) -> str:
    """将字节解码为字符串"""
    return data.decode('utf-8')