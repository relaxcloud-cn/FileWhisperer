#include <gtest/gtest.h>
#include "test_utils.hpp"
#include <common.hpp>

TEST(MIME, JSON) {
    std::string json_file = test_utils::get_test_file_path("tests/fixtures/1.json").string();
    EXPECT_STREQ(get_file_mime_type(json_file.c_str()).c_str(), "application/json");
}