#pragma once
#include <string>
#include <filesystem>

namespace test_utils {
    std::filesystem::path get_project_root();
    std::filesystem::path get_test_file_path(const std::string& relative_path);
}
