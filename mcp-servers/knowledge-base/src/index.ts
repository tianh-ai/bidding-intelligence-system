#!/usr/bin/env node

/**
 * Knowledge Base MCP Server
 * 
 * 提供知识库管理功能：
 * - 搜索知识库条目
 * - 添加/获取/删除知识条目
 * - 列出知识条目
 * - 获取统计信息
 */

import { Server } from '@modelcontextprotocol/sdk/server/index.js';
import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js';
import {
  CallToolRequestSchema,
  ListToolsRequestSchema,
  Tool,
} from '@modelcontextprotocol/sdk/types.js';
import { promisify } from 'util';
import { exec as execCallback } from 'child_process';
import { fileURLToPath } from 'url';
import { dirname, resolve } from 'path';

const exec = promisify(execCallback);
const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);
// 注意：dist 运行时 __dirname 位于 dist/，src 运行时位于 src/。
// 两种情况下知识库根目录都应该是上一级目录。
const kbRoot = resolve(__dirname, '..');
const repoRoot = resolve(kbRoot, '../..');

/**
 * 可用工具定义
 */
const TOOLS: Tool[] = [
  {
    name: 'search_knowledge',
    description: '搜索知识库条目',
    inputSchema: {
      type: 'object',
      properties: {
        query: {
          type: 'string',
          description: '搜索关键词',
        },
        category: {
          type: 'string',
          description: '分类过滤 (tender/proposal/reference)',
          enum: ['tender', 'proposal', 'reference'],
        },
        limit: {
          type: 'number',
          description: '返回数量限制',
          default: 10,
        },
        min_score: {
          type: 'number',
          description: '最小相似度分数',
          default: 0.0,
        },
      },
      required: ['query'],
    },
  },
  {
    name: 'add_knowledge_entry',
    description: '添加知识库条目',
    inputSchema: {
      type: 'object',
      properties: {
        file_id: {
          type: 'string',
          description: '文件ID',
        },
        category: {
          type: 'string',
          description: '分类',
          enum: ['tender', 'proposal', 'reference'],
        },
        title: {
          type: 'string',
          description: '标题',
        },
        content: {
          type: 'string',
          description: '内容',
        },
        keywords: {
          type: 'array',
          items: { type: 'string' },
          description: '关键词列表',
        },
        importance_score: {
          type: 'number',
          description: '重要性分数 (0-100)',
          default: 50.0,
        },
        metadata: {
          type: 'object',
          description: '元数据',
        },
      },
      required: ['file_id', 'category', 'title', 'content'],
    },
  },
  {
    name: 'get_knowledge_entry',
    description: '获取知识库条目详情',
    inputSchema: {
      type: 'object',
      properties: {
        entry_id: {
          type: 'string',
          description: '条目ID',
        },
      },
      required: ['entry_id'],
    },
  },
  {
    name: 'list_knowledge_entries',
    description: '列出知识库条目',
    inputSchema: {
      type: 'object',
      properties: {
        file_id: {
          type: 'string',
          description: '文件ID过滤',
        },
        category: {
          type: 'string',
          description: '分类过滤',
          enum: ['tender', 'proposal', 'reference'],
        },
        limit: {
          type: 'number',
          description: '返回数量限制',
          default: 50,
        },
        offset: {
          type: 'number',
          description: '偏移量',
          default: 0,
        },
      },
      required: [],
    },
  },
  {
    name: 'delete_knowledge_entry',
    description: '删除知识库条目',
    inputSchema: {
      type: 'object',
      properties: {
        entry_id: {
          type: 'string',
          description: '条目ID',
        },
      },
      required: ['entry_id'],
    },
  },
  {
    name: 'get_knowledge_statistics',
    description: '获取知识库统计信息',
    inputSchema: {
      type: 'object',
      properties: {},
      required: [],
    },
  },
  {
    name: 'search_knowledge_semantic',
    description: '语义向量搜索知识库（使用 Ollama embeddings）',
    inputSchema: {
      type: 'object',
      properties: {
        query: {
          type: 'string',
          description: '搜索查询',
        },
        category: {
          type: 'string',
          description: '分类过滤 (tender/proposal/reference)',
          enum: ['tender', 'proposal', 'reference'],
        },
        limit: {
          type: 'number',
          description: '返回数量限制',
          default: 10,
        },
        min_similarity: {
          type: 'number',
          description: '最小相似度阈值 (0-1)',
          default: 0.7,
        },
      },
      required: ['query'],
    },
  },
  {
    name: 'reindex_embeddings',
    description: '批量重建知识库向量索引',
    inputSchema: {
      type: 'object',
      properties: {
        batch_size: {
          type: 'number',
          description: '批次大小',
          default: 10,
        },
        category: {
          type: 'string',
          description: '仅重建特定分类',
          enum: ['tender', 'proposal', 'reference'],
        },
      },
      required: [],
    },
  },
];

/**
 * 调用 Python 后端
 */
async function callPythonBackend(
  method: string,
  args: Record<string, any>
): Promise<any> {
  const fs = await import('fs/promises');
  const fsSync = await import('fs');
  const os = await import('os');
  const path = await import('path');

  // 兼容两种运行形态：
  // - 本地源码：<repo>/backend + <repo>/mcp-servers/knowledge-base/python
  // - Docker（compose 挂载 backend 到 /app）：backendRoot 即 /app
  const backendCandidates = [
    resolve(repoRoot, 'backend'),
    repoRoot,
  ].filter((p) => {
    try {
      return fsSync.existsSync(p);
    } catch {
      return false;
    }
  });
  const pythonDir = resolve(kbRoot, 'python');
  
  // 使用临时文件避免引号转义问题
  const tmpDir = os.tmpdir();
  const scriptPath = path.join(tmpDir, `kb_${Date.now()}_${Math.random().toString(36).slice(2)}.py`);
  
  const pythonScript = `
import sys
import json
import os

# backend 必须在第一位，因为 knowledge_base.py 需要导入 database
for p in ${JSON.stringify(backendCandidates)}:
    if p and os.path.isdir(p) and p not in sys.path:
        sys.path.insert(0, p)

py_dir = r'''${pythonDir}'''
if py_dir and os.path.isdir(py_dir) and py_dir not in sys.path:
    sys.path.insert(0, py_dir)

from knowledge_base import KnowledgeBaseMCP

kb = KnowledgeBaseMCP()
args = json.loads('''${JSON.stringify(args)}''')
result = kb.${method}(**args)
print(json.dumps(result, ensure_ascii=False))
`;

  try {
    // 写入临时文件
    await fs.writeFile(scriptPath, pythonScript, 'utf-8');
    
    // 执行
    const { stdout, stderr } = await exec(`python3 ${scriptPath}`);
    
    // 删除临时文件
    await fs.unlink(scriptPath).catch(() => {});
    
    if (stderr) {
      console.error('Python stderr:', stderr);
    }
    
    return JSON.parse(stdout);
  } catch (error: any) {
    // 确保删除临时文件
    await fs.unlink(scriptPath).catch(() => {});
    throw new Error(`Python backend error: ${error.message}`);
  }
}

/**
 * 处理工具调用
 */
async function handleToolCall(name: string, args: any): Promise<any> {
  switch (name) {
    case 'search_knowledge':
      return await callPythonBackend('search_knowledge', {
        query: args.query,
        category: args.category,
        limit: args.limit ?? 10,
        min_score: args.min_score ?? 0.0,
      });

    case 'add_knowledge_entry':
      return await callPythonBackend('add_knowledge_entry', {
        file_id: args.file_id,
        category: args.category,
        title: args.title,
        content: args.content,
        keywords: args.keywords,
        importance_score: args.importance_score ?? 50.0,
        metadata: args.metadata,
      });

    case 'get_knowledge_entry':
      return await callPythonBackend('get_knowledge_entry', {
        entry_id: args.entry_id,
      });

    case 'list_knowledge_entries':
      return await callPythonBackend('list_knowledge_entries', {
        file_id: args.file_id,
        category: args.category,
        limit: args.limit ?? 50,
        offset: args.offset ?? 0,
      });

    case 'delete_knowledge_entry':
      return await callPythonBackend('delete_knowledge_entry', {
        entry_id: args.entry_id,
      });

    case 'get_knowledge_statistics':
      return await callPythonBackend('get_statistics', {});

    case 'search_knowledge_semantic':
      return await callPythonBackend('search_knowledge_semantic', {
        query: args.query,
        category: args.category,
        limit: args.limit ?? 10,
        min_similarity: args.min_similarity ?? 0.7,
      });

    case 'reindex_embeddings':
      return await callPythonBackend('reindex_embeddings', {
        batch_size: args.batch_size ?? 10,
        category: args.category,
      });

    default:
      throw new Error(`Unknown tool: ${name}`);
  }
}

/**
 * 主服务器设置
 */
async function main() {
  const server = new Server(
    {
      name: 'knowledge-base-mcp',
      version: '1.0.0',
    },
    {
      capabilities: {
        tools: {},
      },
    }
  );

  // 列出可用工具
  server.setRequestHandler(ListToolsRequestSchema, async () => ({
    tools: TOOLS,
  }));

  // 处理工具调用
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

  // 启动服务器
  const transport = new StdioServerTransport();
  await server.connect(transport);

  console.error('Knowledge Base MCP Server running on stdio');
}

main().catch((error) => {
  console.error('Fatal error:', error);
  process.exit(1);
});
