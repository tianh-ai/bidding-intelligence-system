#!/bin/bash
# 设置项目数据目录到 SSD 的符号链接

PROJECT_ROOT="/Users/tianmac/vscode/zhaobiao/bidding-intelligence-system/backend"
SSD_DATA="/Volumes/ssd/bidding-data"

echo "🔧 配置数据目录链接到 SSD..."

# 创建 SSD 目录结构
mkdir -p "$SSD_DATA/uploads/temp"
mkdir -p "$SSD_DATA/parsed"
mkdir -p "$SSD_DATA/archive"
mkdir -p "$SSD_DATA/images"
mkdir -p "$SSD_DATA/logs"

# 删除项目中的旧目录（如果存在）
cd "$PROJECT_ROOT"

# 备份现有数据
if [ -d "uploads" ] && [ ! -L "uploads" ]; then
    echo "📦 备份现有 uploads 数据..."
    cp -r uploads/* "$SSD_DATA/uploads/" 2>/dev/null || true
    rm -rf uploads
fi

if [ -d "archive" ] && [ ! -L "archive" ]; then
    echo "📦 备份现有 archive 数据..."
    cp -r archive/* "$SSD_DATA/archive/" 2>/dev/null || true
    rm -rf archive
fi

if [ -d "images" ] && [ ! -L "images" ]; then
    echo "📦 备份现有 images 数据..."
    cp -r images/* "$SSD_DATA/images/" 2>/dev/null || true
    rm -rf images
fi

if [ -d "logs" ] && [ ! -L "logs" ]; then
    echo "📦 备份现有 logs 数据..."
    cp -r logs/* "$SSD_DATA/logs/" 2>/dev/null || true
    rm -rf logs
fi

if [ -d "parsed" ] && [ ! -L "parsed" ]; then
    rm -rf parsed
fi

# 创建符号链接
echo "🔗 创建符号链接..."
ln -sf "$SSD_DATA/uploads" uploads
ln -sf "$SSD_DATA/parsed" parsed
ln -sf "$SSD_DATA/archive" archive
ln -sf "$SSD_DATA/images" images
ln -sf "$SSD_DATA/logs" logs

echo ""
echo "✅ 完成！数据目录已链接到 SSD:"
echo "   uploads  -> $SSD_DATA/uploads"
echo "   parsed   -> $SSD_DATA/parsed"
echo "   archive  -> $SSD_DATA/archive"
echo "   images   -> $SSD_DATA/images"
echo "   logs     -> $SSD_DATA/logs"
echo ""
echo "📁 检查目录内容:"
ls -lh "$PROJECT_ROOT" | grep -E "(uploads|archive|images|logs|parsed)"
echo ""
echo "💾 SSD 实际文件:"
find "$SSD_DATA" -name "*.docx" | head -10
