import signal
import argparse
import grpc
from concurrent import futures
import os
import mmap
from typing import List, Optional
import logging
from pathlib import Path
import shutil

# os.environ['PADDLEOCR_LOG_LEVEL'] = '3'
# logging.getLogger("paddle").setLevel(logging.ERROR)
# logging.getLogger("paddleocr").setLevel(logging.ERROR)

# Assuming these are generated from your protobuf definitions
from file_whisper_pb2 import WhisperRequest, WhisperReply, Node, File, Data, Meta
from file_whisper_pb2_grpc import WhisperServicer, add_WhisperServicer_to_server
from file_whisper_lib.dt import Node as DataNode, File as DataFile, Data as DataData
from file_whisper_lib.tree import Tree

server = None

class GreeterServiceImpl(WhisperServicer):
    def Whispering(self, request: WhisperRequest, context) -> WhisperReply:
        try:
            tree = Tree()
            node = DataNode()
            node.content = DataFile()

            if request.HasField('root_id'):
                node.id = request.root_id
            else:
                node.id = 0

            passwords = list(request.passwords)
            node.passwords = passwords
            
            # 提取PDF最大页数参数
            if request.HasField('pdf_max_pages'):
                node.pdf_max_pages = request.pdf_max_pages
            else:
                node.pdf_max_pages = 10  # 默认值为10页
                
            # 提取Word最大页数参数
            if request.HasField('word_max_pages'):
                node.word_max_pages = request.word_max_pages
            else:
                node.word_max_pages = 10  # 默认值为10页

            if request.HasField('file_path'):
                file_path = request.file_path
                with open(file_path, 'rb') as f:
                    mm = mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ)
                    file_content = mm.read()
                    mm.close()
            elif request.HasField('file_content'):
                file_content = request.file_content
                file_path = "memory_file"
            else:
                error_msg = "No file data provided"
                logging.error(error_msg)
                context.set_code(grpc.StatusCode.INVALID_ARGUMENT)
                context.set_details(error_msg)
                return WhisperReply()

            file = node.content
            file.path = file_path
            file.name = os.path.basename(file_path)
            file.content = file_content
            tree.digest(node)
            reply = WhisperReply()
            make_whisper_reply(reply, tree)
            return reply

        except Exception as e:
            error_msg = f"Error processing request: {str(e)}"
            logging.error(error_msg)
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(error_msg)
            return WhisperReply()

def make_whisper_reply(reply: WhisperReply, tree: Tree):
    bfs(reply, tree.root)

def bfs(reply: WhisperReply, root: Optional[DataNode]):
    if not root:
        return

    from collections import deque
    queue = deque([root])

    while queue:
        curr = queue.popleft()
        bfs_process_whisper_reply_node(reply, curr)

        for child in curr.children:
            queue.append(child)

def bfs_process_whisper_reply_node(reply: WhisperReply, root: DataNode):
    node = reply.tree.add()
    node.id = root.id
    
    if hasattr(root, 'prev') and root.prev is not None:
        node.parent_id = root.prev.id

    if root.children:
        node.children.extend([child.id for child in root.children])

    if isinstance(root.content, DataFile):
        root_file = root.content
        file = node.file
        file_path = root.uuid
        file.path = file_path
        file.name = root_file.name
        file.extension = root_file.extension
        file.size = root_file.size
        file.mime_type = root_file.mime_type
        file.md5 = root_file.md5
        file.sha256 = root_file.sha256
        file.sha1 = root_file.sha1
        write_content_to_file(file_path, root_file.content)

    elif isinstance(root.content, DataData):
        root_data = root.content
        data = node.data
        data.type = root_data.type
        data.content = root_data.content

    node_meta = node.meta
    
    for key, value in root.meta.map_string.items():
        node_meta.map_string[key] = value
    
    for key, value in root.meta.map_number.items():
        node_meta.map_number[key] = value

    for key, value in root.meta.map_bool.items():
        node_meta.map_bool[key] = value

def signal_handler(signum, frame):
    if server:
        logging.info(f"Received signal {signum}. Shutting down...")
        server.stop(0)

def write_content_to_file(file_path: str, content: bytes):
    output_dir = os.environ.get('FILE_WHISPERER_OUTPUT_DIR')
    if not output_dir:
        raise RuntimeError("FILE_WHISPERER_OUTPUT_DIR environment variable not set")

    full_path = Path(output_dir) / file_path
    
    # Ensure directory exists
    full_path.parent.mkdir(parents=True, exist_ok=True)

    with open(full_path, 'wb') as f:
        f.write(content)

def run_server(port: int):
    global server
    server_address = f'0.0.0.0:{port}'
    server = grpc.server(
        futures.ThreadPoolExecutor(max_workers=10),
        options=[
            ('grpc.max_receive_message_length', 50 * 1024 * 1024),
            ('grpc.max_send_message_length', 50 * 1024 * 1024),
        ]
    )
    
    add_WhisperServicer_to_server(GreeterServiceImpl(), server)
    server.add_insecure_port(server_address)
    server.start()
    
    logging.info(f"Server listening on {server_address}")
    
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)
    
    server.wait_for_termination()

def main():
    parser = argparse.ArgumentParser(description='FileWhisperer server')
    parser.add_argument('-p', '--port', type=int, default=50051,
                      help='Port to listen on', choices=range(1, 65536))
    parser.add_argument('-l', '--log-level', type=str, default='debug',
                      choices=['trace', 'debug', 'info', 'warn', 'error', 'critical'],
                      help='Log level')

    args = parser.parse_args()

    from loguru import logger
    import sys
    
    logger.remove()
    
    # 添加新的处理器，使用自定义格式
    logger.add(
        sys.stderr,
        # format="[<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green>] [<level>{level}</level>] [<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan>] <level>{message}</level>",
        format="[<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green>] [<level>{level}</level>] <level>{message}</level>",
        level=args.log_level.upper()
    )
    
    logger.info(f"Starting server on port {args.port} with log level {args.log_level}")
    run_server(args.port)

if __name__ == '__main__':
    main()