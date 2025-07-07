#include "test_utils.hpp"

namespace test_utils {
    std::filesystem::path get_project_root() {
        return std::filesystem::path(__FILE__).parent_path().parent_path();
    }
    
    std::filesystem::path get_test_file_path(const std::string& relative_path) {
        return get_project_root() / relative_path;
    }
}
