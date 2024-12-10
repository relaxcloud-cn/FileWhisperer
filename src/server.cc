#include <CLI/CLI.hpp>
#include <grpcpp/grpcpp.h>
#include <iostream>
#include <string>
#include <boost/uuid/uuid.hpp>
#include <boost/uuid/uuid_generators.hpp>
#include <boost/uuid/uuid_io.hpp>
#include <mio/mmap.hpp>
#include <iostream>
#include "common.hpp"
#include "cpp/file_whisper.grpc.pb.h"

class GreeterServiceImpl final : public whisper::Whisper::Service
{
  grpc::Status Whispering(grpc::ServerContext *context,
                          const whisper::WhisperRequest *request,
                          whisper::WhisperReply *reply) override
  {
    boost::uuids::random_generator generator;
    boost::uuids::uuid uuid = generator();

    whisper::Node *node = reply->add_tree();
    node->set_id(boost::uuids::to_string(uuid));

    mio::mmap_source mmap(request->path());
    const uint8_t* data = reinterpret_cast<const uint8_t*>(mmap.data());
    auto data_size = mmap.size();

    whisper::File *file = node->mutable_file();
    file->set_path(request->path());
    file->set_size(data_size);
    file->set_md5(calculate_md5(data, data_size));
    file->set_sha256(calculate_sha256(data, data_size));

    return grpc::Status::OK;
  }
};

void RunServer(int port)
{
  std::string server_address = "0.0.0.0:" + std::to_string(port);
  GreeterServiceImpl service;

  grpc::ServerBuilder builder;
  builder.AddListeningPort(server_address, grpc::InsecureServerCredentials());
  builder.RegisterService(&service);

  std::unique_ptr<grpc::Server> server(builder.BuildAndStart());
  std::cout << "Server listening on " << server_address << std::endl;
  server->Wait();
}

int main(int argc, char **argv) {
    CLI::App app{"FileWhisperer server"};
    
    int port = 50051;
    app.add_option("-p,--port", port, "Port to listen on")
        ->check(CLI::Range(1, 65535));

    try {
        app.parse(argc, argv);
    } catch(const CLI::ParseError &e) {
        return app.exit(e);
    }

    RunServer(port);
    return 0;
}