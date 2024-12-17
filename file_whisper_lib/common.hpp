#include <openssl/evp.h>
#include <iomanip>
#include <sstream>
#include <string>
#include <magic.h>
#include <unicode/ucsdet.h>
#include <unicode/ucnv.h>
#include <unicode/ustring.h>
#include <unicode/unistr.h>
#include <spdlog/spdlog.h>
#include "snowflake.hpp"

#pragma once

std::string calculate_md5(const uint8_t *data, size_t length);
std::string calculate_sha256(const uint8_t *data, size_t length);
std::string get_file_mime_type(const char *file);
std::string get_buffer_mime_type(const uint8_t *data, size_t length);
struct EncodingResult {
    std::string encoding;
    int32_t confidence;
    
    EncodingResult(const std::string& enc = "", int32_t conf = 0) 
        : encoding(enc), confidence(conf) {}
};
EncodingResult detect_encoding(const std::vector<uint8_t> &data);
std::vector<EncodingResult> detect_encodings(const std::vector<uint8_t>& data, int32_t max_matches = 3);
std::string decode_binary(const std::vector<uint8_t>& data);
std::vector<uint8_t> encode_binary(const std::string& str);
