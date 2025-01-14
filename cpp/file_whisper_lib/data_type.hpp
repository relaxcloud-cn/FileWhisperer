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
namespace whisper_data_type {

    struct File {
        std::string path;
        std::string name;
        int64_t size;
        std::string mime_type;
        std::string extension;
        std::string md5;
        std::string sha256;
        std::string sha1;
        std::vector<uint8_t> content;
    };

    struct Data {
        std::string type;
        std::vector<uint8_t> content;
    };

    struct Meta {
        std::map<std::string, std::string> map_string;
        std::map<std::string, int64_t> map_number;
        std::map<std::string, bool> map_bool;
    };

    struct Node {
        int64_t id;
        std::string uuid;
        std::weak_ptr<Node> prev;
        std::vector<std::shared_ptr<Node>> children;
        std::variant<File, Data> content;
        std::vector<std::string> passwords;
        Types type;
        Meta meta;

        void add_child(std::shared_ptr<Node> child) {
            children.push_back(child);
        }

        void set_type(std::string key) {
            if (Types__1.count(key)) {
                this->type = Types__1.at(key);
            }
            else {
                this->type = Types::OTHER;
            }
        }
    };

    struct Tree {
        std::shared_ptr<Node> root;
        Tree() = default;
        
        void digest(std::shared_ptr<Node> node);
    };

    void meta_detect_encoding(Meta& meta, const std::vector<uint8_t>& data);

} // namespace whisper