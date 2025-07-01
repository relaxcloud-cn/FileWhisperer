#!/usr/bin/env python3
"""
并发测试脚本 - 用于测试 FileWhisperer gRPC 服务的并发性能

使用示例:
    python tests/test_concurrent.py --dir /root/eml/5.0/100封钓鱼/ --workers 10 --repeat 3
    python tests/test_concurrent.py --dir /path/to/files --workers 20 --duration 60
"""

import argparse
import os
import sys
import time
import threading
import statistics
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from typing import List, Dict, Any
import grpc

# 添加src目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
import file_whisper_pb2
import file_whisper_pb2_grpc


@dataclass
class TestResult:
    """测试结果数据类"""
    file_path: str
    success: bool
    duration: float
    error: str = ""
    node_count: int = 0
    file_size: int = 0


class ConcurrentTester:
    """并发测试器"""
    
    def __init__(self, host: str = "localhost", port: int = 50051):
        self.host = host
        self.port = port
        self.results: List[TestResult] = []
        self.results_lock = threading.Lock()
        self.start_time = None
        self.end_time = None
        
    def create_stub(self):
        """创建gRPC客户端连接"""
        channel = grpc.insecure_channel(f'{self.host}:{self.port}')
        return file_whisper_pb2_grpc.WhisperStub(channel), channel
    
    def process_single_file(self, file_path: str, binary: bool = True, 
                          passwords: List[str] = None, 
                          pdf_max_pages: int = None,
                          word_max_pages: int = None) -> TestResult:
        """处理单个文件"""
        if passwords is None:
            passwords = []
            
        try:
            # 获取文件大小
            file_size = os.path.getsize(file_path)
            
            # 创建连接
            stub, channel = self.create_stub()
            
            try:
                # 准备请求参数
                request_params = {
                    'passwords': passwords
                }
                
                if pdf_max_pages is not None:
                    request_params['pdf_max_pages'] = pdf_max_pages
                    
                if word_max_pages is not None:
                    request_params['word_max_pages'] = word_max_pages
                
                # 读取文件内容
                if binary:
                    with open(file_path, 'rb') as f:
                        file_content = f.read()
                    request_params['file_content'] = file_content
                else:
                    request_params['file_path'] = file_path
                
                request = file_whisper_pb2.WhisperRequest(**request_params)
                
                # 执行请求并计时
                start_time = time.time()
                response = stub.Whispering(request)
                end_time = time.time()
                
                duration = end_time - start_time
                node_count = len(response.tree)
                
                return TestResult(
                    file_path=file_path,
                    success=True,
                    duration=duration,
                    node_count=node_count,
                    file_size=file_size
                )
                
            finally:
                channel.close()
                
        except Exception as e:
            return TestResult(
                file_path=file_path,
                success=False,
                duration=0.0,
                error=str(e),
                file_size=file_size
            )
    
    def add_result(self, result: TestResult):
        """线程安全地添加测试结果"""
        with self.results_lock:
            self.results.append(result)
    
    def collect_files(self, directory: str, pattern: str = "*") -> List[str]:
        """收集目录下的所有文件"""
        path = Path(directory)
        if not path.exists():
            raise ValueError(f"Directory does not exist: {directory}")
        
        if path.is_file():
            return [str(path)]
        
        files = []
        for file_path in path.rglob(pattern):
            if file_path.is_file():
                files.append(str(file_path))
        
        return sorted(files)
    
    def run_test(self, directory: str, workers: int = 10, repeat: int = 1, 
                 duration: int = None, binary: bool = True, 
                 passwords: List[str] = None, pattern: str = "*",
                 pdf_max_pages: int = None, word_max_pages: int = None):
        """运行并发测试"""
        
        print(f"正在收集文件从目录: {directory}")
        files = self.collect_files(directory, pattern)
        
        if not files:
            print(f"在目录 {directory} 中没有找到文件 (pattern: {pattern})")
            return
        
        print(f"找到 {len(files)} 个文件")
        print(f"并发线程数: {workers}")
        print(f"重复次数: {repeat}")
        if duration:
            print(f"运行时长: {duration} 秒")
        print("=" * 60)
        
        # 准备测试文件列表
        test_files = []
        if duration:
            # 按时间运行测试
            self.start_time = time.time()
            while time.time() - self.start_time < duration:
                test_files.extend(files)
        else:
            # 按重复次数运行测试
            for _ in range(repeat):
                test_files.extend(files)
        
        total_tests = len(test_files)
        print(f"总测试数: {total_tests}")
        
        self.start_time = time.time()
        
        # 启动并发测试
        completed = 0
        with ThreadPoolExecutor(max_workers=workers) as executor:
            # 提交所有任务
            futures = [
                executor.submit(
                    self.process_single_file, 
                    file_path, 
                    binary, 
                    passwords,
                    pdf_max_pages,
                    word_max_pages
                )
                for file_path in test_files
            ]
            
            # 处理完成的任务
            for future in as_completed(futures):
                try:
                    result = future.result()
                    self.add_result(result)
                    completed += 1
                    
                    # 实时进度显示
                    if completed % max(1, total_tests // 20) == 0 or completed == total_tests:
                        progress = (completed / total_tests) * 100
                        elapsed = time.time() - self.start_time
                        rate = completed / elapsed if elapsed > 0 else 0
                        print(f"进度: {completed}/{total_tests} ({progress:.1f}%) "
                              f"- 速率: {rate:.1f} req/s - 已用时: {elapsed:.1f}s")
                        
                        # 如果是按时间运行，检查是否超时
                        if duration and elapsed >= duration:
                            break
                            
                except Exception as e:
                    print(f"处理任务时出错: {e}")
        
        self.end_time = time.time()
        self.print_statistics()
    
    def print_statistics(self):
        """打印测试统计信息"""
        if not self.results:
            print("没有测试结果")
            return
        
        total_duration = self.end_time - self.start_time
        total_tests = len(self.results)
        successful_tests = [r for r in self.results if r.success]
        failed_tests = [r for r in self.results if not r.success]
        
        success_rate = len(successful_tests) / total_tests * 100
        failure_rate = len(failed_tests) / total_tests * 100
        throughput = total_tests / total_duration
        
        print("\n" + "=" * 60)
        print("测试统计结果")
        print("=" * 60)
        print(f"总测试数:     {total_tests}")
        print(f"成功数:       {len(successful_tests)} ({success_rate:.1f}%)")
        print(f"失败数:       {len(failed_tests)} ({failure_rate:.1f}%)")
        print(f"总耗时:       {total_duration:.2f} 秒")
        print(f"吞吐量:       {throughput:.2f} req/s")
        
        if successful_tests:
            durations = [r.duration for r in successful_tests]
            file_sizes = [r.file_size for r in successful_tests]
            node_counts = [r.node_count for r in successful_tests]
            
            print(f"\n响应时间统计 (成功请求):")
            print(f"  平均响应时间: {statistics.mean(durations):.3f} 秒")
            print(f"  中位数响应时间: {statistics.median(durations):.3f} 秒")
            print(f"  最短响应时间: {min(durations):.3f} 秒")
            print(f"  最长响应时间: {max(durations):.3f} 秒")
            if len(durations) > 1:
                print(f"  响应时间标准差: {statistics.stdev(durations):.3f} 秒")
            
            print(f"\n文件大小统计:")
            print(f"  平均文件大小: {statistics.mean(file_sizes)/1024:.1f} KB")
            print(f"  总处理字节数: {sum(file_sizes)/1024/1024:.1f} MB")
            
            print(f"\n节点数统计:")
            print(f"  平均节点数: {statistics.mean(node_counts):.1f}")
            print(f"  总节点数: {sum(node_counts)}")
        
        if failed_tests:
            print(f"\n失败原因统计:")
            error_counts = {}
            for test in failed_tests:
                error_type = test.error.split(':')[0] if ':' in test.error else test.error
                error_counts[error_type] = error_counts.get(error_type, 0) + 1
            
            for error, count in sorted(error_counts.items(), key=lambda x: x[1], reverse=True):
                print(f"  {error}: {count} 次")
        
        print("=" * 60)


def main():
    parser = argparse.ArgumentParser(description='FileWhisperer 并发测试工具')
    parser.add_argument('--dir', required=True, help='测试文件目录路径')
    parser.add_argument('--host', default='localhost', help='gRPC服务器地址 (默认: localhost)')
    parser.add_argument('--port', type=int, default=50051, help='gRPC服务器端口 (默认: 50051)')
    parser.add_argument('--workers', type=int, default=10, help='并发线程数 (默认: 10)')
    parser.add_argument('--repeat', type=int, default=1, help='每个文件重复测试次数 (默认: 1)')
    parser.add_argument('--duration', type=int, help='运行时长(秒)，指定则忽略repeat参数')
    parser.add_argument('--pattern', default='*', help='文件匹配模式 (默认: *)')
    parser.add_argument('--no-binary', action='store_true', help='使用文件路径而不是二进制内容')
    parser.add_argument('--password', '-p', action='append', help='密码列表 (可多次指定)')
    parser.add_argument('--pdf-max-pages', type=int, help='PDF最大处理页数')
    parser.add_argument('--word-max-pages', type=int, help='Word最大处理页数')
    
    args = parser.parse_args()
    
    # 创建并运行测试
    tester = ConcurrentTester(host=args.host, port=args.port)
    
    try:
        tester.run_test(
            directory=args.dir,
            workers=args.workers,
            repeat=args.repeat,
            duration=args.duration,
            binary=not args.no_binary,
            passwords=args.password or [],
            pattern=args.pattern,
            pdf_max_pages=args.pdf_max_pages,
            word_max_pages=args.word_max_pages
        )
    except KeyboardInterrupt:
        print("\n测试被用户中断")
        if tester.results:
            tester.end_time = time.time()
            tester.print_statistics()
    except Exception as e:
        print(f"测试过程中出错: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()