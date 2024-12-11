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

std::string get_buffer_mime_type(const uint8_t* data, size_t length) {
    magic_t magic;
    const char* file_type;
    std::string mime_type;

    // Initialize magic library
    magic = magic_open(MAGIC_MIME_TYPE);
    if (magic == NULL) {
        throw std::runtime_error("Unable to initialize magic library");
    }

    // Load default magic database
    if (magic_load(magic, "/usr/local/share/misc/magic.mgc") != 0) {
        std::string error = magic_error(magic);
        magic_close(magic);
        throw std::runtime_error("Cannot load magic database: " + error);
    }

    // Get file type
    file_type = magic_buffer(magic, data, length);
    if (file_type == NULL) {
        std::string error = magic_error(magic);
        magic_close(magic);
        throw std::runtime_error("Error getting file type: " + error);
    }

    mime_type = file_type;

    // Clean up
    magic_close(magic);
    return mime_type;
}

std::string get_file_mime_type(const char * file) {
    magic_t magic;
    const char* file_type;
    std::string mime_type;

    // Initialize magic library
    magic = magic_open(MAGIC_MIME_TYPE);
    if (magic == NULL) {
        throw std::runtime_error("Unable to initialize magic library");
    }

    // Load default magic database
    if (magic_load(magic, "/usr/local/share/misc/magic.mgc") != 0) {
        std::string error = magic_error(magic);
        magic_close(magic);
        throw std::runtime_error("Cannot load magic database: " + error);
    }

    // Get file type
    file_type = magic_file(magic, file);
    if (file_type == NULL) {
        std::string error = magic_error(magic);
        magic_close(magic);
        throw std::runtime_error("Error getting file type: " + error);
    }

    mime_type = file_type;

    // Clean up
    magic_close(magic);
    return mime_type;
}
