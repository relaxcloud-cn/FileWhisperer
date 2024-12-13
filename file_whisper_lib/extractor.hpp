#include <iostream>
#include <string>
#include <vector>
#include <re2/re2.h>
#include <spdlog/spdlog.h>
#include "mime_type_enum.hpp"

std::vector<std::string> extract_urls(const std::string &text);

