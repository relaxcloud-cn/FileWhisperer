#include <gtest/gtest.h>
#include "test_utils.hpp"
#include "extractor.hpp"
#include <vector>
#include <fstream>

TEST(EXTRACT_QRCODE, qrcode_wikipedia)
{
    std::string json_file = test_utils::get_test_file_path("tests/fixtures/qrcode_wikipedia.jpg").string();
    
    std::ifstream file(json_file, std::ios::binary);
    ASSERT_TRUE(file.is_open());
    
    file.seekg(0, std::ios::end);
    size_t fileSize = file.tellg();
    file.seekg(0, std::ios::beg);
    
    std::vector<uint8_t> fileData(fileSize);
    file.read(reinterpret_cast<char*>(fileData.data()), fileSize);
    file.close();
    
    std::string result = extractor::decodeQRCode(fileData);
    
    EXPECT_FALSE(result.empty());
    EXPECT_EQ(result, "http://en.m.wikipedia.org");
}