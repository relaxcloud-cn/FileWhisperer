#include "common.hpp"

std::string calculate_md5(const uint8_t *data, size_t length)
{
    unsigned char result[EVP_MAX_MD_SIZE];
    unsigned int resultLen;

    EVP_MD_CTX *ctx = EVP_MD_CTX_new();
    EVP_DigestInit_ex(ctx, EVP_md5(), NULL);
    EVP_DigestUpdate(ctx, data, length);
    EVP_DigestFinal_ex(ctx, result, &resultLen);
    EVP_MD_CTX_free(ctx);

    std::stringstream ss;
    for (int i = 0; i < resultLen; i++)
    {
        ss << std::hex << std::setw(2) << std::setfill('0') << static_cast<int>(result[i]);
    }
    return ss.str();
}

std::string calculate_sha256(const uint8_t *data, size_t length)
{
    unsigned char result[EVP_MAX_MD_SIZE];
    unsigned int resultLen;

    EVP_MD_CTX *ctx = EVP_MD_CTX_new();
    EVP_DigestInit_ex(ctx, EVP_sha256(), NULL);
    EVP_DigestUpdate(ctx, data, length);
    EVP_DigestFinal_ex(ctx, result, &resultLen);
    EVP_MD_CTX_free(ctx);

    std::stringstream ss;
    for (int i = 0; i < resultLen; i++)
    {
        ss << std::hex << std::setw(2) << std::setfill('0') << static_cast<int>(result[i]);
    }
    return ss.str();
}

class MagicWrapper
{
public:
    MagicWrapper()
    {
        magic = magic_open(MAGIC_MIME_TYPE);
        if (magic == NULL)
        {
            throw std::runtime_error("Unable to initialize magic library");
        }

        const char *magic_path = std::getenv("MAGIC_MGC_PATH");
        if (magic_path == NULL)
        {
            magic_path = "/usr/local/share/misc/magic.mgc";
        }

        if (magic_load(magic, magic_path) != 0)
        {
            std::string error = magic_error(magic);
            magic_close(magic);
            throw std::runtime_error("Cannot load magic database: " + error);
        }
    }

    ~MagicWrapper()
    {
        if (magic)
        {
            magic_close(magic);
        }
    }

    std::string get_mime_type(const uint8_t *data, size_t length)
    {
        const char *file_type = magic_buffer(magic, data, length);
        if (file_type == NULL)
        {
            throw std::runtime_error("Error getting file type: " + std::string(magic_error(magic)));
        }
        return file_type;
    }

    std::string get_mime_type(const char *file)
    {
        const char *file_type = magic_file(magic, file);
        if (file_type == NULL)
        {
            throw std::runtime_error("Error getting file type: " + std::string(magic_error(magic)));
        }
        return file_type;
    }

private:
    magic_t magic;
};

std::string get_buffer_mime_type(const uint8_t *data, size_t length)
{
    MagicWrapper magic;
    return magic.get_mime_type(data, length);
}

std::string get_file_mime_type(const char *file)
{
    MagicWrapper magic;
    return magic.get_mime_type(file);
}


EncodingResult detect_encoding(const std::vector<uint8_t>& data) {
    UErrorCode status = U_ZERO_ERROR;
    UCharsetDetector* csd = ucsdet_open(&status);
    if (U_FAILURE(status)) {
        return EncodingResult();
    }

    ucsdet_setText(csd, 
                   reinterpret_cast<const char*>(data.data()),
                   static_cast<int32_t>(data.size()),
                   &status);
    
    const UCharsetMatch* ucm = ucsdet_detect(csd, &status);
    if (!ucm || U_FAILURE(status)) {
        ucsdet_close(csd);
        return EncodingResult();
    }
    
    const char* name = ucsdet_getName(ucm, &status);
    int32_t confidence = ucsdet_getConfidence(ucm, &status);
    
    EncodingResult result(name, confidence);
    
    ucsdet_close(csd);
    return result;
}

std::vector<EncodingResult> detect_encodings(const std::vector<uint8_t>& data, int32_t max_matches) {
    std::vector<EncodingResult> results;
    UErrorCode status = U_ZERO_ERROR;
    UCharsetDetector* csd = ucsdet_open(&status);
    if (U_FAILURE(status)) {
        return results;
    }

    ucsdet_setText(csd, 
                   reinterpret_cast<const char*>(data.data()),
                   static_cast<int32_t>(data.size()),
                   &status);
    
    int32_t found;
    const UCharsetMatch** matches = ucsdet_detectAll(csd, &found, &status);
    if (U_FAILURE(status) || !matches) {
        ucsdet_close(csd);
        return results;
    }
    
    int32_t count = std::min(max_matches, found);
    for (int32_t i = 0; i < count; ++i) {
        const char* name = ucsdet_getName(matches[i], &status);
        int32_t confidence = ucsdet_getConfidence(matches[i], &status);
        if (U_SUCCESS(status)) {
            results.emplace_back(name, confidence);
        }
    }
    
    ucsdet_close(csd);
    return results;
}

std::string decode_to_string(const std::vector<uint8_t>& data, const std::string& encoding) {
    UErrorCode status = U_ZERO_ERROR;
    
    UConverter* converter = ucnv_open(encoding.c_str(), &status);
    if (U_FAILURE(status) || !converter) {
        return "";
    }

    struct ConverterGuard {
        UConverter* conv;
        ~ConverterGuard() { if (conv) ucnv_close(conv); }
    } guard{converter};
    
    icu::UnicodeString ustr(reinterpret_cast<const char*>(data.data()), 
                           static_cast<int32_t>(data.size()), 
                           converter, 
                           status);
    
    if (U_FAILURE(status)) {
        return "";
    }
    
    std::string result;
    ustr.toUTF8String(result);
    
    return result;
}

std::string decode_binary(const std::vector<uint8_t>& data) {
    auto encoding_result = detect_encoding(data);
    if (encoding_result.encoding.empty() || encoding_result.confidence < 10) {
        return "";
    }
    
    return decode_to_string(data, encoding_result.encoding);
}

