#include <iostream>
#include <string>
#include <vector>
#include <re2/re2.h>
#include <spdlog/spdlog.h>
#include <functional>
#include <stdexcept>
#include <bit7z/bitfileextractor.hpp>
#include <bit7z/bit7zlibrary.hpp>
#include <bit7z/bitexception.hpp>
#include <bit7z/bitarchivereader.hpp>
#include "bit7z/biterror.hpp"
#include "data_type.hpp"
#include "types.hpp"

#pragma once

namespace extractor
{
    using namespace whisper_data_type;
    std::vector<Node *> extract_urls(Node *node);
    std::vector<std::string> extract_urls_from_text(const std::string &text);
    std::vector<Node *> extract_compressed_file(Node *node);
    std::map<std::string, std::vector<uint8_t>> extract_files_from_data(const std::vector<uint8_t> file, std::string password = "");
}
