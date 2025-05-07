#!/bin/bash
# 设置CUDA环境变量，使PaddlePaddle能够找到所需的CUDA和cuDNN库

# 设置库路径
export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:/root/miniconda3/envs/filewhisperer/lib
echo "LD_LIBRARY_PATH已设置为: $LD_LIBRARY_PATH"

# 如果想使用GPU，取消下面注释，但在解决所有依赖问题前先使用CPU
# export CUDA_VISIBLE_DEVICES=0 
export CUDA_VISIBLE_DEVICES=-1  # 强制使用CPU模式

echo "已强制使用CPU模式：CUDA_VISIBLE_DEVICES=$CUDA_VISIBLE_DEVICES"
echo "环境变量已设置，现在可以启动服务器" 