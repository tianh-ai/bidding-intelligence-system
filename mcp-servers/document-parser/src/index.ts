#!/usr/bin/env node

/**
 * Document Parser MCP Server
 * 
 * Provides document parsing capabilities through MCP protocol:
 * - Parse PDF/DOCX documents
 * - Extract chapters and structure
 * - Extract images from documents
 * - Support for OCR (optional)
 */

import { Server } from '@modelcontextprotocol/sdk/server/index.js';
import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js';
import {
  CallToolRequestSchema,
  ListToolsRequestSchema,
  Tool,
} from '@modelcontextprotocol/sdk/types.js';
import { spawn } from 'child_process';
import { promisify } from 'util';
import { exec as execCallback } from 'child_process';

const exec = promisify(execCallback);

/**
 * Available tools for document parsing
 */
const TOOLS: Tool[] = [
  {
    name: 'parse_document',
    description: 'Parse a PDF or DOCX document and extract text content, chapters, and structure',
    inputSchema: {
      type: 'object',
      properties: {
        file_path: {
          type: 'string',
          description: 'Absolute path to the document file (PDF or DOCX)',
        },
        extract_chapters: {
          type: 'boolean',
          description: 'Whether to extract chapter structure (default: true)',
          default: true,
        },
        extract_images: {
          type: 'boolean',
          description: 'Whether to extract images from the document (default: false)',
          default: false,
        },
        ocr_enabled: {
          type: 'boolean',
          description: 'Enable OCR for scanned PDFs (default: false)',
          default: false,
        },
      },
      required: ['file_path'],
    },
  },
  {
    name: 'extract_chapters',
    description: 'Extract chapter structure from document text content',
    inputSchema: {
      type: 'object',
      properties: {
        content: {
          type: 'string',
          description: 'Document text content to analyze',
        },
        patterns: {
          type: 'array',
          description: 'Custom regex patterns for chapter detection (optional)',
          items: {
            type: 'string',
          },
        },
      },
      required: ['content'],
    },
  },
  {
    name: 'extract_images',
    description: 'Extract all images from a PDF or DOCX document',
    inputSchema: {
      type: 'object',
      properties: {
        file_path: {
          type: 'string',
          description: 'Absolute path to the document file',
        },
        output_dir: {
          type: 'string',
          description: 'Directory to save extracted images',
        },
        format: {
          type: 'string',
          description: 'Output image format (png, jpeg)',
          enum: ['png', 'jpeg'],
          default: 'png',
        },
      },
      required: ['file_path', 'output_dir'],
    },
  },
  {
    name: 'get_document_info',
    description: 'Get basic information about a document (pages, size, format)',
    inputSchema: {
      type: 'object',
      properties: {
        file_path: {
          type: 'string',
          description: 'Absolute path to the document file',
        },
      },
      required: ['file_path'],
    },
  },
];

/**
 * Call Python parsing backend
 */
async function callPythonParser(
  method: string,
  args: Record<string, any>
): Promise<any> {
  const pythonScript = `
import sys
import json
sys.path.insert(0, '${__dirname}/../python')

from document_parser import DocumentParser

parser = DocumentParser()
args = json.loads('${JSON.stringify(args).replace(/'/g, "\\'")}')
result = parser.${method}(**args)
print(json.dumps(result, ensure_ascii=False))
`;

  try {
    const { stdout, stderr } = await exec(`python3 -c "${pythonScript}"`);
    if (stderr) {
      console.error('Python stderr:', stderr);
    }
    return JSON.parse(stdout);
  } catch (error: any) {
    throw new Error(`Python parser error: ${error.message}`);
  }
}

/**
 * Handle tool execution
 */
async function handleToolCall(name: string, args: any): Promise<any> {
  switch (name) {
    case 'parse_document':
      return await callPythonParser('parse_document', {
        file_path: args.file_path,
        extract_chapters: args.extract_chapters ?? true,
        extract_images: args.extract_images ?? false,
        ocr_enabled: args.ocr_enabled ?? false,
      });

    case 'extract_chapters':
      return await callPythonParser('extract_chapters', {
        content: args.content,
        patterns: args.patterns,
      });

    case 'extract_images':
      return await callPythonParser('extract_images', {
        file_path: args.file_path,
        output_dir: args.output_dir,
        format: args.format ?? 'png',
      });

    case 'get_document_info':
      return await callPythonParser('get_document_info', {
        file_path: args.file_path,
      });

    default:
      throw new Error(`Unknown tool: ${name}`);
  }
}

/**
 * Main server setup
 */
async function main() {
  const server = new Server(
    {
      name: 'document-parser-mcp',
      version: '1.0.0',
    },
    {
      capabilities: {
        tools: {},
      },
    }
  );

  // List available tools
  server.setRequestHandler(ListToolsRequestSchema, async () => ({
    tools: TOOLS,
  }));

  // Handle tool calls
  server.setRequestHandler(CallToolRequestSchema, async (request) => {
    try {
      const result = await handleToolCall(request.params.name, request.params.arguments);
      return {
        content: [
          {
            type: 'text',
            text: JSON.stringify(result, null, 2),
          },
        ],
      };
    } catch (error: any) {
      return {
        content: [
          {
            type: 'text',
            text: `Error: ${error.message}`,
          },
        ],
        isError: true,
      };
    }
  });

  // Start server with stdio transport
  const transport = new StdioServerTransport();
  await server.connect(transport);

  console.error('Document Parser MCP Server running on stdio');
}

main().catch((error) => {
  console.error('Fatal error:', error);
  process.exit(1);
});
