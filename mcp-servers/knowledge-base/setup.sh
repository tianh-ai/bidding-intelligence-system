#!/bin/bash
# Setup script for Knowledge Base MCP Server

set -e

echo "🚀 Setting up Knowledge Base MCP Server..."

# 1. Install Node dependencies
echo "📦 Installing Node.js dependencies..."
cd "$(dirname "$0")"
npm install

# 2. Build TypeScript
echo "🔨 Building TypeScript..."
npm run build

# 3. Make executable
chmod +x dist/index.js

# 4. Verify Python dependencies
echo "🐍 Verifying Python dependencies..."
python3 -c "import sys; sys.path.insert(0, '../../backend'); from database import db" 2>/dev/null || {
    echo "⚠️  Cannot import backend modules. Make sure backend is set up."
}

echo ""
echo "✅ Setup complete!"
echo ""
echo "📋 Next steps:"
echo "1. Test the MCP server:"
echo "   python python/knowledge_base.py stats"
echo ""
echo "2. Use in main program:"
echo "   from core.mcp_client import get_knowledge_base_client"
echo "   client = get_knowledge_base_client()"
echo "   results = await client.search_knowledge('query')"
echo ""
echo "3. Add to MCP client configuration (optional):"
echo '   {
     "mcpServers": {
       "knowledge-base": {
         "command": "node",
         "args": ["'$(pwd)'/dist/index.js"]
       }
     }
   }'
echo ""
