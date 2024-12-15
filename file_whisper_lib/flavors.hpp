#include <map>
#include <vector>
#include <functional>
#include "types.hpp"
#include "data_type.hpp"
#include "extractor.hpp"

namespace flavors
{
    using namespace whisper_data_type;

    using ExtractFunctionModern = std::function<std::vector<Node *>(Node *)>;
    std::map<Types, std::vector<ExtractFunctionModern>> flavor_extractors = {
        {Types::TEXT_PLAIN, {extractor::extract_urls}},
        {Types::COMPRESSED_FILE, {extractor::extract_compressed_file}}};

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
                auto extracted = extractor(node);
                nodes.insert(nodes.end(), extracted.begin(), extracted.end());
            }
        }

        return nodes;
    }

}
