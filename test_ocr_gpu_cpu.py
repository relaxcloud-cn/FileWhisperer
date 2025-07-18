#!/usr/bin/env python3
"""
Test script to verify OCR GPU/CPU environment variable control
"""
import os
import hashlib

def _should_use_gpu() -> bool:
    """
    根据环境变量决定是否使用GPU
    支持完全控制和基于进程百分比的部分控制
    """
    # 检查是否强制使用CPU
    if os.environ.get("EASYOCR_FORCE_CPU", "false").lower() == "true":
        return False
    
    # 检查是否启用GPU
    gpu_enabled = os.environ.get("EASYOCR_GPU_ENABLED", "false").lower() == "true"
    if not gpu_enabled:
        return False
    
    # 检查GPU百分比设置
    gpu_percentage = float(os.environ.get("EASYOCR_GPU_PERCENTAGE", "0"))
    if gpu_percentage <= 0:
        return False
    elif gpu_percentage >= 100:
        return True
    
    # 基于进程ID和TREE_POOL_SIZE进行百分比分配
    tree_pool_size = int(os.environ.get("TREE_POOL_SIZE", "1"))
    
    # 使用进程ID的哈希值来确定性地分配GPU/CPU
    process_id = os.getpid()
    process_hash = hashlib.md5(str(process_id).encode()).hexdigest()
    process_hash_int = int(process_hash[:8], 16)
    
    # 计算应该使用GPU的进程数量
    gpu_process_count = max(1, int(tree_pool_size * gpu_percentage / 100))
    
    # 基于哈希值确定当前进程是否应该使用GPU
    process_index = process_hash_int % tree_pool_size
    should_use_gpu = process_index < gpu_process_count
    
    return should_use_gpu

def test_gpu_cpu_control():
    """Test different environment variable configurations"""
    
    # Test cases
    test_cases = [
        {
            "name": "Force CPU",
            "env": {"EASYOCR_FORCE_CPU": "true"},
            "expected": False
        },
        {
            "name": "GPU disabled",
            "env": {"EASYOCR_GPU_ENABLED": "false"},
            "expected": False
        },
        {
            "name": "GPU enabled, 0% percentage",
            "env": {"EASYOCR_GPU_ENABLED": "true", "EASYOCR_GPU_PERCENTAGE": "0"},
            "expected": False
        },
        {
            "name": "GPU enabled, 100% percentage",
            "env": {"EASYOCR_GPU_ENABLED": "true", "EASYOCR_GPU_PERCENTAGE": "100"},
            "expected": True
        },
        {
            "name": "GPU enabled, 50% percentage, pool size 4",
            "env": {"EASYOCR_GPU_ENABLED": "true", "EASYOCR_GPU_PERCENTAGE": "50", "TREE_POOL_SIZE": "4"},
            "expected": "depends on process hash"
        }
    ]
    
    for test_case in test_cases:
        print(f"\nTesting: {test_case['name']}")
        
        # Clear environment variables
        for key in ["EASYOCR_FORCE_CPU", "EASYOCR_GPU_ENABLED", "EASYOCR_GPU_PERCENTAGE", "TREE_POOL_SIZE"]:
            if key in os.environ:
                del os.environ[key]
        
        # Set test environment variables
        for key, value in test_case["env"].items():
            os.environ[key] = value
        
        # Test the function
        result = _should_use_gpu()
        print(f"  Environment: {test_case['env']}")
        print(f"  Should use GPU: {result}")
        
        if isinstance(test_case["expected"], bool):
            assert result == test_case["expected"], f"Expected {test_case['expected']}, got {result}"
            print(f"  ✓ Test passed")
        else:
            print(f"  ✓ Test result varies based on process hash (expected)")

if __name__ == "__main__":
    print("Testing OCR GPU/CPU control functionality...")
    test_gpu_cpu_control()
    print("\n✅ All tests passed!")
    
    # Example of OCRExtractor usage
    print("\n" + "="*50)
    print("Example OCRExtractor initialization:")
    
    # Set environment for partial GPU usage
    os.environ["EASYOCR_GPU_ENABLED"] = "true"
    os.environ["EASYOCR_GPU_PERCENTAGE"] = "50"
    os.environ["TREE_POOL_SIZE"] = "4"
    
    print(f"Environment settings:")
    print(f"  EASYOCR_GPU_ENABLED: {os.environ.get('EASYOCR_GPU_ENABLED')}")
    print(f"  EASYOCR_GPU_PERCENTAGE: {os.environ.get('EASYOCR_GPU_PERCENTAGE')}")
    print(f"  TREE_POOL_SIZE: {os.environ.get('TREE_POOL_SIZE')}")
    print(f"  Current PID: {os.getpid()}")
    
    # This would normally initialize EasyOCR, but we'll just check the GPU decision
    should_use_gpu = _should_use_gpu()
    print(f"  This process should use: {'GPU' if should_use_gpu else 'CPU'}")