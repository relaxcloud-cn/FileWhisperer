#pragma once
#include <map>

namespace whisper_data_type
{

    enum Types
    {
        TEXT_PLAIN,
        OTHER
    };

    const std::map<std::string, Types> Types__1 = {
        {"text/plain", TEXT_PLAIN}};
}
