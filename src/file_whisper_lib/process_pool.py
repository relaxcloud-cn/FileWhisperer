"""
进程池管理器 - 用于加速慢的extractor操作
"""
import os
import json
import pickle
import multiprocessing as mp
from typing import Dict, Any, Optional, Callable, List
from concurrent.futures import ProcessPoolExecutor, Future
from loguru import logger
from threading import Lock
import time


class ExtractorProcessPool:
    """可配置的进程池管理器"""
    
    _instance = None
    _lock = Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if hasattr(self, '_initialized'):
            return
        
        self._initialized = True
        self._pools: Dict[str, ProcessPoolExecutor] = {}
        self._config = self._load_config()
        self._init_pools()
    
    def _load_config(self) -> Dict[str, Any]:
        """从环境变量加载进程池配置"""
        config = {"pools": {}}
        
        # 支持的进程池类型和默认配置
        pool_types = {
            "ocr": {"enabled": True, "workers": 2},      # OCR默认启用2个进程 
            "word": {"enabled": False, "workers": 1},    # Word默认不启用
            "pdf": {"enabled": False, "workers": 1},     # PDF默认不启用
            "html": {"enabled": False, "workers": 1},    # HTML默认不启用
            "archive": {"enabled": False, "workers": 1}  # Archive默认不启用
        }
        
        # 从环境变量读取配置
        for pool_name, defaults in pool_types.items():
            enabled_var = f'FILEWHISPERER_{pool_name.upper()}_POOL_ENABLED'
            workers_var = f'FILEWHISPERER_{pool_name.upper()}_POOL_WORKERS'
            
            # 读取是否启用
            enabled = defaults["enabled"]
            if os.environ.get(enabled_var):
                enabled = os.environ.get(enabled_var).lower() == 'true'
            
            # 读取工作进程数
            workers = defaults["workers"] 
            if os.environ.get(workers_var):
                try:
                    workers = int(os.environ.get(workers_var))
                    if workers < 1:
                        logger.warning(f"Invalid workers count for {pool_name}: {workers}, using default")
                        workers = defaults["workers"]
                except ValueError:
                    logger.warning(f"Invalid value for {workers_var}, using default")
            
            config["pools"][pool_name] = {
                "enabled": enabled,
                "workers": workers,
                "max_tasks_per_child": 50  # 固定值
            }
            
            if enabled:
                logger.info(f"Process pool '{pool_name}' enabled with {workers} workers")
        
        return config
    
    def _init_pools(self):
        """初始化进程池"""
        for pool_name, config in self._config["pools"].items():
            if config["enabled"]:
                workers = config["workers"]
                max_tasks_per_child = config.get("max_tasks_per_child", 50)
                
                try:
                    pool = ProcessPoolExecutor(
                        max_workers=workers,
                        mp_context=mp.get_context('spawn')  # 使用spawn context避免问题
                    )
                    self._pools[pool_name] = pool
                    logger.info(f"Initialized {pool_name} process pool with {workers} workers")
                except Exception as e:
                    logger.error(f"Failed to initialize {pool_name} process pool: {e}")
    
    def is_pool_enabled(self, pool_name: str) -> bool:
        """检查指定的进程池是否启用"""
        return pool_name in self._pools
    
    def submit_task(self, pool_name: str, func: Callable, *args, **kwargs) -> Optional[Future]:
        """提交任务到指定的进程池"""
        if pool_name not in self._pools:
            return None
        
        try:
            # 序列化参数用于进程间传递
            serialized_args = pickle.dumps((func, args, kwargs))
            future = self._pools[pool_name].submit(_execute_in_process, serialized_args)
            return future
        except Exception as e:
            logger.error(f"Failed to submit task to {pool_name} pool: {e}")
            return None
    
    def get_pool_status(self) -> Dict[str, Dict[str, Any]]:
        """获取所有进程池的状态信息"""
        status = {}
        for pool_name, pool in self._pools.items():
            status[pool_name] = {
                "enabled": True,
                "workers": self._config["pools"][pool_name]["workers"],
            }
        
        for pool_name, config in self._config["pools"].items():
            if pool_name not in self._pools:
                status[pool_name] = {
                    "enabled": False,
                    "workers": config["workers"]
                }
        
        return status
    
    def shutdown(self):
        """关闭所有进程池"""
        logger.info("Shutting down process pools...")
        for pool_name, pool in self._pools.items():
            try:
                pool.shutdown(wait=True, cancel_futures=True)
                logger.info(f"Shutdown {pool_name} process pool")
            except Exception as e:
                logger.error(f"Error shutting down {pool_name} pool: {e}")
        
        self._pools.clear()
    
    def __del__(self):
        self.shutdown()


def _execute_in_process(serialized_data: bytes) -> Any:
    """在进程中执行序列化的函数调用"""
    try:
        func, args, kwargs = pickle.loads(serialized_data)
        return func(*args, **kwargs)
    except Exception as e:
        logger.error(f"Error executing function in process: {e}")
        raise


# 全局进程池实例
_process_pool_instance = None

def get_process_pool() -> ExtractorProcessPool:
    """获取进程池单例实例"""
    global _process_pool_instance
    if _process_pool_instance is None:
        _process_pool_instance = ExtractorProcessPool()
    return _process_pool_instance


def shutdown_process_pools():
    """关闭进程池（用于优雅关闭）"""
    global _process_pool_instance
    if _process_pool_instance:
        _process_pool_instance.shutdown()
        _process_pool_instance = None