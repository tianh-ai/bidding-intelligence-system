#!/bin/bash
# Setup script for Document Parser MCP Server

set -e

echo "🚀 Setting up Document Parser MCP Server..."

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
python3 -c "import pypdf, docx, PIL" 2>/dev/null || {
    echo "⚠️  Python dependencies missing. Installing..."
    pip3 install pypdf python-docx Pillow
}

echo ""
echo "✅ Setup complete!"
echo ""
echo "📋 Next steps:"
echo "1. Add to your MCP client configuration:"
echo ""
echo '   {
     "mcpServers": {
       "document-parser": {
         "command": "node",
         "args": ["'$(pwd)'/dist/index.js"]
       }
     }
   }'
echo ""
echo "2. Test with Python CLI:"
echo "   python python/document_parser.py info /path/to/doc.pdf"
echo ""
