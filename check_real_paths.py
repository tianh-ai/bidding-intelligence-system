#!/usr/bin/env python3
import sys
sys.path.insert(0, '/Users/tianmac/vscode/zhaobiao/bidding-intelligence-system/backend')

from database import db

files = db.query("""
    SELECT filename, archive_path, created_at 
    FROM uploaded_files 
    WHERE created_at >= NOW() - INTERVAL '1 day'
    ORDER BY created_at DESC 
    LIMIT 20
""")

print(f"找到 {len(files)} 个文件\n")
for f in files:
    print(f"文件: {f['filename']}")
    print(f"路径: {f['archive_path']}")
    print(f"时间: {f['created_at']}")
    print()
