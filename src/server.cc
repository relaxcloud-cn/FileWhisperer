#include <CLI/CLI.hpp>
#include <grpcpp/grpcpp.h>
#include <iostream>
#include <string>
#include <mio/mmap.hpp>
#include "data_type.hpp"
#include "cpp/file_whisper.grpc.pb.h"
#include <queue>
#include <spdlog/spdlog.h>

void make_whisper_reply(whisper::WhisperReply *, whisper_data_type::Tree *);
void bfs(whisper::WhisperReply *, whisper_data_type::Node *);
void bsf_process_whisper_reply_node(whisper::WhisperReply *, whisper_data_type::Node *);
void RunServer(int);

int main(int argc, char **argv)
{
  CLI::App app{"FileWhisperer server"};

  int port = 50051;
  std::string log_level = "debug";

  app.add_option("-p,--port", port, "Port to listen on")
      ->check(CLI::Range(1, 65535));

  app.add_option("-l,--log-level", log_level, "Log level (trace, debug, info, warn, error, critical)")
      ->check(CLI::IsMember({"trace", "debug", "info", "warn", "error", "critical"}));

  try
  {
    app.parse(argc, argv);

    spdlog::set_pattern("[%Y-%m-%d %H:%M:%S.%e] [%^%l%$] [%t] %v");

    if (log_level == "trace")
      spdlog::set_level(spdlog::level::trace);
    else if (log_level == "debug")
      spdlog::set_level(spdlog::level::debug);
    else if (log_level == "info")
      spdlog::set_level(spdlog::level::info);
    else if (log_level == "warn")
      spdlog::set_level(spdlog::level::warn);
    else if (log_level == "error")
      spdlog::set_level(spdlog::level::err);
    else if (log_level == "critical")
      spdlog::set_level(spdlog::level::critical);
  }
  catch (const CLI::ParseError &e)
  {
    return app.exit(e);
  }

  RunServer(port);
  return 0;
}

class GreeterServiceImpl final : public whisper::Whisper::Service
{
  grpc::Status Whispering(grpc::ServerContext *context,
                          const whisper::WhisperRequest *request,
                          whisper::WhisperReply *reply) override
  {
    try
    {
      std::unique_ptr<whisper_data_type::Tree> tree = std::make_unique<whisper_data_type::Tree>();
      tree->root = nullptr;
      whisper_data_type::Node *node = new whisper_data_type::Node{.content = whisper_data_type::File{}};

      const uint8_t *data = nullptr;
      size_t data_size = 0;
      std::string file_path;

      std::unique_ptr<mio::mmap_source> mmap;

      if (request->has_file_path())
      {
        file_path = request->file_path();
        mmap = std::make_unique<mio::mmap_source>(file_path);
        data = reinterpret_cast<const uint8_t *>(mmap->data());
        data_size = mmap->size();
      }
      else if (request->has_file_content())
      {
        const std::string &content = request->file_content();
        data = reinterpret_cast<const uint8_t *>(content.data());
        data_size = content.size();
        file_path = "memory_file";
      }
      else
      {
        const std::string error_msg = "No file data provided";
        std::cerr << error_msg << std::endl;
        return grpc::Status(grpc::StatusCode::INVALID_ARGUMENT, error_msg);
      }

      std::vector<uint8_t> file_content(data, data + data_size);
      whisper_data_type::File &file = std::get<whisper_data_type::File>(node->content);
      file.path = file_path;
      file.content = std::move(file_content);
      tree->digest(node);
      make_whisper_reply(reply, tree.get());
      return grpc::Status::OK;
    }
    catch (const std::exception &e)
    {
      std::string error_msg = std::string("Error processing request: ") + e.what();
      std::cerr << error_msg << std::endl;
      return grpc::Status(grpc::StatusCode::INTERNAL, error_msg);
    }
  }
};

void make_whisper_reply(whisper::WhisperReply *reply, whisper_data_type::Tree *tree)
{
  bfs(reply, tree->root);
}

void bfs(whisper::WhisperReply *reply, whisper_data_type::Node *root)
{
  if (!root)
    return;

  std::queue<whisper_data_type::Node *> q;
  q.push(root);

  while (!q.empty())
  {
    whisper_data_type::Node *curr = q.front();
    q.pop();

    bsf_process_whisper_reply_node(reply, curr);

    for (whisper_data_type::Node *child : curr->children)
    {
      q.push(child);
    }
  }
}

void bsf_process_whisper_reply_node(whisper::WhisperReply *reply, whisper_data_type::Node *root)
{
  whisper::Node *node = reply->add_tree();
  node->set_id(root->id);
  if (root->prev)
  {
    node->set_parent_id(root->prev->id);
  }
  if (!root->children.empty())
  {
    for (const auto &child : root->children)
    {
      node->add_children(child->id);
    }
  }
  if (std::holds_alternative<whisper_data_type::File>(root->content))
  {
    whisper_data_type::File &root_file = std::get<whisper_data_type::File>(root->content);
    whisper::File *file = node->mutable_file();
    file->set_path(root_file.path);
    file->set_size(root_file.size);
    file->set_mime_type(root_file.mime_type);
    file->set_md5(root_file.md5);
    file->set_sha256(root_file.sha256);
    file->set_content(std::string(root_file.content.begin(), root_file.content.end()));
  }
  else if (std::holds_alternative<whisper_data_type::Data>(root->content))
  {
    whisper_data_type::Data &root_data = std::get<whisper_data_type::Data>(root->content);
    whisper::Data *data = node->mutable_data();
    data->set_type(root_data.type);
    data->set_content(std::string(root_data.content.begin(), root_data.content.end()));
  }

  whisper::Meta *node_meta = node->mutable_meta();

  for (const auto &[key, value] : root->meta.map_string)
  {
    (*node_meta->mutable_map_string())[key] = value;
  }

  for (const auto &[key, value] : root->meta.map_number)
  {
    (*node_meta->mutable_map_number())[key] = value;
  }

  for (const auto &[key, value] : root->meta.map_bool)
  {
    (*node_meta->mutable_map_bool())[key] = value;
  }
}

void RunServer(int port)
{
  std::string server_address = "0.0.0.0:" + std::to_string(port);
  GreeterServiceImpl service;

  grpc::ServerBuilder builder;
  builder.AddListeningPort(server_address, grpc::InsecureServerCredentials());
  builder.RegisterService(&service);

  std::unique_ptr<grpc::Server> server(builder.BuildAndStart());
  spdlog::info("Server listening on {} ", server_address);
  server->Wait();
}
