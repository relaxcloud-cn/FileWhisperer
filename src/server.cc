#include <CLI/CLI.hpp>
#include <grpcpp/grpcpp.h>
#include <iostream>
#include <string>
#include <boost/uuid/uuid.hpp>
#include <boost/uuid/uuid_generators.hpp>
#include <boost/uuid/uuid_io.hpp>
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

    whisper::File *file = node->mutable_file();
    file->set_path(request->path());

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