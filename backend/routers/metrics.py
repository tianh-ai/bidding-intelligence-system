from fastapi import APIRouter
from pydantic import BaseModel
from database.connection import db
from core.config import get_settings

settings = get_settings()
router = APIRouter()


class DashboardStats(BaseModel):
    total_files: int
    learned_rules: int
    generation_tasks: int
    success_rate: float


@router.get("/dashboard", response_model=DashboardStats, tags=["统计"])
async def get_dashboard_stats() -> DashboardStats:
    """首页仪表盘统计数据，尽量从数据库/文件中获取真实数据，取不到时回退为 0。"""
    total_files = 0
    learned_rules = 0
    generation_tasks = 0
    success_rate = 0.0

    # 尝试从数据库读取统计数据（如果相关表存在）
    try:
        # 已上传文件数
        try:
            rows = db.query("SELECT COUNT(1) AS c FROM uploaded_files")
            total_files = int(rows[0]["c"]) if rows else 0
        except Exception:
            pass

        # 逻辑规则数
        try:
            rows = db.query("SELECT COUNT(1) AS c FROM logic_rules")
            learned_rules = int(rows[0]["c"]) if rows else 0
        except Exception:
            pass

        # 生成任务数量
        try:
            rows = db.query("SELECT COUNT(1) AS c FROM generation_tasks")
            generation_tasks = int(rows[0]["c"]) if rows else 0
        except Exception:
            pass

        # 成功率（若有评分/任务表，可从中计算，这里容错处理）
        try:
            rows = db.query(
                "SELECT AVG(CASE WHEN status = 'success' THEN 1.0 ELSE 0.0 END) AS r FROM generation_tasks"
            )
            avg_success = rows[0]["r"] if rows else None
            if avg_success is not None:
                success_rate = float(round(float(avg_success) * 100, 2))
        except Exception:
            pass
    except Exception:
        # 数据库不可用时保持默认 0
        pass

    return DashboardStats(
        total_files=total_files,
        learned_rules=learned_rules,
        generation_tasks=generation_tasks,
        success_rate=success_rate,
    )


class ModelInfo(BaseModel):
    id: str
    name: str
    provider: str
    description: str
    is_default: bool = False


@router.get("/models", response_model=list[ModelInfo], tags=["模型"])
async def list_models() -> list[ModelInfo]:
    """返回可选大模型列表，前端用于下拉选择。"""
    models: list[ModelInfo] = [
        ModelInfo(
            id="deepseek-chat",
            name="DeepSeek Chat",
            provider="deepseek",
            description="DeepSeek 深度求索，擅长内容生成和理解",
            is_default=True,
        ),
        ModelInfo(
            id="qwen-plus",
            name="通义千问 Plus",
            provider="qwen",
            description="阿里云千问模型，中文优化，适合分析评估",
        ),
    ]
    return models
