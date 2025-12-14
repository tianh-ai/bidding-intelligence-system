# Document Parser MCP Server

A Model Context Protocol (MCP) server that provides document parsing capabilities for PDF and DOCX files.

## Features

- 📄 **Document Parsing**: Extract text content from PDF and DOCX files
- 📚 **Chapter Extraction**: Automatically detect and extract chapter structure
- 🖼️ **Image Extraction**: Extract embedded images from documents
- 🔍 **OCR Support**: Optional OCR for scanned PDFs
- 📊 **Document Info**: Get metadata (pages, size, format)

## Installation

```bash
cd mcp-document-parser
npm install
npm run build
```

## Usage

### As MCP Server

Add to your MCP client configuration (e.g., Claude Desktop):

```json
{
  "mcpServers": {
    "document-parser": {
      "command": "node",
      "args": ["/path/to/mcp-document-parser/dist/index.js"]
    }
  }
}
```

### Available Tools

#### 1. `parse_document`

Parse a PDF or DOCX document and extract all content.

```json
{
  "file_path": "/path/to/document.pdf",
  "extract_chapters": true,
  "extract_images": false,
  "ocr_enabled": false
}
```

**Returns:**
```json
{
  "filename": "document.pdf",
  "content": "Full text content...",
  "content_length": 12345,
  "chapters": [
    {
      "chapter_number": "1.1",
      "chapter_title": "Introduction",
      "chapter_level": 2,
      "content": "Chapter content...",
      "position": 1
    }
  ],
  "metadata": {
    "size_mb": 2.5,
    "page_count": 50
  }
}
```

#### 2. `extract_chapters`

Extract chapter structure from text content.

```json
{
  "content": "Your document text here..."
}
```

#### 3. `extract_images`

Extract all images from a document.

```json
{
  "file_path": "/path/to/document.pdf",
  "output_dir": "/path/to/output",
  "format": "png"
}
```

#### 4. `get_document_info`

Get basic document information without parsing.

```json
{
  "file_path": "/path/to/document.pdf"
}
```

## Python CLI

Test the parser directly:

```bash
# Parse document
python python/document_parser.py parse /path/to/doc.pdf --extract-images

# Extract chapters only
python python/document_parser.py chapters /path/to/doc.pdf

# Extract images
python python/document_parser.py images /path/to/doc.pdf --output-dir ./images

# Get document info
python python/document_parser.py info /path/to/doc.pdf
```

## Architecture

```
mcp-document-parser/
├── src/
│   └── index.ts          # TypeScript MCP server
├── python/
│   └── document_parser.py # Python parsing backend
├── package.json
├── tsconfig.json
└── README.md
```

The MCP server (TypeScript) handles the MCP protocol and calls the Python backend for actual document processing. This allows reusing existing parsing engines from the main bidding system.

## Dependencies

- **Backend Engines**: Uses existing `ParseEngine`, `EnhancedChapterExtractor`, and `ImageExtractor` from the main system
- **Python Libraries**: pypdf, python-docx, PIL
- **MCP SDK**: @modelcontextprotocol/sdk

## Integration with Main System

This MCP server is designed to work alongside the bidding intelligence system:

- Shares the same parsing engines (`backend/engines/`)
- Can be used independently or as part of the main system
- Provides standardized API through MCP protocol

## License

MIT
