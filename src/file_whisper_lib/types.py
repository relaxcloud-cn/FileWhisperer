from enum import Enum

class Types(Enum):
    TEXT_PLAIN = 0
    COMPRESSED_FILE = 1
    IMAGE = 2
    TEXT_HTML = 3
    OTHER = 4

Types__1 = {
    # DATA
    "TEXT": Types.TEXT_PLAIN,
    "OCR": Types.TEXT_PLAIN,
    "QRCODE": Types.TEXT_PLAIN,

    # FILE
    "text/plain": Types.TEXT_PLAIN,
    "text/html": Types.TEXT_HTML,
    "application/zip": Types.COMPRESSED_FILE,
    "application/x-rar-compressed": Types.COMPRESSED_FILE,
    "application/vnd.rar": Types.COMPRESSED_FILE,
    "application/x-7z-compressed": Types.COMPRESSED_FILE,
    "application/x-tar": Types.COMPRESSED_FILE,
    "application/gzip": Types.COMPRESSED_FILE,
    "application/x-gzip": Types.COMPRESSED_FILE,
    "application/x-bzip2": Types.COMPRESSED_FILE,
    "application/x-xz": Types.COMPRESSED_FILE,
    # ... (all image mime types remain the same)
}