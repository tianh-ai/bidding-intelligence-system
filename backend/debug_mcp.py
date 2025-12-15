#!/usr/bin/env python3
"""
Debug MCP 通信 - 完整流程
"""
import asyncio
import json

async def debug_mcp():
    # 启动 MCP server
    process = await asyncio.create_subprocess_exec(
        "node",
        "/Users/tianmac/vscode/zhaobiao/bidding-intelligence-system/mcp-servers/knowledge-base/dist/index.js",
        stdin=asyncio.subprocess.PIPE,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )
    
    # 1. 初始化
    init_req = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "initialize",
        "params": {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {"name": "test", "version": "1.0.0"}
        }
    }
    
    print("=== 发送初始化请求 ===")
    print(json.dumps(init_req, indent=2))
    
    process.stdin.write((json.dumps(init_req) + '\n').encode())
    await process.stdin.drain()
    
    # 读初始化响应
    init_line = await process.stdout.readline()
    print("\n=== 初始化响应 ===")
    print(init_line.decode())
    
    # 2. 工具调用 - 用第一个文件ID
    tool_req = {
        "jsonrpc": "2.0",
        "id": 2,
        "method": "tools/call",
        "params": {
            "name": "list_knowledge_entries",
            "arguments": {
                "file_id": "05fd3785-adad-4dfe-9d83-6d66da8b49e4",  # 第一个文件
                "limit": 10
            }
        }
    }
    
    print("\n=== 发送工具调用 ===")
    print(json.dumps(tool_req, indent=2))
    
    process.stdin.write((json.dumps(tool_req) + '\n').encode())
    await process.stdin.drain()
    process.stdin.close()
    
    # 读工具响应
    print("\n=== 工具响应 ===")
    tool_line = await process.stdout.readline()
    print("Raw:", repr(tool_line))
    print("Decoded:", tool_line.decode())
    
    # 等待进程
    await process.wait()
    
    # stderr
    stderr = await process.stderr.read()
    if stderr:
        print("\n=== STDERR ===")
        print(stderr.decode())

asyncio.run(debug_mcp())
