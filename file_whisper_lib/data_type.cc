#include "data_type.hpp"
#include "flavors.hpp"

void whisper_data_type::Tree::digest(std::shared_ptr<Node> node)
{
    std::vector<std::shared_ptr<Node>> extracted_nodes;
    if (this->root == nullptr)
    {
        this->root = node;
    }
    boost::uuids::random_generator generator;
    boost::uuids::uuid uuid = generator();
    node->uuid = boost::uuids::to_string(uuid);
    // 根结点可能会由调用方提供 id
    if (node->id == 0)
    {
        // node->id = boost::uuids::to_string(uuid);
        SnowFlake *snowflake = SnowFlake::getInstance(1, 1);
        int64_t id = snowflake->nextId();
        node->id = id;
    }
    Meta meta{};
    if (std::holds_alternative<File>(node->content))
    {
        File &file = std::get<File>(node->content);
        file.size = file.content.size();
        file.mime_type = get_buffer_mime_type(file.content.data(), file.size);
        file.md5 = calculate_md5(file.content.data(), file.size);
        file.sha256 = calculate_sha256(file.content.data(), file.size);
        file.sha1 = calculate_sha1(file.content.data(), file.size);
        node->set_type(file.mime_type);
        meta_detect_encoding(meta, file.content);
    }
    else if (std::holds_alternative<Data>(node->content))
    {
        Data &data = std::get<Data>(node->content);
        meta_detect_encoding(meta, data.content);
        node->set_type(data.type);
    }
    node->meta = meta;

    auto nodes = flavors::extract(node);
    extracted_nodes.insert(extracted_nodes.end(), nodes.begin(), nodes.end());

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
