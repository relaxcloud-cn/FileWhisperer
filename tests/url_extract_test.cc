#include <gtest/gtest.h>
#include "extractor.hpp"

TEST(EXTRACT_URLS, single_url)
{
    std::string text = "访问我们的网站 https://www.example.com";
    std::vector<std::string> result = extractor::extract_urls_from_text(text);
    EXPECT_EQ(result.size(), 1);
    if (result.size())
    {
        EXPECT_STREQ(result[0].c_str(), "https://www.example.com");
    }
}
