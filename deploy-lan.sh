#!/bin/bash
# ==============================================
# 标书智能系统 - 局域网部署启动脚本
# ==============================================
# 功能: 一键启动局域网服务器模式
# 作者: AI Assistant
# 日期: 2025-12-08
# ==============================================

set -e  # 遇到错误立即退出

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 打印带颜色的消息
print_info() { echo -e "${BLUE}ℹ️  $1${NC}"; }
print_success() { echo -e "${GREEN}✅ $1${NC}"; }
print_warning() { echo -e "${YELLOW}⚠️  $1${NC}"; }
print_error() { echo -e "${RED}❌ $1${NC}"; }

# 显示标题
echo ""
echo "=============================================="
echo "   标书智能系统 - 局域网服务器部署"
echo "=============================================="
echo ""

# 1. 检查环境
print_info "检查部署环境..."

# 检查Docker
if ! command -v docker &> /dev/null; then
    print_error "Docker 未安装，请先安装 Docker Desktop"
    echo "下载地址: https://www.docker.com/products/docker-desktop"
    exit 1
fi
print_success "Docker 已安装: $(docker --version)"

# 检查Docker Compose
if ! docker compose version &> /dev/null; then
    print_error "Docker Compose 不可用"
    exit 1
fi
print_success "Docker Compose 已安装: $(docker compose version)"

# 检查Docker是否运行
if ! docker info &> /dev/null; then
    print_error "Docker 未运行，请启动 Docker Desktop"
    exit 1
fi
print_success "Docker 服务正在运行"

echo ""

# 2. 检查配置文件
print_info "检查配置文件..."

if [ ! -f ".env.lan" ]; then
    print_error "配置文件 .env.lan 不存在"
    echo "请先运行: cp .env.example .env.lan 并编辑配置"
    exit 1
fi
print_success "配置文件 .env.lan 存在"

# 加载环境变量（过滤注释和空行）
export $(grep -v '^#' .env.lan | grep -v '^$' | sed 's/#.*$//' | xargs -0)

# 检查必填配置
check_config() {
    local var_name=$1
    local var_value=${!var_name}
    if [ -z "$var_value" ] || [[ "$var_value" == *"your-"* ]] || [[ "$var_value" == *"change"* ]]; then
        print_warning "配置项 $var_name 未正确设置"
        return 1
    fi
    return 0
}

has_warnings=0

if ! check_config "DB_PASSWORD"; then has_warnings=1; fi
if ! check_config "SECRET_KEY"; then has_warnings=1; fi
if ! check_config "DEEPSEEK_API_KEY"; then 
    print_warning "DEEPSEEK_API_KEY 未配置，某些AI功能可能不可用"
    has_warnings=1
fi

if [ $has_warnings -eq 1 ]; then
    echo ""
    print_warning "发现配置警告，建议修改 .env.lan 文件"
    read -p "是否继续部署? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        print_info "部署已取消"
        exit 0
    fi
fi

echo ""

# 3. 获取本机局域网IP
print_info "检测局域网IP地址..."

# macOS获取IP
LAN_IP=$(ifconfig | grep "inet " | grep -v 127.0.0.1 | awk '{print $2}' | head -1)

if [ -z "$LAN_IP" ]; then
    print_warning "无法自动获取局域网IP"
    LAN_IP="localhost"
else
    print_success "检测到局域网IP: $LAN_IP"
fi

echo ""

# 4. 检查数据目录
print_info "检查数据存储目录..."

DATA_DIRS=(
    "${HOST_DATA_POSTGRES:-./data/postgres}"
    "${HOST_DATA_REDIS:-./data/redis}"
    "${HOST_DATA_UPLOADS:-./data/uploads}"
    "${HOST_DATA_LOGS:-./data/logs}"
)

missing_dirs=0
for dir in "${DATA_DIRS[@]}"; do
    if [ ! -d "$dir" ]; then
        print_warning "数据目录不存在: $dir"
        missing_dirs=1
    fi
done

if [ $missing_dirs -eq 1 ]; then
    echo ""
    print_info "发现数据目录缺失，运行初始化脚本..."
    if [ -f "./init-data-dirs.sh" ]; then
        bash ./init-data-dirs.sh
    else
        print_error "初始化脚本不存在，请手动创建数据目录"
        exit 1
    fi
fi

echo ""

# 5. 检查端口占用
print_info "检查端口占用情况..."

check_port() {
    local port=$1
    local service=$2
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
        print_warning "端口 $port ($service) 已被占用"
        lsof -Pi :$port -sTCP:LISTEN | tail -1
        return 1
    else
        print_success "端口 $port ($service) 可用"
        return 0
    fi
}

port_conflicts=0
check_port ${FRONTEND_PORT:-5173} "前端" || port_conflicts=1
check_port ${PORT:-8000} "后端API" || port_conflicts=1
check_port ${DB_EXTERNAL_PORT:-5433} "PostgreSQL" || port_conflicts=1
check_port ${REDIS_EXTERNAL_PORT:-6380} "Redis" || port_conflicts=1

if [ $port_conflicts -eq 1 ]; then
    echo ""
    print_warning "发现端口冲突，请关闭占用端口的程序或修改 .env.lan 中的端口配置"
    read -p "是否继续部署? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        print_info "部署已取消"
        exit 0
    fi
fi

echo ""

# 6. 停止现有服务
print_info "停止现有服务..."

if docker compose -f docker-compose.lan.yml ps | grep -q "Up"; then
    docker compose -f docker-compose.lan.yml down
    print_success "已停止现有服务"
else
    print_info "没有运行中的服务"
fi

echo ""

# 7. 构建并启动服务
print_info "构建并启动服务..."
echo "这可能需要几分钟时间，请耐心等待..."
echo ""

docker compose -f docker-compose.lan.yml up -d --build

echo ""

# 8. 等待服务启动
print_info "等待服务启动..."

sleep 10

# 9. 检查服务状态
print_info "检查服务状态..."
echo ""

docker compose -f docker-compose.lan.yml ps

echo ""

# 10. 健康检查
print_info "执行健康检查..."

# 检查后端
BACKEND_URL="http://localhost:${PORT:-8000}/health"
if curl -s "$BACKEND_URL" | grep -q "healthy"; then
    print_success "后端API健康检查通过"
else
    print_warning "后端API健康检查失败，请查看日志"
fi

# 检查前端
FRONTEND_URL="http://localhost:${FRONTEND_PORT:-5173}"
if curl -s "$FRONTEND_URL" >/dev/null 2>&1; then
    print_success "前端服务响应正常"
else
    print_warning "前端服务响应异常，请查看日志"
fi

echo ""

# 11. 防火墙提示
print_warning "局域网访问配置提示:"
echo ""
echo "如需局域网其他设备访问，请确保:"
echo "  1. macOS 防火墙允许 Docker Desktop"
echo "     系统偏好设置 → 安全性与隐私 → 防火墙 → 防火墙选项"
echo ""
echo "  2. 如果使用路由器，确保设备在同一局域网"
echo ""

# 12. 显示访问信息
echo "=============================================="
echo "🎉 部署成功！"
echo "=============================================="
echo ""
echo "📱 本机访问:"
echo "  前端: http://localhost:${FRONTEND_PORT:-5173}"
echo "  后端: http://localhost:${PORT:-8000}"
echo "  API文档: http://localhost:${PORT:-8000}/docs"
echo ""
echo "🌐 局域网访问 (其他设备):"
echo "  前端: http://$LAN_IP:${FRONTEND_PORT:-5173}"
echo "  后端: http://$LAN_IP:${PORT:-8000}"
echo ""
echo "🔐 默认登录凭据:"
echo "  用户名: admin"
echo "  密码: admin123"
echo ""
echo "💾 数据存储位置:"
echo "  ${HOST_DATA_POSTGRES:-./data/postgres}"
echo ""
echo "📋 常用命令:"
echo "  查看日志: docker compose -f docker-compose.lan.yml logs -f"
echo "  停止服务: docker compose -f docker-compose.lan.yml down"
echo "  重启服务: docker compose -f docker-compose.lan.yml restart"
echo ""
echo "=============================================="
