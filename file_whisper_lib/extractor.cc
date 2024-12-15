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

namespace extractor
{
    std::vector<Node *> extract_compressed_file(Node *node)
    {
        std::vector<uint8_t> data;
        std::vector<Node *> nodes;
        if (std::holds_alternative<File>(node->content))
        {
            File &file = std::get<File>(node->content);
            data = file.content;
        }
        else if (std::holds_alternative<Data>(node->content))
        {
            spdlog::debug("extract_compressed_file enter Data type");
            return nodes;
        }

        auto files = extract_files_from_data(data);

        for (const auto &pair : files)
        {
            const std::string &key = pair.first;
            const std::vector<uint8_t> &value = pair.second;

            Node *t_node = new Node{.content = File{}};
            File &file = std::get<File>(t_node->content);
            file.path = key;
            file.name = key;
            file.content = std::move(value);

            t_node->prev = node;
            nodes.push_back(t_node);
        }

        return nodes;
    }

    std::map<std::string, std::vector<uint8_t>> extract_files_from_data(const std::vector<uint8_t> file, std::string password)
    {
        std::locale::global(std::locale("en_US.UTF-8"));
        std::map<std::string, std::vector<uint8_t>> result_map;
        using namespace bit7z;
        try
        {
            const char *path = std::getenv("LIB_PATH_7Z");
            if (path == NULL)
            {
                path = "/usr/local/share/7z/7z.so";
            }
            Bit7zLibrary lib{path};
            BitExtractor<std::vector<uint8_t>> extractor{lib, BitFormat::Auto};
            if (!password.empty())
            {
                extractor.setPassword(password);
            }
            extractor.extract(file, result_map);
        }
        catch (const bit7z::BitException &ex)
        {
            std::error_code ec = ex.code();
            switch (static_cast<BitError>(ec.value()))
            {
            case BitError::Fail:
                std::cerr << "Operation failed" << std::endl;
                break;
            case BitError::FilterNotSpecified:
                std::cerr << "Filter not specified" << std::endl;
                break;
            case BitError::FormatFeatureNotSupported:
                std::cerr << "Format feature not supported" << std::endl;
                break;
            case BitError::IndicesNotSpecified:
                std::cerr << "Indices not specified" << std::endl;
                break;
            case BitError::InvalidArchivePath:
                std::cerr << "Invalid archive path" << std::endl;
                break;
            case BitError::InvalidOutputBufferSize:
                std::cerr << "Invalid output buffer size" << std::endl;
                break;
            case BitError::InvalidCompressionMethod:
                std::cerr << "Invalid compression method" << std::endl;
                break;
            case BitError::InvalidDictionarySize:
                std::cerr << "Invalid dictionary size" << std::endl;
                break;
            case BitError::InvalidIndex:
                std::cerr << "Invalid index" << std::endl;
                break;
            case BitError::InvalidWordSize:
                std::cerr << "Invalid word size" << std::endl;
                break;
            case BitError::ItemIsAFolder:
                std::cerr << "Item is a folder" << std::endl;
                break;
            case BitError::ItemMarkedAsDeleted:
                std::cerr << "Item marked as deleted" << std::endl;
                break;
            case BitError::NoMatchingItems:
                std::cerr << "No matching items found" << std::endl;
                break;
            case BitError::NoMatchingSignature:
                std::cerr << "No matching signature" << std::endl;
                break;
            case BitError::NonEmptyOutputBuffer:
                std::cerr << "Non-empty output buffer" << std::endl;
                break;
            case BitError::NullOutputBuffer:
                std::cerr << "Null output buffer" << std::endl;
                break;
            case BitError::RequestedWrongVariantType:
                std::cerr << "Requested wrong variant type" << std::endl;
                break;
            case BitError::UnsupportedOperation:
                std::cerr << "Unsupported operation" << std::endl;
                break;
            case BitError::UnsupportedVariantType:
                std::cerr << "Unsupported variant type" << std::endl;
                break;
            case BitError::WrongUpdateMode:
                std::cerr << "Wrong update mode" << std::endl;
                break;
            case BitError::InvalidZipPassword:
                std::cerr << "Invalid ZIP password" << std::endl;
                break;
            default:
                std::cerr << "Unknown bit7z error: " << ex.what() << std::endl;
            }
            throw; // Re-throw exception
        }
        catch (const std::exception &ex)
        {
            std::cerr << "Standard exception: " << ex.what() << std::endl;
            throw; // Re-throw exception
        }
        catch (...)
        {
            std::cerr << "Unknown error occurred!" << std::endl;
            throw; // Re-throw exception
        }

        return result_map;
    }
}