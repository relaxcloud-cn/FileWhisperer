#include <gtest/gtest.h>
#include "test_utils.hpp"
#include "extractor.hpp"
#include "common.hpp"
#include <vector>
#include <fstream>

TEST(EXTRACT_HTML, html)
{
    std::string html_file = test_utils::get_test_file_path("tests/fixtures/sample.html").string();
    
    std::ifstream file(html_file, std::ios::binary);
    ASSERT_TRUE(file.is_open());
    
    file.seekg(0, std::ios::end);
    size_t fileSize = file.tellg();
    file.seekg(0, std::ios::beg);
    
    std::vector<uint8_t> fileData(fileSize);
    file.read(reinterpret_cast<char*>(fileData.data()), fileSize);
    file.close();
    
    std::string result = extractor::stripHtml(decode_binary(fileData));
    
    EXPECT_FALSE(result.empty());
    EXPECT_EQ(result, "URL http://en.m.wikipedia.org");
}