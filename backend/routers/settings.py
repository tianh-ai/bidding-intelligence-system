"""
系统设置管理路由
提供系统配置的查询和修改功能
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Optional
from core.config import get_settings
from core.logger import logger
import os

router = APIRouter(prefix="/api/settings", tags=["系统设置"])

# ========== Pydantic Models ==========

class UploadSettings(BaseModel):
    """文件上传设置"""
    upload_dir: str = Field(..., description="上传目录路径（支持相对或绝对路径）")
    max_file_size: int = Field(..., description="最大文件大小（字节）", ge=1024, le=1024*1024*1024)
    allowed_extensions: list[str] = Field(..., description="允许的文件扩展名")

class SystemSettings(BaseModel):
    """系统设置"""
    upload: UploadSettings
    debug: bool
    project_name: str

class UpdateUploadSettingsRequest(BaseModel):
    """更新上传设置请求"""
    upload_dir: Optional[str] = Field(None, description="上传目录路径")
    max_file_size: Optional[int] = Field(None, description="最大文件大小（字节）", ge=1024, le=1024*1024*1024)
    allowed_extensions: Optional[list[str]] = Field(None, description="允许的文件扩展名")

# ========== API Endpoints ==========

@router.get("/upload")
async def get_upload_settings():
    """
    获取文件上传设置
    
    Returns:
        当前的上传目录、最大文件大小、允许的扩展名
    """
    settings = get_settings()
    
    return {
        "upload_dir": settings.UPLOAD_DIR,
        "max_file_size": settings.MAX_FILE_SIZE,
        "allowed_extensions": settings.ALLOWED_EXTENSIONS
    }

@router.get("/upload/path-info")
async def get_upload_path_info():
    """
    获取上传路径的详细信息
    
    Returns:
        配置的路径、实际绝对路径、目录是否存在、可用空间等
    """
    settings = get_settings()
    upload_path = settings.upload_path
    
    info = {
        "configured_path": settings.UPLOAD_DIR,
        "absolute_path": upload_path,
        "exists": os.path.exists(upload_path),
        "is_absolute": os.path.isabs(settings.UPLOAD_DIR),
        "permissions": {
            "readable": os.access(upload_path, os.R_OK) if os.path.exists(upload_path) else False,
            "writable": os.access(upload_path, os.W_OK) if os.path.exists(upload_path) else False,
        }
    }
    
    # 获取磁盘空间信息
    if os.path.exists(upload_path):
        try:
            stat = os.statvfs(upload_path)
            info["disk_space"] = {
                "total": stat.f_blocks * stat.f_frsize,
                "free": stat.f_bavail * stat.f_frsize,
                "used_percent": round((1 - stat.f_bavail / stat.f_blocks) * 100, 2)
            }
        except Exception as e:
            logger.warning(f"Failed to get disk space info: {e}")
    
    # 统计已上传文件
    if os.path.exists(upload_path):
        try:
            files = os.listdir(upload_path)
            total_size = sum(os.path.getsize(os.path.join(upload_path, f)) 
                           for f in files if os.path.isfile(os.path.join(upload_path, f)))
            info["uploaded_files"] = {
                "count": len([f for f in files if os.path.isfile(os.path.join(upload_path, f))]),
                "total_size": total_size
            }
        except Exception as e:
            logger.warning(f"Failed to get uploaded files info: {e}")
    
    return info

@router.put("/upload")
async def update_upload_settings(request: UpdateUploadSettingsRequest):
    """
    更新文件上传设置
    
    注意：此API仅更新环境变量，需要重启服务才能生效
    生产环境建议直接修改 .env 文件
    
    Args:
        request: 更新请求
        
    Returns:
        更新结果和提示信息
    """
    settings = get_settings()
    updated_fields = []
    
    # 更新 .env 文件
    env_file = ".env"
    if not os.path.exists(env_file):
        raise HTTPException(status_code=404, detail=".env 文件不存在，请先创建")
    
    # 读取当前 .env 内容
    with open(env_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    # 更新配置
    new_lines = []
    for line in lines:
        if request.upload_dir and line.startswith('UPLOAD_DIR='):
            new_lines.append(f'UPLOAD_DIR={request.upload_dir}\n')
            updated_fields.append('upload_dir')
        elif request.max_file_size and line.startswith('MAX_FILE_SIZE='):
            new_lines.append(f'MAX_FILE_SIZE={request.max_file_size}\n')
            updated_fields.append('max_file_size')
        elif request.allowed_extensions and line.startswith('ALLOWED_EXTENSIONS='):
            exts = ','.join(request.allowed_extensions)
            new_lines.append(f'ALLOWED_EXTENSIONS={exts}\n')
            updated_fields.append('allowed_extensions')
        else:
            new_lines.append(line)
    
    # 如果字段不存在，追加到文件末尾
    if request.upload_dir and 'upload_dir' not in updated_fields:
        new_lines.append(f'UPLOAD_DIR={request.upload_dir}\n')
        updated_fields.append('upload_dir')
    if request.max_file_size and 'max_file_size' not in updated_fields:
        new_lines.append(f'MAX_FILE_SIZE={request.max_file_size}\n')
        updated_fields.append('max_file_size')
    if request.allowed_extensions and 'allowed_extensions' not in updated_fields:
        exts = ','.join(request.allowed_extensions)
        new_lines.append(f'ALLOWED_EXTENSIONS={exts}\n')
        updated_fields.append('allowed_extensions')
    
    # 写回文件
    with open(env_file, 'w', encoding='utf-8') as f:
        f.writelines(new_lines)
    
    logger.info(f"Updated settings: {updated_fields}")
    
    return {
        "status": "success",
        "message": "配置已更新，请重启服务使其生效",
        "updated_fields": updated_fields,
        "restart_required": True,
        "current_values": {
            "upload_dir": settings.UPLOAD_DIR,
            "absolute_path": settings.upload_path
        }
    }

@router.post("/upload/test-path")
async def test_upload_path(path: str):
    """
    测试指定路径是否可用于文件上传
    
    Args:
        path: 要测试的路径
        
    Returns:
        路径是否可用、错误信息等
    """
    result = {
        "path": path,
        "valid": False,
        "errors": [],
        "warnings": []
    }
    
    # 检查路径格式
    if not path:
        result["errors"].append("路径不能为空")
        return result
    
    # 转换为绝对路径
    if not os.path.isabs(path):
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        abs_path = os.path.join(base_dir, path)
        result["absolute_path"] = abs_path
    else:
        abs_path = path
        result["absolute_path"] = abs_path
    
    # 检查目录是否存在
    if not os.path.exists(abs_path):
        result["warnings"].append("目录不存在，将自动创建")
        try:
            os.makedirs(abs_path, exist_ok=True)
            result["warnings"].append("✓ 目录创建成功")
        except Exception as e:
            result["errors"].append(f"无法创建目录: {str(e)}")
            return result
    
    # 检查权限
    if not os.access(abs_path, os.R_OK):
        result["errors"].append("目录不可读")
    if not os.access(abs_path, os.W_OK):
        result["errors"].append("目录不可写")
    
    # 检查磁盘空间
    try:
        stat = os.statvfs(abs_path)
        free_space = stat.f_bavail * stat.f_frsize
        if free_space < 100 * 1024 * 1024:  # 小于100MB
            result["warnings"].append(f"可用空间不足: {free_space / 1024 / 1024:.2f} MB")
        result["disk_info"] = {
            "free_mb": free_space / 1024 / 1024,
            "total_mb": stat.f_blocks * stat.f_frsize / 1024 / 1024
        }
    except Exception as e:
        result["warnings"].append(f"无法获取磁盘空间信息: {str(e)}")
    
    # 判断是否可用
    result["valid"] = len(result["errors"]) == 0
    
    return result
