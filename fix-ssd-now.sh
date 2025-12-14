#!/bin/bash
set -e

echo "🔧 开始配置 SSD 存储..."

# 1. 创建 SSD 目录
echo "📁 创建 SSD 目录结构..."
mkdir -p /Volumes/ssd/bidding-data/uploads/temp
mkdir -p /Volumes/ssd/bidding-data/archive
mkdir -p /Volumes/ssd/bidding-data/images  
mkdir -p /Volumes/ssd/bidding-data/logs
mkdir -p /Volumes/ssd/bidding-data/parsed

# 2. 从 Docker 容器复制文件到 SSD
echo "📦 从容器复制文件到 SSD..."
docker exec bidding_backend find /Volumes/ssd/bidding-data/archive -type f 2>/dev/null | while read file; do
    echo "  复制: $file"
done || echo "容器内没有文件"

docker cp bidding_backend:/Volumes/ssd/bidding-data/ /Volumes/ssd/ 2>/dev/null || echo "容器内路径不存在，跳过"

# 3. 从项目目录复制已有文件
echo "📦 复制项目现有文件到 SSD..."
if [ -d "backend/uploads/archive" ]; then
    cp -rv backend/uploads/archive/* /Volumes/ssd/bidding-data/archive/ 2>/dev/null || true
fi

# 4. 在项目中创建符号链接
echo "🔗 创建符号链接..."
cd backend

rm -rf uploads/archive uploads/parsed images logs 2>/dev/null || true

ln -sf /Volumes/ssd/bidding-data/archive uploads/archive
ln -sf /Volumes/ssd/bidding-data/parsed uploads/parsed  
ln -sf /Volumes/ssd/bidding-data/images images
ln -sf /Volumes/ssd/bidding-data/logs logs

cd ..

# 5. 重启 Docker
echo "🔄 重启 Docker 容器..."
docker-compose down
docker-compose up -d

# 6. 验证
echo ""
echo "✅ 配置完成！"
echo ""
echo "📊 检查 SSD 文件:"
find /Volumes/ssd/bidding-data/archive -name "*.docx" 2>/dev/null | head -10
echo ""
echo "🔗 检查符号链接:"
ls -lh backend/ | grep -E "(uploads|images|logs)"
