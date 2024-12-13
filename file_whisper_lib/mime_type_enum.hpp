#include <optional>
#include <string>
#include <map>

enum MimeType {
    TEXT_PLAIN,
    OTHER
};


const std::map<std::string, MimeType> MimeTypeMap__1 = {
    {"text/plain", TEXT_PLAIN}
};