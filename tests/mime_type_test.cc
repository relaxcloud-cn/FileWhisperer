#include <gtest/gtest.h>
#include <common.hpp>
#include <filesystem>

namespace test_utils {
    std::filesystem::path get_project_root() {
        return std::filesystem::path(__FILE__).parent_path().parent_path();
    }
    
    std::filesystem::path get_test_file_path(const std::string& relative_path) {
        return get_project_root() / relative_path;
    }
}

TEST(MIME, JSON) {
    std::string json_file = test_utils::get_test_file_path("tests/fixtures/1.json").string();
    EXPECT_STREQ(get_file_mime_type(json_file.c_str()).c_str(), "application/json");
}