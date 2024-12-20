#include <map>
#include <vector>
#include <functional>
#include <chrono>
#include "types.hpp"
#include "data_type.hpp"
#include "extractor.hpp"

namespace flavors
{
    using namespace whisper_data_type;

    using ExtractFunctionModern = std::function<std::vector<Node *>(Node *)>;
    
    struct ExtractorInfo {
        std::string name;
        ExtractFunctionModern func;
    };

    const ExtractorInfo url_extractor{"url_extractor", extractor::extract_urls};
    const ExtractorInfo qrcode_extractor{"qrcode_extractor", extractor::extract_qrcode};
    const ExtractorInfo ocr_extractor{"ocr_extractor", extractor::extract_ocr};
    const ExtractorInfo html_extractor{"html_extractor", extractor::extract_html};
    const ExtractorInfo compressed_file_extractor{"compressed_file_extractor", extractor::extract_compressed_file};

    std::map<Types, std::vector<ExtractorInfo>> flavor_extractors = {
        {Types::TEXT_PLAIN, {url_extractor}},
        {Types::IMAGE, {qrcode_extractor, ocr_extractor}},
        {Types::TEXT_HTML, {html_extractor}},
        {Types::COMPRESSED_FILE, {compressed_file_extractor}}
    };

    std::vector<Node *> extract(Node *node)
    {
        std::vector<Node *> nodes;

        if (!node)
        {
            return nodes;
        }

        auto it = flavor_extractors.find(node->type);
        if (it != flavor_extractors.end())
        {
            for (const auto &extractor : it->second)
            {
                auto start = std::chrono::high_resolution_clock::now();
                auto extracted = extractor.func(node);
                auto end = std::chrono::high_resolution_clock::now();
                
                auto duration = std::chrono::duration_cast<std::chrono::microseconds>(end - start).count();
                std::string key = "microsecond_" + extractor.name;
                node->meta.map_number[key] = duration;
                
                nodes.insert(nodes.end(), extracted.begin(), extracted.end());
            }
        }

        return nodes;
    }
}