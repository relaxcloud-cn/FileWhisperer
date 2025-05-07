#!/usr/bin/env python
"""
检查系统库和环境变量，特别是CUDA和cuDNN相关的库
"""
import os
import subprocess
import sys
from loguru import logger

def run_cmd(cmd):
    """运行命令并返回输出"""
    try:
        result = subprocess.run(cmd, shell=True, check=True, capture_output=True, text=True)
        return result.stdout
    except subprocess.CalledProcessError as e:
        return f"Error: {e.stderr}"

def check_environment():
    """检查环境变量"""
    logger.info("=== 环境变量 ===")
    for var in ['LD_LIBRARY_PATH', 'CUDA_HOME', 'PATH']:
        value = os.environ.get(var, 'Not set')
        logger.info(f"{var}: {value}")

def check_cuda_libs():
    """检查CUDA库"""
    logger.info("=== CUDA 库位置 ===")
    libs = [
        'libcudnn.so',
        'libcudart.so',
        'libcublas.so',
        'libcufft.so',
        'libcurand.so',
        'libcusolver.so',
        'libcusparse.so'
    ]
    
    for lib in libs:
        output = run_cmd(f"find /usr -name '{lib}*' 2>/dev/null || echo 'Not found in /usr'")
        output += run_cmd(f"find /root/miniconda3 -name '{lib}*' 2>/dev/null || echo 'Not found in conda'")
        logger.info(f"{lib}: {output.replace(chr(10), ' ')}")

def check_paddle_config():
    """检查PaddlePaddle配置"""
    try:
        import paddle
        logger.info("=== PaddlePaddle 配置 ===")
        logger.info(f"版本: {paddle.__version__}")
        logger.info(f"安装路径: {paddle.__file__}")
        logger.info(f"compiled with CUDA: {paddle.device.is_compiled_with_cuda()}")
        if paddle.device.is_compiled_with_cuda():
            try:
                cuda_version = paddle.version.cuda()
                logger.info(f"CUDA版本: {cuda_version}")
            except:
                logger.error("无法获取CUDA版本")
            
            try:
                cudnn_version = paddle.version.cudnn()
                logger.info(f"cuDNN版本: {cudnn_version}")
            except:
                logger.error("无法获取cuDNN版本")
    except ImportError:
        logger.error("PaddlePaddle未安装")

if __name__ == "__main__":
    logger.add("libs_check.log")
    logger.info("开始检查系统库和环境")
    check_environment()
    check_cuda_libs()
    check_paddle_config()
    logger.info("检查完成，详细结果已记录到libs_check.log") 