#pragma once
#include <map>

namespace whisper_data_type
{

    enum Types
    {
        TEXT_PLAIN,
        COMPRESSED_FILE,
        OTHER
    };

    const std::map<std::string, Types> Types__1 = {
        {"text/plain", TEXT_PLAIN},
        {"application/zip", COMPRESSED_FILE},
        {"application/x-rar-compressed", COMPRESSED_FILE},
        {"application/vnd.rar", COMPRESSED_FILE},
        {"application/x-7z-compressed", COMPRESSED_FILE},
        {"application/x-tar", COMPRESSED_FILE},
        {"application/gzip", COMPRESSED_FILE},
        {"application/x-gzip", COMPRESSED_FILE},
        {"application/x-bzip2", COMPRESSED_FILE},
        {"application/x-xz", COMPRESSED_FILE},
    };
}
