add_library(file_whisper_lib
    common.cc
)

target_include_directories(file_whisper_lib
    PUBLIC
    ${CMAKE_CURRENT_SOURCE_DIR}
)

find_package(OpenSSL REQUIRED)
find_package(unofficial-libmagic REQUIRED)

target_link_libraries(file_whisper_lib
    PUBLIC
    OpenSSL::SSL
    OpenSSL::Crypto
    unofficial::libmagic::libmagic
)