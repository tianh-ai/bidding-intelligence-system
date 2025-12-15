#!/usr/bin/env node

/**
 * Logic Learning MCP Server
 * 
 * 提供逻辑学习功能：
 * - 启动学习任务（章节级/全局级）
 * - 查询学习进度
 * - 获取学习结果
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
const llRoot = resolve(__dirname, '..');
const repoRoot = resolve(llRoot, '../..');

/**
 * 可用工具定义
 */
const TOOLS: Tool[] = [
  {
    name: 'start_learning',
    description: '启动逻辑学习任务（章节级或全局级）',
    inputSchema: {
      type: 'object',
      properties: {
        file_ids: {
          type: 'array',
          items: { type: 'string' },
          description: '学习文件ID列表',
        },
        learning_type: {
          type: 'string',
          description: '学习类型：chapter（章节级）或 global（全局级）',
          enum: ['chapter', 'global'],
        },
        chapter_ids: {
          type: 'array',
          items: { type: 'string' },
          description: '章节ID列表（章节级学习时必填）',
        },
      },
      required: ['file_ids', 'learning_type'],
    },
  },
  {
    name: 'get_learning_status',
    description: '查询学习任务状态',
    inputSchema: {
      type: 'object',
      properties: {
        task_id: {
          type: 'string',
          description: '任务ID',
        },
      },
      required: ['task_id'],
    },
  },
  {
    name: 'get_learning_result',
    description: '获取学习任务完成结果',
    inputSchema: {
      type: 'object',
      properties: {
        task_id: {
          type: 'string',
          description: '任务ID',
        },
      },
      required: ['task_id'],
    },
  },
  {
    name: 'get_logic_database',
    description: '获取逻辑数据库统计',
    inputSchema: {
      type: 'object',
      properties: {
        category: {
          type: 'string',
          description: '分类过滤（可选）',
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
  const pythonDir = resolve(llRoot, 'python');
  
  if (backendCandidates.length === 0) {
    throw new Error('Backend directory not found');
  }
  const backendRoot = backendCandidates[0];

  // 创建临时输入文件
  const tmpInput = path.join(os.tmpdir(), `ll_mcp_${Date.now()}_${Math.random().toString(36)}.json`);
  await fs.writeFile(
    tmpInput,
    JSON.stringify({ method, args }, null, 2),
    'utf-8'
  );

  try {
    // 调用 Python 脚本
    const pythonScript = path.join(pythonDir, 'logic_learning.py');
    
    // 设置 PYTHONPATH 为 backend 目录
    const env = {
      ...process.env,
      PYTHONPATH: backendRoot
    };
    
    const { stdout, stderr } = await exec(
      `cd "${backendRoot}" && python3 "${pythonScript}" "${tmpInput}"`,
      { maxBuffer: 10 * 1024 * 1024, env }
    );

    if (stderr && !stderr.includes('WARNING')) {
      console.error('Python stderr:', stderr);
    }

    // 解析输出
    const lines = stdout.trim().split('\n');
    const lastLine = lines[lines.length - 1];
    const result = JSON.parse(lastLine);

    if (result.error) {
      throw new Error(result.error);
    }

    return result.data;
  } finally {
    // 清理临时文件
    try {
      await fs.unlink(tmpInput);
    } catch {}
  }
}

/**
 * 处理工具调用
 */
async function handleToolCall(name: string, args: any): Promise<any> {
  switch (name) {
    case 'start_learning':
      return await callPythonBackend('start_learning', {
        file_ids: args.file_ids,
        learning_type: args.learning_type,
        chapter_ids: args.chapter_ids || [],
      });

    case 'get_learning_status':
      return await callPythonBackend('get_learning_status', {
        task_id: args.task_id,
      });

    case 'get_learning_result':
      return await callPythonBackend('get_learning_result', {
        task_id: args.task_id,
      });

    case 'get_logic_database':
      return await callPythonBackend('get_logic_database', {
        category: args.category || null,
      });

    default:
      throw new Error(`Unknown tool: ${name}`);
  }
}

/**
 * 主程序
 */
async function main() {
  const server = new Server(
    {
      name: 'logic-learning-mcp',
      version: '1.0.0',
    },
    {
      capabilities: {
        tools: {},
      },
    }
  );

  // 列出工具
  server.setRequestHandler(ListToolsRequestSchema, async () => ({
    tools: TOOLS,
  }));

  // 调用工具
  server.setRequestHandler(CallToolRequestSchema, async (request) => {
    const { name, arguments: args } = request.params;

    try {
      const result = await handleToolCall(name, args || {});
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
            text: JSON.stringify({
              error: error.message || String(error),
            }),
          },
        ],
        isError: true,
      };
    }
  });

  // 启动服务器
  const transport = new StdioServerTransport();
  await server.connect(transport);
  console.error('Logic Learning MCP server running on stdio');
}

main().catch((error) => {
  console.error('Fatal error:', error);
  process.exit(1);
});
