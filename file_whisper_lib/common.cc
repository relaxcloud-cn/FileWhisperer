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
