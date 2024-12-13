cmake_minimum_required(VERSION 3.14)
project(FileWhisperer)

option(BUILD_TESTING "Build the testing tree." OFF)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

add_definitions(-DU_STATIC_IMPLEMENTATION)

add_subdirectory(file_whisper_lib)

find_package(gRPC CONFIG REQUIRED)
find_package(Protobuf CONFIG REQUIRED)
find_package(CLI11 CONFIG REQUIRED)
find_package(mio CONFIG REQUIRED)
find_package(spdlog CONFIG REQUIRED)

include_directories(${CMAKE_CURRENT_SOURCE_DIR}) 

add_executable(
    FileWhisperer 
    src/server.cc 
    cpp/file_whisper.grpc.pb.cc
    cpp/file_whisper.pb.cc
)
    
target_link_libraries(FileWhisperer 
    PRIVATE 
    file_whisper_lib
    gRPC::grpc++ 
    protobuf::libprotobuf
    CLI11::CLI11
    mio::mio 
    mio::mio-headers
    spdlog::spdlog
)

target_include_directories(FileWhisperer
    PRIVATE
    ${CMAKE_SOURCE_DIR}/file_whisper_lib
)
    
if(BUILD_TESTING)
    find_package(GTest CONFIG REQUIRED)
    enable_testing()
    add_subdirectory(tests)
endif()