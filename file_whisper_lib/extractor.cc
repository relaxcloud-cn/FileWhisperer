#include "extractor.hpp"

std::vector<std::string> extract_urls(const std::string& text) {
    static const re2::RE2 url_pattern("(https?://[^\\s\"<>{}]+)");

    std::vector<std::string> urls;
    re2::StringPiece input(text);
    std::string url;

    while (RE2::FindAndConsume(&input, url_pattern, &url)) {
        urls.push_back(url);
    }

    return urls;
}