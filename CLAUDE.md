# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

FileWhisperer is a gRPC-based document parsing service that extracts structured data from various file types (ZIP archives, PDFs, Word documents, HTML, etc.) in an LLM-friendly format. The system supports OCR, password-protected archives, and outputs hierarchical tree structures with metadata.

## Python Environment
conda filewhisperer

## Architecture

- **gRPC Service**: Core service defined in `proto/file_whisper.proto` with single `Whispering` RPC endpoint
- **Server**: Python gRPC server (`src/server.py`) using concurrent futures for handling requests
- **Client**: CLI client (`src/client.py`) for testing and interacting with the service
- **File Processing Library**: `src/file_whisper_lib/` contains core extraction and analysis logic
  - `analyzer.py`: Archive analysis (currently commented out pybit7z implementation)
  - `extractor.py`: Main file extraction logic with unified interface
  - `dt.py`: Data type definitions (Node, File, Data)
  - `tree.py`: Tree structure management and file processing
  - `flavors.py`: File type detection and routing to appropriate extractors
  - `extractors/`: Specialized extractors for different file types
- **OCR Support**: PaddleOCR integration with Chinese/English language models in `ocr/` directory
- **Docker**: Containerized deployment for OCR processing

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
# Run all tests using Makefile (recommended)
make test

# Run tests with coverage report
make test-coverage

# Run specific test suites
make test-ocr     # OCR extractor tests only
make test-html    # HTML extractor tests only

# Manual pytest commands
python -m pytest tests/                    # All tests
python -m pytest tests/test_extract_html.py
python -m pytest tests/extractors/test_ocr_extractor.py
python -m pytest tests/extractors/test_archive_extractor.py

# Test GPU functionality
python src/test_gpu.py

# Install test dependencies if needed
make install-test-deps
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

## Code Architecture Details

### Core Data Flow
1. **Request Processing**: `WhisperRequest` can contain either file path or binary content, plus optional passwords and page limits
2. **File Type Detection**: `flavors.py` determines file type and routes to appropriate extractor 
3. **Tree Construction**: `tree.py` manages hierarchical Node structures with parent-child relationships
4. **Content Extraction**: Each extractor in `extractors/` handles specific file types and returns structured data

### Key Extractors
- `ocr_extractor.py`: PaddleOCR integration for text recognition, supports Chinese/English
- `pdf_extractor.py`: PyMuPDF-based PDF text and metadata extraction with page limits
- `word_extractor.py`: python-docx for Word document processing
- `archive_extractor.py`: ZIP/7z archive handling with password support via pybit7z
- `html_extractor.py`: BeautifulSoup-based HTML parsing and URL extraction
- `qrcode_extractor.py`: QR code detection and decoding from images

### Node Structure
- Each `Node` has unique ID, parent/child relationships, and either `File` or `Data` content
- `Meta` provides key-value storage for file metadata and processing parameters
- Tree structures preserve original file hierarchy for archives and nested documents

## Important Notes

- The service processes password-protected archives - use `passwords` field in `WhisperRequest`
- PDF and Word document processing can be limited via `pdf_max_pages` and `word_max_pages` parameters
- OCR processing uses PaddleOCR for text recognition from images
- All file processing returns hierarchical tree structures with unique node IDs
- OCR extractor uses static class variables to maintain model instances across requests for efficiency