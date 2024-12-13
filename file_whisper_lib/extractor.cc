#include "extractor.hpp"

namespace extractor
{

    using namespace whisper_data_type;

    std::vector<Node *> extract_urls(Node *node)
    {
        std::vector<Node *> nodes;
        std::string text;
        if (std::holds_alternative<File>(node->content))
        {
            File &file = std::get<File>(node->content);
            spdlog::debug("Node[{}] file {}", node->id, file.mime_type);
            text = decode_binary(file.content);
        }
        else if (std::holds_alternative<Data>(node->content))
        {
            Data &data = std::get<Data>(node->content);
            spdlog::debug("Node[{}] data {}", node->id, data.type);
            text = decode_binary(data.content);
        }

        auto urls = extract_urls_from_text(text);

        spdlog::debug("Node[{}] Number of urls: {}", node->id, urls.size());

        for (auto &item : urls)
        {
            Node *t_node = new whisper_data_type::Node{.content = whisper_data_type::Data{
                                                         .type = "URL",
                                                         .content = encode_binary(item)}};
            t_node->prev = node;
            nodes.push_back(t_node);
        }

        return nodes;
    }

    std::vector<std::string> extract_urls_from_text(const std::string &text)
    {
        std::vector<std::string> urls;
        static const re2::RE2 url_pattern("(https?://[^\\s\"<>{}]+)");

        re2::StringPiece input(text);
        std::string url;

        while (RE2::FindAndConsume(&input, url_pattern, &url))
        {
            urls.push_back(url);
        }

        return urls;
    }

}