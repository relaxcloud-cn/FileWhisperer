#include "extractor.hpp"

namespace extractor
{

    using namespace whisper_data_type;

    std::vector<std::shared_ptr<Node>> extract_urls(std::shared_ptr<Node> node)
    {
        std::vector<std::shared_ptr<Node>> nodes;
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
            auto t_node = std::make_shared<Node>();
            t_node->id = 0;
            t_node->content = Data{.type = "URL", .content = encode_binary(item)};
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

    std::vector<std::shared_ptr<Node>> extract_compressed_file(std::shared_ptr<Node> node)
    {
        using namespace bit7z;
        std::vector<uint8_t> data;
        std::vector<std::shared_ptr<Node>> nodes;

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

        if (!extracted)
        {
            // 这里只能使用 find("Wrong password") 的方法来判断密码错误, bit7z 封装到标准错误里了。
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

            auto t_node = std::make_shared<Node>();
            t_node->content = File{};
            File &file = std::get<File>(t_node->content);
            file.path = key;
            file.name = key;
            file.content = value;

            t_node->prev = node;
            nodes.push_back(t_node);
        }

        return nodes;
    }

    std::map<std::string, std::vector<uint8_t>> extract_files_from_data(const std::vector<uint8_t> file, std::string password)
    {
        using namespace bit7z;
        std::locale::global(std::locale("en_US.UTF-8"));
        std::map<std::string, std::vector<uint8_t>> result_map;

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
            throw;
        }

        return result_map;
    }

    std::vector<std::shared_ptr<Node>> extract_qrcode(std::shared_ptr<Node> node)
    {
        std::vector<std::shared_ptr<Node>> nodes;

        if (std::holds_alternative<File>(node->content))
        {
            File &file = std::get<File>(node->content);
            std::vector<uint8_t> &data = file.content;
            auto url = decodeQRCodeZXing(data);

            if (!url.empty())
            {
                auto t_node = std::make_shared<Node>();
                t_node->id = 0;
                t_node->content = Data{.type = "QRCODE", .content = encode_binary(url)};
                t_node->prev = node;
                nodes.push_back(t_node);
            }
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

    std::string decodeQRCodeZXing(const std::vector<uint8_t> &file)
    {
        try
        {
            cv::Mat image = cv::imdecode(file, cv::IMREAD_COLOR);
            if (image.empty())
            {
                return "";
            }

            cv::Mat grey;
            cv::cvtColor(image, grey, cv::COLOR_BGR2GRAY);

            ZXing::ImageView imageView(grey.data, grey.cols, grey.rows, ZXing::ImageFormat::Lum);

            ZXing::ReaderOptions options;
            options.setTryHarder(true);
            options.setTryRotate(true);
            options.setFormats(ZXing::BarcodeFormat::QRCode);

            auto result = ZXing::ReadBarcode(imageView, options);

            if (result.isValid())
            {
                return result.text();
            }

            return "";
        }
        catch (const std::exception &e)
        {
            spdlog::error("QR code decode error: {}", e.what());
            return "";
        }
    }

    std::vector<std::shared_ptr<Node>> extract_html(std::shared_ptr<Node> node)
    {
        std::vector<std::shared_ptr<Node>> nodes;
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
        auto t_node = std::make_shared<Node>();
        t_node->id = 0;
        t_node->content = Data{.type = "TEXT", .content = encode_binary(html_text)};
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
    std::string recognize_image(const std::vector<uint8_t> &image_data)
    {
        char *outText;
        std::string result;

        tesseract::TessBaseAPI *api = new tesseract::TessBaseAPI();

        // Initialize tesseract-ocr with Chinese Traditional and English
        if (api->Init(NULL, "chi_tra+eng"))
        {
            throw std::runtime_error("Could not initialize tesseract.");
        }

        // Convert image_data to Pix using Leptonica
        Pix *image = pixReadMem(
            image_data.data(),
            image_data.size()
        );

        if (!image)
        {
            api->End();
            delete api;
            throw std::runtime_error("Failed to load image data.");
        }

        api->SetImage(image);

        // Get OCR result
        outText = api->GetUTF8Text();
        if (outText)
        {
            result = std::string(outText);
        }

        // Cleanup
        api->End();
        delete api;
        delete[] outText;
        pixDestroy(&image);

        return result;
    }

    std::vector<std::shared_ptr<Node>> extract_ocr(std::shared_ptr<Node> node)
    {
        std::vector<std::shared_ptr<Node>> nodes;

        if (std::holds_alternative<File>(node->content))
        {
            File &file = std::get<File>(node->content);
            std::vector<uint8_t> &data = file.content;

            try
            {
                std::string result = recognize_image(data);

                auto t_node = std::make_shared<Node>();
                t_node->id = 0;
                t_node->content = Data{.type = "OCR", .content = encode_binary(result)};
                t_node->prev = node;
                nodes.push_back(t_node);
            }
            catch (const std::exception &e)
            {
                spdlog::error("OCR processing failed: {}", e.what());
            }
        }
        else if (std::holds_alternative<Data>(node->content))
        {
            spdlog::debug("extract_compressed_file enter Data type");
        }

        return nodes;
    }
}

namespace extractor
{
    std::vector<std::shared_ptr<Node>> extract_py(std::shared_ptr<Node> node)
    {
        std::vector<std::shared_ptr<Node>> nodes;
        const char *pythonPath = std::getenv("FILE_WHISPERER_PYTHON_PATH");
        if (!pythonPath)
        {
            std::cout << "Environment variable FILE_WHISPERER_PYTHON_PATH is not set!" << std::endl;
        }

        Py_Initialize();

        if (!Py_IsInitialized())
        {
            std::cout << "Python initialization failed!" << std::endl;
        }

        PyRun_SimpleString("import sys");
        std::string pythonCmd = "sys.path.append(\"" + std::string(pythonPath) + "\")";
        PyRun_SimpleString(pythonCmd.c_str());

        PyObject *pModule = PyImport_ImportModule("extract_office");
        if (!pModule)
        {
            PyErr_Print();
            std::cout << "Can't find Python file in path: " << pythonPath << std::endl;
            Py_Finalize();
        }

        PyObject *pAddFunc = PyObject_GetAttrString(pModule, "add");
        PyObject *pGreetFunc = PyObject_GetAttrString(pModule, "greet");

        PyObject *pArgs = PyTuple_Pack(2, PyLong_FromLong(3), PyLong_FromLong(4));
        PyObject *pResult = PyObject_CallObject(pAddFunc, pArgs);

        int result = PyLong_AsLong(pResult);
        std::cout << "3 + 4 = " << result << std::endl;

        pArgs = PyTuple_Pack(1, PyUnicode_FromString("C++"));
        pResult = PyObject_CallObject(pGreetFunc, pArgs);

        const char *greet_msg = PyUnicode_AsUTF8(pResult);
        std::cout << greet_msg << std::endl;

        Py_DECREF(pModule);
        Py_DECREF(pAddFunc);
        Py_DECREF(pGreetFunc);
        Py_DECREF(pArgs);
        Py_DECREF(pResult);

        Py_Finalize();
        return nodes;
    }
}