import paddle
from loguru import logger

logger.info(f"PaddlePaddle 版本: {paddle.__version__}")
logger.info(f"PaddlePaddle 已编译 CUDA 支持: {paddle.device.is_compiled_with_cuda()}")
logger.info(f"CUDA 设备数量: {paddle.device.cuda.device_count() if paddle.device.is_compiled_with_cuda() else 0}")
logger.info(f"可用设备: {paddle.device.get_available_device()}")

if paddle.device.is_compiled_with_cuda():
    logger.success("成功: PaddlePaddle 支持 CUDA，可以使用 GPU 加速")
else:
    logger.error("错误: PaddlePaddle 不支持 CUDA，将使用 CPU 模式") 