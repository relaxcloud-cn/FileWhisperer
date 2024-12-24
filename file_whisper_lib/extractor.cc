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
            Node *t_node = new whisper_data_type::Node{.id = 0, .content = whisper_data_type::Data{.type = "URL", .content = encode_binary(item)}};
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
        using namespace bit7z;
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

        std::vector<std::string> passwords = node->passwords;
        bool extracted = false;
        std::map<std::string, std::vector<uint8_t>> files;

        if (passwords.empty())
        {
            try
            {
                files = extract_files_from_data(data, "");
                extracted = true;
            }
            catch (...)
            {
                throw;
            }
        }

        // 这里只能使用 find("Wrong password") 的方法来判断密码错误, bit7z 封装到标准错误里了。
        if (!extracted)
        {
            for (const auto &password : passwords)
            {
                try
                {
                    files = extract_files_from_data(data, password);
                    extracted = true;
                    node->meta.map_string["correct_password"] = password;
                    break;
                }
                catch (const bit7z::BitException &e)
                {
                    std::string error_msg = e.what();
                    if (error_msg.find("Wrong password") != std::string::npos)
                    {
                        std::cerr << "Password error: " << error_msg << std::endl;
                        continue;
                    }
                    throw;
                }
                catch (const std::runtime_error &e)
                {
                    std::string error_msg = e.what();
                    if (error_msg.find("Wrong password") != std::string::npos)
                    {
                        std::cerr << "Password error: " << error_msg << std::endl;
                        continue;
                    }
                    throw;
                }
                catch (const std::exception &ex)
                {
                    std::string error_msg = ex.what();
                    if (error_msg.find("Wrong password") != std::string::npos)
                    {
                        std::cerr << "Password error: " << error_msg << std::endl;
                        continue;
                    }
                    std::cerr << "Standard exception: " << error_msg << std::endl;
                    throw;
                }
                catch (...)
                {
                    std::cerr << "Unknown error occurred!" << std::endl;
                    throw;
                }
            }
        }

        if (!extracted)
        {
            throw std::runtime_error("All passwords failed");
        }

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
        catch (...)
        {
            throw; // Re-throw exception
        }

        return result_map;
    }

}

namespace extractor
{
    std::vector<Node *> extract_qrcode(Node *node)
    {
        std::vector<Node *> nodes;
        if (std::holds_alternative<File>(node->content))
        {
            File &file = std::get<File>(node->content);
            std::vector<uint8_t> &data = file.content;
            auto url = decodeQRCode(data);
            Node *t_node = new whisper_data_type::Node{.id = 0, .content = whisper_data_type::Data{.type = "QRCODE", .content = encode_binary(url)}};
            t_node->prev = node;
            nodes.push_back(t_node);
        }
        else if (std::holds_alternative<Data>(node->content))
        {
            spdlog::debug("extract_compressed_file enter Data type");
            return nodes;
        }

        return nodes;
    }

    std::string decodeQRCode(const std::vector<uint8_t> &file)
    {
        try
        {
            cv::Mat image = cv::imdecode(file, cv::IMREAD_COLOR);
            if (image.empty())
            {
                return "";
            }

            cv::QRCodeDetector qrDecoder;

            std::vector<cv::Point> points;

            std::string result = qrDecoder.detectAndDecode(image, points);

            return result;
        }
        catch (const std::exception &e)
        {
            return "";
        }
    }
}

namespace extractor
{
    std::vector<Node *> extract_html(Node *node)
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

        auto html_text = stripHtml(text);
        Node *t_node = new whisper_data_type::Node{.id = 0, .content = whisper_data_type::Data{.type = "TEXT", .content = encode_binary(html_text)}};
        t_node->prev = node;
        nodes.push_back(t_node);

        return nodes;
    }

    std::string extractHtmlText(GumboNode *node)
    {
        if (node->type == GUMBO_NODE_TEXT)
        {
            return std::string(node->v.text.text);
        }
        if (node->type == GUMBO_NODE_ELEMENT)
        {
            std::string contents;
            GumboVector *children = &node->v.element.children;
            for (unsigned int i = 0; i < children->length; ++i)
            {
                std::string text = extractHtmlText((GumboNode *)children->data[i]);
                if (contents.empty())
                {
                    contents = text;
                }
                else if (!text.empty())
                {
                    contents += " " + text;
                }
            }
            return contents;
        }
        return "";
    }

    std::string stripHtml(const std::string &html)
    {
        GumboOutput *output = gumbo_parse(html.c_str());
        std::string text = extractHtmlText(output->root);
        gumbo_destroy_output(&kGumboDefaultOptions, output);
        return text;
    }

}

namespace extractor
{
    std::vector<Node *> extract_ocr(Node *node)
    {
        std::vector<Node *> nodes;
        if (std::holds_alternative<File>(node->content))
        {
            File &file = std::get<File>(node->content);
            std::vector<uint8_t> &data = file.content;
            OCRHelper ocr;
            std::string result = ocr.recognize_image(data);
            Node *t_node = new whisper_data_type::Node{.id = 0, .content = whisper_data_type::Data{.type = "OCR", .content = encode_binary(result)}};
            t_node->prev = node;
            nodes.push_back(t_node);
        }
        else if (std::holds_alternative<Data>(node->content))
        {
            spdlog::debug("extract_compressed_file enter Data type");
            return nodes;
        }

        return nodes;
    }

    OCRHelper::OCRHelper()
    {
        ocr_ = new tesseract::TessBaseAPI();

        if (ocr_->Init(nullptr, "chi_tra+eng") != 0)
        {
            delete ocr_;
            throw std::runtime_error("Could not initialize tesseract. Please ensure TESSDATA_PREFIX environment variable is set correctly.");
        }
    }

    OCRHelper::~OCRHelper()
    {
        if (ocr_)
        {
            ocr_->End();
            delete ocr_;
        }
    }

    std::string OCRHelper::recognize_image(const std::vector<uint8_t> &image_data)
    {
        if (image_data.empty())
        {
            throw std::runtime_error("Image data is empty");
        }

        // 从内存数据创建Pix对象
        Pix *image = pixReadMemPng(
            image_data.data(),
            image_data.size());

        if (!image)
        {
            throw std::runtime_error("Failed to read image data");
        }

        ocr_->SetImage(image);
        char *outText = ocr_->GetUTF8Text();
        std::string result(outText);

        delete[] outText;
        pixDestroy(&image);

        return result;
    }
}
