# proto

```
message WhisperRequest {
  oneof data {
    string file_path = 1;
    bytes file_content = 2;
  }
  repeated string passwords = 3;
  optional int64 root_id = 4;
}
```

# desc

## 文件输入

```
oneof data {
    string file_path
    bytes file_content
}
```

传输文件路径或者文件二进制数据。

## 密码

```
repeated string passwords
```

传入密码数组，如果没有密码，传入空数组。

## 根结点 id

```
optional int64 root_id
```

调用方可以根据自己的 ID 分配情况，选择设置根结点 ID。
如果没有传 root_id， FileWhisperer 会自动为根结点生成一个雪花 ID。