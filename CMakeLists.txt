cmake_minimum_required(VERSION 3.14)
project(FileWhisperer)

set(CMAKE_CXX_STANDARD 14)

find_package(gRPC CONFIG REQUIRED)
find_package(Protobuf CONFIG REQUIRED)
find_package(CLI11 CONFIG REQUIRED)
find_package(Boost REQUIRED COMPONENTS uuid)
find_package(OpenSSL REQUIRED)
find_package(mio CONFIG REQUIRED)

include_directories(${CMAKE_CURRENT_SOURCE_DIR}) 

add_executable(
    FileWhisperer 
    src/server.cc 
    src/common.cc 
    cpp/file_whisper.grpc.pb.cc
    cpp/file_whisper.pb.cc
)
    
target_link_libraries(FileWhisperer 
    PRIVATE 
    gRPC::grpc++ 
    protobuf::libprotobuf
    CLI11::CLI11
    Boost::uuid
    mio::mio 
    mio::mio-headers
    OpenSSL::SSL
    OpenSSL::Crypto
)
    
find_package(GTest CONFIG REQUIRED)
enable_testing()
add_subdirectory(tests)
