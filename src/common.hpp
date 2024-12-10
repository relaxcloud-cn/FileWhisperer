#include <openssl/evp.h>
#include <iomanip>
#include <sstream>
#include <string>

std::string calculate_md5(const uint8_t* data, size_t length);

std::string calculate_sha256(const uint8_t* data, size_t length);
