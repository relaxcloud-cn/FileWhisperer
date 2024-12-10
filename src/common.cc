#include "common.hpp"

std::string calculate_md5(const uint8_t* data, size_t length) {
    unsigned char result[EVP_MAX_MD_SIZE];
    unsigned int resultLen;
    
    EVP_MD_CTX* ctx = EVP_MD_CTX_new();
    EVP_DigestInit_ex(ctx, EVP_md5(), NULL);
    EVP_DigestUpdate(ctx, data, length);
    EVP_DigestFinal_ex(ctx, result, &resultLen);
    EVP_MD_CTX_free(ctx);
    
    std::stringstream ss;
    for(int i = 0; i < resultLen; i++) {
        ss << std::hex << std::setw(2) << std::setfill('0') << static_cast<int>(result[i]);
    }
    return ss.str();
}

std::string calculate_sha256(const uint8_t* data, size_t length) {
    unsigned char result[EVP_MAX_MD_SIZE];
    unsigned int resultLen;
    
    EVP_MD_CTX* ctx = EVP_MD_CTX_new();
    EVP_DigestInit_ex(ctx, EVP_sha256(), NULL);
    EVP_DigestUpdate(ctx, data, length);
    EVP_DigestFinal_ex(ctx, result, &resultLen);
    EVP_MD_CTX_free(ctx);
    
    std::stringstream ss;
    for(int i = 0; i < resultLen; i++) {
        ss << std::hex << std::setw(2) << std::setfill('0') << static_cast<int>(result[i]);
    }
    return ss.str();
}