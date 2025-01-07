#include "analyzer.hpp"

namespace analyzer
{
    using namespace whisper_data_type;

    void analyze_compressed_file(std::shared_ptr<Node> node)
    {
        std::vector<uint8_t> data;
        if (std::holds_alternative<File>(node->content))
        {
            File &file = std::get<File>(node->content);
            data = file.content;
        }
        else if (std::holds_alternative<Data>(node->content))
        {
            spdlog::debug("extract_compressed_file enter Data type");
        }

        std::locale::global(std::locale("en_US.UTF-8"));
        try
        { // bit7z classes can throw BitException objects
            using namespace bit7z;

            const char *path = std::getenv("LIB_PATH_7Z");
            if (path == NULL)
            {
                path = "/usr/local/share/7z/7z.so";
            }
            Bit7zLibrary lib{path};

            BitArchiveReader arc{lib, data, BitFormat::Auto};

            node->meta.map_number["items_count"] = arc.itemsCount();
            node->meta.map_number["folders_count"] = arc.foldersCount();
            node->meta.map_number["files_count"] = arc.filesCount();
            node->meta.map_number["size"] = arc.size();
            node->meta.map_number["pack_size"] = arc.packSize();
            node->meta.map_bool["is_encrypted"] = arc.isEncrypted();
            node->meta.map_number["volumes_count"] = arc.volumesCount();
            node->meta.map_bool["is_multi_volume"] = arc.isMultiVolume();
        }
        catch (const bit7z::BitException &ex)
        { /* Do something with ex.what()...*/
            spdlog::error(ex.what());
            // std::cerr << "Unknown bit7z error: " << ex.what() << std::endl;
            throw;
        }
    }

}
