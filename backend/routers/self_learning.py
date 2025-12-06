"""
自学习系统API路由
"""

from fastapi import APIRouter, UploadFile, File, HTTPException
from typing import List, Dict, Any
from pydantic import BaseModel
import os
from pathlib import Path

from core.logger import logger
from engines.self_learning_system import SelfLearningBiddingSystem

router = APIRouter(prefix="/api/self-learning", tags=["self-learning"])

# 全局系统实例
system: SelfLearningBiddingSystem = None


def get_system() -> SelfLearningBiddingSystem:
    """获取或创建系统实例"""
    global system
    if system is None:
        system = SelfLearningBiddingSystem()
    return system


class HumanFeedback(BaseModel):
    """人工反馈模型"""
    approved: bool
    quality_rating: float
    issues: List[Dict[str, str]] = []
    suggestions: List[str] = []


class GenerationRequest(BaseModel):
    """生成请求模型"""
    tender_file_path: str
    max_iterations: int = 5
    quality_threshold: float = 90.0


@router.post("/batch-upload")
async def batch_upload_files(files: List[UploadFile] = File(...)):
    """
    批量上传招投标文件
    
    系统会自动：
    1. 识别文件类型（招标/投标）
    2. 配对同一项目的文件
    3. 提取章节结构
    """
    try:
        sys = get_system()
        
        # 保存上传的文件
        upload_dir = Path("uploads/batch_learning")
        upload_dir.mkdir(parents=True, exist_ok=True)
        
        file_paths = []
        for file in files:
            file_path = upload_dir / file.filename
            
            with open(file_path, "wb") as f:
                content = await file.read()
                f.write(content)
            
            file_paths.append(str(file_path))
            logger.info(f"Uploaded file: {file.filename}")
        
        return {
            "status": "success",
            "files_uploaded": len(file_paths),
            "file_paths": file_paths,
            "message": "文件上传成功，请调用 /batch-learn 开始学习"
        }
        
    except Exception as e:
        logger.error(f"Batch upload failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/batch-learn")
async def batch_learn(file_paths: List[str]):
    """
    批量学习：从文件构建逻辑库和知识库
    
    完整流程：
    1. 智能配对招标-投标文件
    2. 解析文档结构
    3. 生成知识库
    4. 学习生成逻辑库和验证逻辑库
    """
    try:
        sys = get_system()
        
        logger.info(f"Starting batch learning with {len(file_paths)} files")
        
        result = await sys.batch_learn_from_files(file_paths)
        
        return result
        
    except Exception as e:
        logger.error(f"Batch learning failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/generate-proposal")
async def generate_proposal(request: GenerationRequest):
    """
    为新招标文件生成投标文件
    
    基于：
    - 生成逻辑库
    - 验证逻辑库
    - 知识库
    
    支持迭代优化
    """
    try:
        sys = get_system()
        
        result = await sys.generate_proposal_for_tender(
            tender_file_path=request.tender_file_path,
            max_iterations=request.max_iterations,
            quality_threshold=request.quality_threshold
        )
        
        return result
        
    except Exception as e:
        logger.error(f"Proposal generation failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/human-feedback/{proposal_id}")
async def submit_human_feedback(proposal_id: str, feedback: HumanFeedback):
    """
    提交人工验证反馈
    
    系统会：
    1. 分析反馈中的问题
    2. 更新生成逻辑库
    3. 更新验证逻辑库
    4. 优化知识库分割策略
    """
    try:
        sys = get_system()
        
        result = await sys.refine_with_human_feedback(
            proposal_id=proposal_id,
            human_feedback=feedback.dict()
        )
        
        return result
        
    except Exception as e:
        logger.error(f"Feedback processing failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats")
async def get_system_stats():
    """
    获取系统统计信息
    
    包括：
    - 知识库数量和条目
    - 逻辑库规则数量
    - 平均成功率
    """
    try:
        sys = get_system()
        stats = sys.get_system_stats()
        
        return stats
        
    except Exception as e:
        logger.error(f"Get stats failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def health_check():
    """健康检查"""
    return {
        "status": "healthy",
        "system": "Self-Learning Bidding System",
        "version": "1.0.0"
    }
