import click
import grpc
import file_whisper_pb2
import file_whisper_pb2_grpc
import os
from concurrent.futures import ThreadPoolExecutor
import threading
import argparse
import sys
import json
import time

print_lock = threading.Lock()

@click.group()
def cli():
    """Archive extractor CLI tool"""
    pass

def safe_print(*args, **kwargs):
    """线程安全的打印函数"""
    with print_lock:
        print(*args, **kwargs)

def process_file(stub, file_path, binary, password, root_id, pdf_max_pages, word_max_pages):
    try:
        request_params = {
            'passwords': list(password)
        }
        
        if root_id is not None:
            request_params['root_id'] = root_id
            
        if pdf_max_pages is not None:
            request_params['pdf_max_pages'] = pdf_max_pages
            
        if word_max_pages is not None:
            request_params['word_max_pages'] = word_max_pages
            
        if binary:
            with open(file_path, 'rb') as f:
                file_content = f.read()
            request_params['file_content'] = file_content
        else:
            request_params['file_path'] = file_path
            
        request = file_whisper_pb2.WhisperRequest(**request_params)
        
        start_time = time.time()
        response = stub.Whispering(request)
        end_time = time.time()
        elapsed_time = end_time - start_time
        
        safe_print(f"\nProcessing: {file_path}")
        safe_print(f"总耗时: {elapsed_time:.3f} 秒")
        safe_print("=" * 50)
        
        for node in response.tree:
            safe_print(f"Node ID: {node.id}")
            safe_print(f"Parent ID: {node.parent_id}")
            safe_print(f"Children: {node.children}")
            
            if node.HasField('file'):
                file = node.file
                safe_print(f"File: {file.path}")
                safe_print(f"Name: {file.name}")
                safe_print(f"Size: {file.size}")
                safe_print(f"MIME Type: {file.mime_type}")
                safe_print(f"Extension: {file.extension}")
                safe_print(f"MD5: {file.md5}")
                safe_print(f"SHA256: {file.sha256}")
                safe_print(f"SHA1: {file.sha1}")
                if file.HasField('content'):
                    safe_print(f"Content length: {len(file.content)}")
            elif node.HasField('data'):
                data = node.data
                safe_print(f"Data type: {data.type}")
                if data.type == 'OCR':
                    try:
                        decoded_content = data.content.decode('utf-8')
                        safe_print(f"OCR Content: {decoded_content}")
                    except Exception as e:
                        safe_print(f"OCR Content (decode error): {data.content}")
                        safe_print(f"Decode error: {e}")
                else:
                    safe_print(f"Content length: {data.content[:100]}")
            
            if node.HasField('meta'):
                meta = node.meta
                if meta.map_string:
                    safe_print("Meta Strings:")
                    for key, value in meta.map_string.items():
                        safe_print(f"  {key}: {value}")
                if meta.map_number:
                    safe_print("Meta Numbers:")
                    for key, value in meta.map_number.items():
                        safe_print(f"  {key}: {value}")
                if meta.map_bool:
                    safe_print("Meta Booleans:")
                    for key, value in meta.map_bool.items():
                        safe_print(f"  {key}: {value}")
            
            safe_print("---")
    except Exception as e:
        safe_print(f"Error processing {file_path}: {str(e)}")

@cli.command()
@click.option('--host', default='localhost', help='gRPC server host')
@click.option('--port', default=50051, help='gRPC server port')
@click.option('--binary', is_flag=True, help='Send file as binary content instead of path')
@click.option('--password', '-p', multiple=True, help='Passwords to try')
@click.option('--root-id', type=int, help='Root ID for the request')
@click.option('--max-workers', default=4, help='Maximum number of worker threads')
@click.option('--pdf-max-pages', type=int, help='Maximum number of pages to process for PDF documents')
@click.option('--word-max-pages', type=int, help='Maximum number of pages to process for Word documents')
@click.argument('path', type=click.Path(exists=True))
def run(host, port, binary, password, root_id, max_workers, pdf_max_pages, word_max_pages, path):
    channel = grpc.insecure_channel(f'{host}:{port}')
    stub = file_whisper_pb2_grpc.WhisperStub(channel)
    
    overall_start_time = time.time()
    
    try:
        if os.path.isfile(path):
            process_file(stub, path, binary, password, root_id, pdf_max_pages, word_max_pages)
        else:
            file_paths = []
            for root, _, files in os.walk(path):
                for file in files:
                    file_paths.append(os.path.join(root, file))
            
            print(f"发现 {len(file_paths)} 个文件，开始批量处理...")
            
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                futures = [
                    executor.submit(process_file, stub, file_path, binary, password, root_id, pdf_max_pages, word_max_pages)
                    for file_path in file_paths
                ]
                
                for future in futures:
                    future.result()
    
    finally:
        overall_end_time = time.time()
        overall_elapsed_time = overall_end_time - overall_start_time
        print(f"\n所有任务完成，总耗时: {overall_elapsed_time:.3f} 秒")
        channel.close()

if __name__ == "__main__":
    cli()