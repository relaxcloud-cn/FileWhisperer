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
import threading
import queue

# os.environ['PADDLEOCR_LOG_LEVEL'] = '3'
# logging.getLogger("paddle").setLevel(logging.ERROR)
# logging.getLogger("paddleocr").setLevel(logging.ERROR)

# Assuming these are generated from your protobuf definitions
from file_whisper_pb2 import WhisperRequest, WhisperReply, Node, File, Data, Meta
from file_whisper_pb2_grpc import WhisperServicer, add_WhisperServicer_to_server
from file_whisper_lib.dt import Node as DataNode, File as DataFile, Data as DataData
from file_whisper_lib.tree import Tree

server = None

def calculate_worker_count(env_var: str, default_value: str, cpu_count: int) -> int:
    """
    根据环境变量计算worker数量
    - 负整数：逻辑核数的倍数 (如 -2 表示 cpu_count * 2)
    - 正整数：具体的个数
    - 0~1的小数：逻辑核数乘以这个数
    """
    value_str = os.environ.get(env_var, default_value)
    
    try:
        value = float(value_str)
        
        if value < 0:
            # 负数：逻辑核数的倍数
            result = int(cpu_count * abs(value))
        elif 0 < value < 1:
            # 0~1小数：逻辑核数乘以这个数
            result = int(cpu_count * value)
        elif value >= 1:
            # 正整数：具体个数
            result = int(value)
        else:
            # value == 0
            result = 1
            
        return max(1, result)  # 至少1个
        
    except ValueError:
        from loguru import logger
        logger.warning(f"Invalid {env_var} value: {value_str}, using default")
        return max(1, int(float(default_value)) if float(default_value) >= 1 else int(cpu_count * float(default_value)))

class TreePool:
    """Tree实例池，管理多个Tree实例用于并发处理"""
    
    def __init__(self, pool_size: int = None):
        if pool_size is None:
            pool_size = os.cpu_count() or 1
        
        self.pool_size = pool_size
        self.pool = queue.Queue()
        self._lock = threading.Lock()
        
        # 初始化Tree实例池
        for _ in range(pool_size):
            tree = Tree()
            self.pool.put(tree)
        
        from loguru import logger
        logger.info(f"TreePool initialized with {pool_size} Tree instances")
    
    def acquire(self, timeout: float = None) -> Tree:
        """获取一个空闲的Tree实例，超时则抛出异常"""
        if timeout is None:
            timeout = float(os.environ.get('TREE_POOL_ACQUIRE_TIMEOUT', '3'))
        
        try:
            return self.pool.get(block=True, timeout=timeout)
        except queue.Empty:
            raise RuntimeError(f"No available Tree instances in pool (pool_size={self.pool_size}), timeout after {timeout}s")
    
    def release(self, tree: Tree):
        """归还Tree实例到池中，并清除其状态"""
        tree.clear_state()
        self.pool.put(tree)

class GreeterServiceImpl(WhisperServicer):
    def __init__(self, tree_pool: TreePool):
        # 使用Tree实例池而不是单个Tree实例
        self.tree_pool = tree_pool
    
    def _backup_request_file(self, file_content: bytes, file_path: str, backup_dir: str):
        """
        将WhisperRequest传输的文件备份到指定目录
        """
        import datetime
        from loguru import logger
        
        try:
            # 确保备份目录存在
            backup_path = Path(backup_dir)
            backup_path.mkdir(parents=True, exist_ok=True)
            
            # 生成唯一的备份文件名
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S_%f")
            original_name = os.path.basename(file_path)
            backup_filename = f"{timestamp}_{original_name}"
            backup_file_path = backup_path / backup_filename
            
            # 写入备份文件
            with open(backup_file_path, 'wb') as f:
                f.write(file_content)
            
            logger.debug(f"Debug backup saved: {backup_file_path}")
            
        except Exception as e:
            logger.error(f"Failed to backup request file: {e}")
    
    def Whispering(self, request: WhisperRequest, context) -> WhisperReply:
        tree = None
        try:
            # 从池中获取一个空闲的Tree实例
            tree = self.tree_pool.acquire()
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

            # Debug备份功能：如果设置了FILE_WHISPERER_DEBUG_BACKUP_DIR环境变量，则保存文件
            backup_dir = os.environ.get('FILE_WHISPERER_DEBUG_BACKUP_DIR')
            if backup_dir:
                self._backup_request_file(file_content, file_path, backup_dir)

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
        finally:
            # 确保Tree实例被归还到池中
            if tree is not None:
                self.tree_pool.release(tree)

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
    from loguru import logger
    
    global server
    server_address = f'0.0.0.0:{port}'
    
    # 计算CPU逻辑核数和线程池大小
    cpu_count = os.cpu_count()
    
    # 通过环境变量配置gRPC线程池大小
    max_workers = calculate_worker_count('GRPC_MAX_WORKERS', '0.5', cpu_count)
    
    # 通过环境变量配置Tree实例池大小
    tree_pool_size = calculate_worker_count('TREE_POOL_SIZE', '0.5', cpu_count)
    
    logger.info(f"系统CPU逻辑核数: {cpu_count}")
    logger.info(f"ThreadPoolExecutor 线程数设置为: {max_workers} (环境变量 GRPC_MAX_WORKERS)")
    logger.info(f"TreePool 实例数设置为: {tree_pool_size} (环境变量 TREE_POOL_SIZE)")
    
    tree_pool = TreePool(pool_size=tree_pool_size)
    
    server = grpc.server(
        futures.ThreadPoolExecutor(max_workers=max_workers),
        options=[
            ('grpc.max_receive_message_length', 50 * 1024 * 1024),
            ('grpc.max_send_message_length', 50 * 1024 * 1024),
        ]
    )
    
    add_WhisperServicer_to_server(GreeterServiceImpl(tree_pool), server)
    server.add_insecure_port(server_address)
    server.start()
    
    logger.info(f"Server listening on {server_address}")
    
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