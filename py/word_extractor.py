from spire.doc import *
from spire.doc.common import *
import uuid
import os

def process(path: str) -> str:
    output_dir = os.getenv('FILE_WHISPERER_OUTPUT_DIR')
    full_path = os.path.join(output_dir, path)
    document = Document()
    document.LoadFromFile(full_path)
    new_full_path = os.path.join(output_dir, uuid.uuid4().__str__())
    document.SaveToFile(new_full_path, FileFormat.Docx)
    return new_full_path
