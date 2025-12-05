"""
标书智能系统 - FastAPI主程序
提供文件上传、解析、学习、生成、评分等核心API
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 导入路由
from routers import files, learning

# 创建应用实例
app = FastAPI(
    title="标书智能系统API",
    description="投标文件智能生成与分析系统",
    version="1.0.0"
)

# CORS配置(允许前端跨域访问)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境应指定具体域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(files.router, prefix="/api/files", tags=["文件管理"])
app.include_router(learning.router, prefix="/api/learning", tags=["逻辑学习"])

# 静态文件目录
UPLOAD_DIR = os.getenv("UPLOAD_DIR", "./uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

# 健康检查
@app.get("/health")
async def health_check():
    """健康检查接口"""
    return {"status": "healthy", "service": "bidding-system"}


@app.get("/")
async def root():
    """根路径"""
    return {
        "message": "标书智能系统API",
        "version": "1.0.0",
        "docs": "/docs"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
