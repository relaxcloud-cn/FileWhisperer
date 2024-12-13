add_library(file_whisper_lib
    common.cc
    data_type.cc
    extractor.cc
)

target_include_directories(file_whisper_lib
    PUBLIC
    ${CMAKE_CURRENT_SOURCE_DIR}
)

add_definitions(-DU_STATIC_IMPLEMENTATION)

find_package(OpenSSL REQUIRED)
find_package(Boost REQUIRED COMPONENTS uuid)
find_package(unofficial-libmagic REQUIRED)
find_package(ICU COMPONENTS data uc i18n io REQUIRED)
find_package(re2 CONFIG REQUIRED)
find_package(spdlog CONFIG REQUIRED)

if(APPLE)
    set(WHOLE_ARCHIVE_FLAG "-force_load")
    set(NO_WHOLE_ARCHIVE_FLAG "")
else()
    set(WHOLE_ARCHIVE_FLAG "-Wl,--whole-archive")
    set(NO_WHOLE_ARCHIVE_FLAG "-Wl,--no-whole-archive")
endif()

target_link_libraries(file_whisper_lib
    PUBLIC
    OpenSSL::SSL
    OpenSSL::Crypto
    Boost::uuid
    unofficial::libmagic::libmagic
    ICU::data 
    ICU::uc 
    ICU::i18n 
    ICU::io
    re2::re2
    spdlog::spdlog
    ${WHOLE_ARCHIVE_FLAG} ${ICU_DATA_LIBRARY} ${NO_WHOLE_ARCHIVE_FLAG}
)