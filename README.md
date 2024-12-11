# FileWhisperer: LLM Friendly Local Doc Parser

FileWhisperer 是一个专注于将多种文件类型解析为 LLM 友好 结构化数据的工具。它能高效提取文件中的 文字、URL、元数据、嵌套关系 等深度信息，并以清晰的结构化格式输出，方便大语言模型（LLM）直接处理。

---

# 环境变量

## vcpkg 根目录

```sh
VCPKG_ROOT
```

## libmagic 魔术文件路径

```sh
MAGIC_MGC_PATH
```

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

## gRPC

### 查看所有的 proto 

```sh
make list
```