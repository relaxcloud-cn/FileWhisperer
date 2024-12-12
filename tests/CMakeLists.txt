add_executable(
    hello_test
    hello_test.cc
    mime_type_test.cc
    url_extract_test.cc
)

target_link_libraries(
    hello_test
    PRIVATE
    file_whisper_lib
    GTest::gtest_main 
)

target_include_directories(hello_test
    PRIVATE
    ${CMAKE_SOURCE_DIR}/file_whisper_lib
)

include(GoogleTest)
gtest_discover_tests(hello_test)