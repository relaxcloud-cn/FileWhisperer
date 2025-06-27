# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

FileWhisperer is a gRPC-based document parsing service that extracts structured data from various file types (ZIP archives, PDFs, Word documents, HTML, etc.) in an LLM-friendly format. The system supports OCR, password-protected archives, and outputs hierarchical tree structures with metadata.

## Architecture

- **gRPC Service**: Core service defined in `proto/file_whisper.proto` with single `Whispering` RPC endpoint
- **Server**: Python gRPC server (`src/server.py`) using concurrent futures for handling requests
- **Client**: CLI client (`src/client.py`) for testing and interacting with the service
- **File Processing Library**: `src/file_whisper_lib/` contains core extraction and analysis logic
  - `analyzer.py`: Archive analysis (currently commented out pybit7z implementation)
  - `extractor.py`: Main file extraction logic
  - `dt.py`: Data type definitions (Node, File, Data)
  - `tree.py`: Tree structure management
  - `flavors.py`: File type detection and handling
- **OCR Support**: PaddleOCR integration with Chinese/English language models in `ocr/` directory
- **Docker**: Containerized deployment with GPU support for OCR processing

## Development Commands

### Protocol Buffer Generation
```bash
# Generate both Python and C++ gRPC code from proto files
make generate_proto
# or shortcut
make gen

# Generate Python code only
make gen_python

# List all proto files
make list
```

### Dependencies
```bash
# Install Python dependencies
pip install -r requirements.txt

# Install gRPC tools for protocol buffer generation
make install_deps
```

### Running the Service
```bash
# Start gRPC server (default port 50051)
python src/server.py

# Start with custom port and logging
python src/server.py -p 50098 -l info

# Run client example
python src/client.py run tests/fixtures/test_with_pwd_abcd.zip --binary -p123 -pabcd
```

### Testing
```bash
# Run specific test files
python -m pytest tests/test_extract_html.py
python -m pytest tests/test_extract_html2.py
python -m pytest tests/test_extract_html3.py

# Test GPU functionality
python src/test_gpu.py
```

### Docker Operations
```bash
# Build Docker image
make docker-build

# Clean Docker image
make docker-clean

# Rebuild (clean + build)
make docker-rebuild

# Run with docker-compose
docker-compose up -d
```

## Environment Variables

- `TESSDATA_PREFIX`: Path to Tesseract language data (for OCR)
- `FILE_WHISPERER_OUTPUT_DIR`: Output directory for processed files
- `PADDLEOCR_LOG_LEVEL`: Control PaddleOCR logging verbosity

## Key File Locations

- Protocol definitions: `proto/file_whisper.proto`
- Generated gRPC code: `src/file_whisper_pb2.py` and `src/file_whisper_pb2_grpc.py`
- Test fixtures: `tests/fixtures/` (includes various file types for testing)
- OCR models: `ocr/whl/` (PaddleOCR Chinese and English models)
- Documentation: `doc/` (requirements, gRPC message specs, environment setup)

## Branching Strategy

Follow this merge flow: `doc` → `dev` → `main`

## Important Notes

- The service processes password-protected archives - use `passwords` field in `WhisperRequest`
- PDF and Word document processing can be limited via `pdf_max_pages` and `word_max_pages` parameters
- OCR processing requires GPU support for optimal performance
- All file processing returns hierarchical tree structures with unique node IDs