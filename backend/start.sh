#!/bin/bash
# 标书智能系统 - 启动脚本

echo "========================================="
echo "标书智能系统后端启动中..."
echo "========================================="

# 检查Python环境
if ! command -v python3 &> /dev/null; then
    echo "错误: 未找到Python3,请先安装Python 3.8+"
    exit 1
fi

# 检查依赖
echo "检查依赖..."
pip list | grep fastapi > /dev/null
if [ $? -ne 0 ]; then
    echo "正在安装依赖..."
    pip install -r requirements.txt
fi

# 创建上传目录
mkdir -p uploads

# 检查环境变量文件
if [ ! -f .env ]; then
    echo "警告: .env文件不存在,使用示例配置"
    cp .env.example .env
fi

# 启动服务
echo "启动FastAPI服务..."
echo "========================================="
python3 main.py
