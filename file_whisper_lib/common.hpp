#include <openssl/evp.h>
#include <iomanip>
#include <sstream>
#include <string>
#include <magic.h>

std::string calculate_md5(const uint8_t* data, size_t length);
std::string calculate_sha256(const uint8_t* data, size_t length);
std::string get_file_mime_type(const char * file);
std::string get_buffer_mime_type(const uint8_t* data, size_t length);
