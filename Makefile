# Extended Makefile to Generate C++ Server and Python Client from .proto Files

# Directory containing .proto files
PROTO_DIR = ./proto

# Output directories for generated code
PYTHON_CODE_DIR = ./src
CPP_CODE_DIR = ./cpp

# Docker configuration
DOCKER_IMAGE_NAME = filewhisperer
DOCKER_IMAGE_TAG = latest
DOCKER_BUILD_FLAGS = --progress=plain

# Find all .proto files in the proto directory
PROTO_FILES = $(wildcard $(PROTO_DIR)/*.proto)

# Specify the output directories for Python and C++
PYTHON_OUT = $(PYTHON_CODE_DIR)
GRPC_PYTHON_OUT = $(PYTHON_CODE_DIR)
CPP_OUT = $(CPP_CODE_DIR)
GRPC_CPP_OUT = $(CPP_CODE_DIR)

# Protoc compilers
PROTOC_PYTHON = python -m grpc_tools.protoc
PROTOC_CPP = ./vcpkg_installed/arm64-osx/tools/protobuf/protoc  # Assumes protoc from vcpkg is in PATH

# Paths to grpc_cpp_plugin installed via vcpkg
# Adjust the path below to match where vcpkg installs grpc_cpp_plugin on your system
GRPC_CPP_PLUGIN = $(shell which grpc_cpp_plugin)

# System information for Docker build
CORES = $(shell nproc 2>/dev/null || sysctl -n hw.ncpu 2>/dev/null || echo 1)
MEMORY = $(shell free -g 2>/dev/null | awk '/^Mem:/{print $$2}' || echo 4)

# Phony targets
.PHONY: all clean generate_proto install_deps gen_python gen_cpp list docker-build docker-clean docker-rebuild test test-install check-pytest install-test-deps

# Default target to install dependencies and generate code
all: install_deps generate_proto

# Generate both Python and C++ code
generate_proto: gen_python gen_cpp

# Shortcut target to generate proto files
gen: generate_proto

# Install necessary dependencies
install_deps:
	@echo "Installing Python dependencies..."
	pip install grpcio grpcio-tools
	@echo "Ensure that gRPC C++ is installed via vcpkg and that grpc_cpp_plugin is in your PATH."
	@echo "For example, on macOS with Homebrew:"
	@echo "  brew install grpc"
	@echo "Or using vcpkg:"
	@echo "  ./vcpkg install grpc"
	@echo "  ./vcpkg integrate install"

# Generate Python client code from proto files
gen_python:
	@echo "Generating Python code from proto files..."
	@mkdir -p $(PYTHON_OUT)
	@for proto in $(PROTO_FILES); do \
		$(PROTOC_PYTHON) -I$(PROTO_DIR) \
			--python_out=$(PYTHON_OUT) \
			--grpc_python_out=$(GRPC_PYTHON_OUT) \
			$$proto; \
		echo "Generated Python code for $$proto"; \
	done

# Generate C++ server code from proto files using vcpkg's protoc and grpc_cpp_plugin
gen_cpp:
	@echo "Generating C++ code from proto files..."
	@mkdir -p $(CPP_OUT)
	@if [ -z "$(GRPC_CPP_PLUGIN)" ]; then \
		echo "Error: grpc_cpp_plugin not found in PATH. Please ensure gRPC C++ is installed via vcpkg and grpc_cpp_plugin is in your PATH."; \
		exit 1; \
	fi
	@for proto in $(PROTO_FILES); do \
		$(PROTOC_CPP) -I$(PROTO_DIR) \
			--cpp_out=$(CPP_OUT) \
			--grpc_out=$(GRPC_CPP_OUT) \
			--plugin=protoc-gen-grpc=$(GRPC_CPP_PLUGIN) \
			$$proto; \
		echo "Generated C++ code for $$proto"; \
	done

# Clean generated Python and C++ files
clean:
	@echo "Cleaning generated Python files..."
	@find $(PYTHON_OUT) -type f \( -name "*_pb2.py" -o -name "*_pb2_grpc.py" \) -delete
	@echo "Cleaning generated C++ files..."
	@find $(CPP_OUT) -type f \( -name "*.cc" -o -name "*.h" -o -name "*_pb2_grpc.cc" -o -name "*_pb2_grpc.h" \) -delete

# List all .proto files
list:
	@echo "Proto files found:"
	@for proto in $(PROTO_FILES); do \
		echo "  $$proto"; \
	done

# Docker targets
docker-build:
	@echo "Building Docker image using $(CORES) cores..."
	DOCKER_BUILDKIT=$(DOCKER_BUILDKIT) docker build \
		$(DOCKER_BUILD_FLAGS) \
		--build-arg BUILDKIT_INLINE_CACHE=1 \
		--build-arg MAKEFLAGS="-j$(CORES)" \
		-t $(DOCKER_IMAGE_NAME):$(DOCKER_IMAGE_TAG) \
		.

docker-clean:
	@echo "Removing Docker image $(DOCKER_IMAGE_NAME):$(DOCKER_IMAGE_TAG)..."
	docker rmi -f $(DOCKER_IMAGE_NAME):$(DOCKER_IMAGE_TAG)

docker-rebuild: docker-clean docker-build

# Testing targets
check-pytest:
	@echo "Checking if pytest is installed..."
	@python -c "import pytest" 2>/dev/null || { \
		echo "pytest is not installed. Installing pytest..."; \
		pip install pytest pytest-cov; \
	}
	@echo "pytest is available."

install-test-deps: check-pytest
	@echo "Installing additional test dependencies..."
	@pip install pytest pytest-cov

test: check-pytest
	@echo "Running all tests with pytest..."
	python -m pytest tests/ -v || true

test-install: install-test-deps test
	@echo "Test dependencies installed and tests completed."

test-coverage: check-pytest
	@echo "Running tests with coverage report..."
	python -m pytest tests/ --cov=src --cov-report=html --cov-report=term -v
	@echo "Coverage report generated in htmlcov/ directory"

test-ocr:
	@echo "Running OCR extractor tests only..."
	python -m pytest tests/extractors/test_ocr_extractor.py -v

test-html:
	@echo "Running HTML extractor tests only..."
	python -m pytest tests/test_extract_html*.py -v

# Help target
help:
	@echo "Available targets:"
	@echo "  all              : Install dependencies and generate code (default)"
	@echo "  generate_proto   : Generate both Python and C++ code"
	@echo "  gen              : Shortcut for generate_proto"
	@echo "  install_deps     : Install required dependencies"
	@echo "  gen_python       : Generate Python code only"
	@echo "  gen_cpp          : Generate C++ code only"
	@echo "  clean            : Clean generated files"
	@echo "  list             : List all .proto files"
	@echo "  docker-build     : Build Docker image"
	@echo "  docker-clean     : Remove Docker image"
	@echo "  docker-rebuild   : Clean and rebuild Docker image"
	@echo "  test             : Run all tests (installs pytest if needed)"
	@echo "  test-install     : Install test dependencies and run tests"
	@echo "  test-coverage    : Run tests with coverage report"
	@echo "  test-ocr         : Run OCR extractor tests only"
	@echo "  test-html        : Run HTML extractor tests only"
	@echo "  check-pytest     : Check if pytest is installed"
	@echo "  install-test-deps: Install pytest and test dependencies"
	@echo "  help             : Show this help message"