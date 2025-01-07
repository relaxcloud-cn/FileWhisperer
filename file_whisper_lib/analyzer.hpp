#include <bit7z/bitfileextractor.hpp>
#include <bit7z/bit7zlibrary.hpp>
#include <bit7z/bitexception.hpp>
#include <bit7z/bitarchivereader.hpp>
#include <stdexcept>
#include "data_type.hpp"
#include "types.hpp"


namespace analyzer
{
    using namespace whisper_data_type;

    void analyze_compressed_file(std::shared_ptr<Node> node);
} // namespace analyzer
