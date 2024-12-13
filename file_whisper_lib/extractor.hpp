#include <iostream>
#include <string>
#include <vector>
#include <re2/re2.h>
#include <spdlog/spdlog.h>
#include <functional>
#include "data_type.hpp"
#include "types.hpp"

#pragma once

namespace extractor
{
    std::vector<whisper_data_type::Node *> extract_urls(whisper_data_type::Node *node);
    std::vector<std::string> extract_urls_from_text(const std::string &text);

}
