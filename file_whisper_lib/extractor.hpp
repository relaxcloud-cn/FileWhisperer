#include <iostream>
#include <string>
#include <vector>
#include <memory>
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

namespace extractor {
    using namespace whisper_data_type;
    
    // URL extraction
    std::vector<std::shared_ptr<Node>> extract_urls(std::shared_ptr<Node> node);
    std::vector<std::string> extract_urls_from_text(const std::string& text);
    
    // Compressed file handling
    std::vector<std::shared_ptr<Node>> extract_compressed_file(std::shared_ptr<Node> node);
    std::map<std::string, std::vector<uint8_t>> extract_files_from_data(
        const std::vector<uint8_t> file, 
        std::string password = ""
    );
    
    // QR code processing
    std::vector<std::shared_ptr<Node>> extract_qrcode(std::shared_ptr<Node> node);
    std::string decodeQRCode(const std::vector<uint8_t>& file);
    std::string decodeQRCodeZXing(const std::vector<uint8_t>& file);
    
    // HTML processing
    std::vector<std::shared_ptr<Node>> extract_html(std::shared_ptr<Node> node);
    std::string extractHtmlText(GumboNode* node);
    std::string stripHtml(const std::string& html);
    
    // OCR processing
    std::vector<std::shared_ptr<Node>> extract_ocr(std::shared_ptr<Node> node);
    
    class OCRHelper {
    public:
        OCRHelper();
        ~OCRHelper();

        // Delete copy constructor and assignment operator
        OCRHelper(const OCRHelper&) = delete;
        OCRHelper& operator=(const OCRHelper&) = delete;

        std::string recognize_image(const std::vector<uint8_t>& image_data);

    private:
        tesseract::TessBaseAPI* ocr_;
    };
}