#!/bin/bash

# Docker 服务管理脚本
# 用于启动、停止、重启整个标书智能系统

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 项目根目录
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_ROOT"

# 打印带颜色的消息
print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

# 检查 Docker 是否运行
check_docker() {
    print_info "检查 Docker 状态..."
    if ! docker info >/dev/null 2>&1; then
        print_error "Docker 未运行！"
        print_warning "请执行以下步骤："
        echo "  1. 打开 Docker Desktop 应用"
        echo "  2. 等待 Docker 完全启动（状态栏显示绿色）"
        echo "  3. 重新运行此脚本"
        exit 1
    fi
    print_success "Docker 正在运行"
}

# 检查必要文件
check_requirements() {
    print_info "检查必要文件..."
    
    if [ ! -f "docker-compose.yml" ]; then
        print_error "找不到 docker-compose.yml"
        exit 1
    fi
    
    if [ ! -f "backend/Dockerfile" ]; then
        print_error "找不到 backend/Dockerfile"
        exit 1
    fi
    
    if [ ! -f "frontend/Dockerfile" ]; then
        print_error "找不到 frontend/Dockerfile"
        exit 1
    fi
    
    print_success "所有必要文件存在"
}

# 启动服务
start_services() {
    print_info "启动所有 Docker 服务..."
    
    # 先启动数据库和 Redis
    print_info "启动数据库和缓存..."
    docker compose up -d postgres redis
    
    # 等待数据库就绪
    print_info "等待数据库就绪..."
    for i in {1..30}; do
        if docker compose exec -T postgres pg_isready -U postgres >/dev/null 2>&1; then
            print_success "数据库已就绪"
            break
        fi
        echo -n "."
        sleep 2
    done
    
    # 启动后端和 Celery
    print_info "启动后端服务..."
    docker compose up -d backend celery_worker
    
    # 等待后端就绪
    print_info "等待后端服务就绪..."
    sleep 5
    
    # 启动前端
    print_info "启动前端服务..."
    docker compose up -d frontend
    
    print_success "所有服务已启动"
}

# 停止服务
stop_services() {
    print_info "停止所有服务..."
    docker compose down
    print_success "所有服务已停止"
}

# 重启服务
restart_services() {
    print_info "重启所有服务..."
    stop_services
    sleep 2
    start_services
}

# 查看服务状态
show_status() {
    print_info "服务状态："
    docker compose ps
    
    echo ""
    print_info "服务访问地址："
    echo "  🌐 前端: http://localhost:5173"
    echo "  🔧 后端 API: http://localhost:8000"
    echo "  📚 API 文档: http://localhost:8000/docs"
    echo "  🗄️  PostgreSQL: localhost:5433"
    echo "  🔴 Redis: localhost:6380"
}

# 查看日志
show_logs() {
    SERVICE=${1:-}
    if [ -z "$SERVICE" ]; then
        print_info "查看所有服务日志 (Ctrl+C 退出)..."
        docker compose logs -f
    else
        print_info "查看 $SERVICE 服务日志 (Ctrl+C 退出)..."
        docker compose logs -f "$SERVICE"
    fi
}

# 重建服务
rebuild_services() {
    print_info "重建所有服务..."
    docker compose down
    docker compose build --no-cache
    docker compose up -d
    print_success "服务重建完成"
}

# 清理所有数据
clean_all() {
    print_warning "这将删除所有容器、数据卷和镜像！"
    read -p "确定要继续吗？(yes/no): " confirm
    
    if [ "$confirm" = "yes" ]; then
        print_info "停止并删除所有容器..."
        docker compose down -v
        
        print_info "删除相关镜像..."
        docker images | grep bidding | awk '{print $3}' | xargs docker rmi -f 2>/dev/null || true
        
        print_success "清理完成"
    else
        print_info "取消操作"
    fi
}

# 进入容器
exec_container() {
    SERVICE=${1:-backend}
    print_info "进入 $SERVICE 容器..."
    docker compose exec "$SERVICE" /bin/bash
}

# 初始化数据库
init_database() {
    print_info "初始化数据库..."
    docker compose exec -T postgres psql -U postgres -d bidding_db -f /docker-entrypoint-initdb.d/init.sql
    print_success "数据库初始化完成"
}

# 显示帮助
show_help() {
    cat << EOF
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
标书智能系统 Docker 管理脚本
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

用法: ./docker-manager.sh [命令]

命令:
  start       启动所有服务
  stop        停止所有服务
  restart     重启所有服务
  status      查看服务状态
  logs        查看所有服务日志
  logs <服务> 查看指定服务日志 (backend/frontend/postgres/redis/celery_worker)
  rebuild     重建所有服务（清除缓存）
  clean       清理所有数据（危险操作）
  exec        进入后端容器
  exec <服务> 进入指定服务容器
  init-db     初始化数据库
  help        显示此帮助信息

示例:
  ./docker-manager.sh start              # 启动所有服务
  ./docker-manager.sh logs backend       # 查看后端日志
  ./docker-manager.sh exec postgres      # 进入数据库容器

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
EOF
}

# 主程序
main() {
    case "${1:-}" in
        start)
            check_docker
            check_requirements
            start_services
            show_status
            ;;
        stop)
            stop_services
            ;;
        restart)
            check_docker
            restart_services
            show_status
            ;;
        status)
            show_status
            ;;
        logs)
            show_logs "${2:-}"
            ;;
        rebuild)
            check_docker
            rebuild_services
            show_status
            ;;
        clean)
            clean_all
            ;;
        exec)
            exec_container "${2:-backend}"
            ;;
        init-db)
            init_database
            ;;
        help|--help|-h)
            show_help
            ;;
        *)
            print_error "未知命令: ${1:-}"
            echo ""
            show_help
            exit 1
            ;;
    esac
}

# 执行主程序
main "$@"
