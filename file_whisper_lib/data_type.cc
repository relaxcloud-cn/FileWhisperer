#include "data_type.hpp"

void whisper_data_type::Tree::digest(Node *node)
{
    std::vector<Node *> extracted_nodes;
    if (this->root == nullptr)
    {
        this->root = node;
    }
    boost::uuids::random_generator generator;
    boost::uuids::uuid uuid = generator();
    node->id = boost::uuids::to_string(uuid);
    Meta meta{};
    if (std::holds_alternative<File>(node->content))
    {
        File &file = std::get<File>(node->content);
        file.size = file.content.size();
        file.mime_type = get_buffer_mime_type(file.content.data(), file.size);
        file.md5 = calculate_md5(file.content.data(), file.size);
        file.sha256 = calculate_sha256(file.content.data(), file.size);
        meta_detect_encoding(meta, file.content);

        auto nodes = file_extract(node);

        extracted_nodes.insert(extracted_nodes.end(), nodes.begin(), nodes.end());
    }
    else if (std::holds_alternative<Data>(root->content))
    {
        Data &data = std::get<Data>(node->content);
        meta_detect_encoding(meta, data.content);
    }
    node->meta = meta;
    node->children = extracted_nodes;

    for (auto &t_node : extracted_nodes)
    {
        this->digest(t_node);
    }
    return;
}

namespace whisper_data_type
{
    void meta_detect_encoding(Meta &meta, const std::vector<uint8_t> &data)
    {
        std::vector<EncodingResult> er = detect_encodings(data);
        if (!er.empty())
        {
            meta.map_string["encoding"] = er[0].encoding;
            meta.map_number["encoding_confidence"] = er[0].confidence;

            for (size_t i = 1; i < er.size(); i++)
            {
                std::string key = "encoding" + std::to_string(i + 1);
                std::string conf_key = "encoding_confidence" + std::to_string(i + 1);

                meta.map_string[key] = er[i].encoding;
                meta.map_number[conf_key] = er[i].confidence;
            }
        }
    }
}

namespace whisper_data_type
{
    std::vector<Node *> file_extract(Node *node)
    {
        spdlog::debug("Inter file_extract");
        std::vector<Node *> nodes;
        File &file = std::get<File>(node->content);
        if (file.mime_type == "text/plain")
        {
            auto urls = extract_urls(decode_binary(file.content));
            spdlog::debug("Number of urls: {}", urls.size());
            for (auto &item : urls)
            {
                Node *node = new whisper_data_type::Node{.content = whisper_data_type::Data{
                                                             .type = "URL",
                                                             .content = encode_binary(item)}};
                node->prev = node;
                nodes.push_back(node);
            }
        }
        else if (file.mime_type == "some")
        {
        }
        else
        {
        }

        return nodes;
    }
}