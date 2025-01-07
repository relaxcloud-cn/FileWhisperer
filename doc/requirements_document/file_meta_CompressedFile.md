# 压缩文件相关标识

## mime type

```
application/zip
application/x-rar-compressed
application/vnd.rar
application/x-7z-compressed
application/x-tar
application/gzip
application/x-gzip
application/x-bzip2
application/x-xz
```

## map_string

键名 | 说明 | 状态
---|---|---
correct_password| 正确密码 | yes

## map_number

键名 | 说明 | 状态
---|---|---
items_count | 归档总数量 | yes
folders_count | 文件夹数量 | yes
files_count | 文件数量 | yes
size | 未压缩时的大小 | yes 
pack_size | 压缩后的大小 | yes
volumes_count | 分卷数量 | yes

## map_bool

键名 | 说明| 状态
---|---|---
is_encrypted | 是否加密 | yes
is_multi_volume | 是否分卷压缩 | yes
