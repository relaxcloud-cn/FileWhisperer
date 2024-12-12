#include "data_type.hpp"

void whisper_data_type::Tree::digest(Node *node)
{
    if (this->root == nullptr)
    {
        this->root = node;
    }
    boost::uuids::random_generator generator;
    boost::uuids::uuid uuid = generator();
    node->id = boost::uuids::to_string(uuid);
    if (std::holds_alternative<File>(node->content))
    {
        whisper_data_type::File &file = std::get<File>(node->content);
        file.size = file.content.size();
        file.mime_type = get_buffer_mime_type(file.content.data(), file.size);
        file.md5 = calculate_md5(file.content.data(), file.size);
        file.sha256 = calculate_sha256(file.content.data(), file.size);
    }
    else if (std::holds_alternative<whisper_data_type::Data>(root->content))
    {
    }
    return;
}