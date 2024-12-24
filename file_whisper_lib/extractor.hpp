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
#include <opencv2/opencv.hpp>
#include <gumbo.h>
#include <tesseract/baseapi.h>
#include <leptonica/allheaders.h>
#include <ZXing/ReadBarcode.h>

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
    std::vector<Node *> extract_qrcode(Node *node);
    std::string decodeQRCode(const std::vector<uint8_t> &file);
    std::string decodeQRCodeZXing(const std::vector<uint8_t> &file);
    std::vector<Node *> extract_html(Node *node);
    std::string extractHtmlText(GumboNode *node);
    std::string stripHtml(const std::string &html);
    std::vector<Node *> extract_ocr(Node *node);
    class OCRHelper
    {
    public:
        OCRHelper();
        ~OCRHelper();

        // 删除拷贝构造和赋值操作符
        OCRHelper(const OCRHelper &) = delete;
        OCRHelper &operator=(const OCRHelper &) = delete;

        std::string recognize_image(const std::vector<uint8_t> &image_data);

    private:
        tesseract::TessBaseAPI *ocr_;
    };
}
