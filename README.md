# FileWhisperer: LLM Friendly Local Doc Parser

FileWhisperer 是一个专注于将多种文件类型解析为 LLM 友好 结构化数据的工具。它能高效提取文件中的 文字、URL、元数据、嵌套关系 等深度信息，并以清晰的结构化格式输出，方便大语言模型（LLM）直接处理。

---

# 需求

[requirements](./doc/requirements_document/requirements.md)

---

# 数据结构说明

## FileWhisperer 扫描请求

[WhisperRequest](./doc/grpc/request/WhisperRequest.md)

## FileWhisperer 扫描返回结果

[WhisperReply](./doc/grpc/reply/WhisperReply.md)

# 环境变量

[environment variable](./doc/env.md)

---

# 测试

## 启用单元测试

```sh
cmake -DBUILD_TESTING=ON build
```

## 测试命令

```sh
ctest --test-dir build
```

---

# 开发环境

## 分支合并说明

doc --> dev --> main

## gRPC

### 查看所有的 proto 

```sh
make list
```

## 请求服务

可以使用、参考项目文件 `py/client.py` 。

```sh
# python py/client.py --help
Usage: client.py [OPTIONS] COMMAND [ARGS]...

  Archive extractor CLI tool

Options:
  --help  Show this message and exit.

Commands:
  run
```

示例命令：

```sh
python src/client.py run tests/fixtures/test_with_pwd_abcd.zip --binary -p123 -pabcd
python src/client.py run tests/fixtures/image_cn.png --binary -p123 -pabcd --port 50098 --host 192.168.2.225
```

```
# 安装存储库
curl -s -L https://nvidia.github.io/libnvidia-container/stable/rpm/nvidia-container-toolkit.repo | \
  sudo tee /etc/yum.repos.d/nvidia-container-toolkit.repo

# 安装包
sudo yum install -y nvidia-container-toolkit

# 配置Docker使用NVIDIA运行时
sudo nvidia-ctk runtime configure --runtime=docker

# 重启Docker服务
sudo systemctl restart docker
```

```
# 测试指定目录下所有文件，10个并发线程，每个文件测试3次
python tests/test_concurrent.py --dir /root/eml/5.0/100封钓鱼/ --workers 10 --repeat 3

# 运行60秒压力测试，20个并发线程
python tests/test_concurrent.py --dir /path/to/files --workers 20 --duration 60

# 测试特定文件类型，带密码
python tests/test_concurrent.py --dir /path/to/files --pattern "*.zip" --workers 5 -p password1 -p password2

# 连接远程服务器测试
python tests/test_concurrent.py --dir /path/to/files --host 192.168.1.100 --port 50098 --workers 15
```