"""统一注册 FastAPI 子路由"""

from fastapi import APIRouter

from . import files, learning, enhanced, self_learning, auth, metrics

api_router = APIRouter(prefix="/api")

api_router.include_router(auth.router, prefix="/auth", tags=["认证"])
api_router.include_router(files.router, prefix="/files", tags=["文件"])
api_router.include_router(learning.router, prefix="/learning", tags=["学习"])
api_router.include_router(enhanced.router, prefix="/enhanced", tags=["增强功能"])
api_router.include_router(self_learning.router, prefix="/self-learning", tags=["自学习"])
api_router.include_router(metrics.router, prefix="/metrics")

__all__ = ["api_router"]
