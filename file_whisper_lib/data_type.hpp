#include <string>
#include <vector>
#include <map>
#include <memory>
#include <variant>
#include <optional>
#include <boost/uuid/uuid.hpp>
#include <boost/uuid/uuid_generators.hpp>
#include <boost/uuid/uuid_io.hpp>
#include <spdlog/spdlog.h>
#include "common.hpp"
#include "types.hpp"

#pragma once
namespace whisper_data_type
{

    struct File
    {
        std::string path;
        std::string name;
        int64_t size;
        std::string mime_type;
        std::string extension;
        std::string md5;
        std::string sha256;
        std::vector<uint8_t> content;
    };

    struct Data
    {
        std::string type;
        std::vector<uint8_t> content;
    };

    struct Meta
    {
        std::map<std::string, std::string> map_string;
        std::map<std::string, int64_t> map_number;
        std::map<std::string, bool> map_bool;
    };

    struct Node
    {
        std::string id;
        // std::string parent_id;
        Node *prev;
        // std::vector<std::string> children;
        std::vector<Node *> children;
        std::variant<File, Data> content;
        std::vector<std::string> passwords;
        Types type;
        Meta meta;

        void add_child(Node *child)
        {
            children.push_back(child);
        }

        void set_type(std::string key)
        {
            if (Types__1.count(key))
            {
                this->type = Types__1.at(key);
            }
            else
            {
                this->type = Types::OTHER;
            }
        }
    };

    struct Tree
    {
        Node *root;
        Tree() = default;
        ~Tree()
        {
            deleteNode(root);
        }

    public:
        void digest(Node *node);
        void deleteNode(Node *node)
        {
            if (node == nullptr)
                return;

            for (Node *child : node->children)
            {
                deleteNode(child);
            }

            delete node;
        }
    };

    void meta_detect_encoding(Meta &meta, const std::vector<uint8_t> &data);
    std::vector<Node *> file_extract(Node *node);

} // namespace whisper
