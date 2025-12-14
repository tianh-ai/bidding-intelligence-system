"""
图片访问API - 提供图片查询和下载接口
"""

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from typing import List, Dict, Optional
from pathlib import Path
import os

from core.logger import logger
from database import db

router = APIRouter()


@router.get("/images/stats")
async def get_image_stats() -> Dict:
    """
    获取图片统计信息
    
    Returns:
        {
            'total_images': 1000,
            'total_size': 1234567890,
            'by_year': {
                '2025': {'count': 500, 'size': 600000000},
                '2024': {'count': 300, 'size': 400000000},
                ...
            },
            'by_format': {
                'PNG': 600,
                'JPEG': 400
            }
        }
    """
    try:
        # 总数和总大小
        total_stats = db.query_one(
            "SELECT COUNT(*) as total, SUM(size) as total_size FROM extracted_images"
        )
        
        total_images = total_stats['total'] if total_stats else 0
        total_size = total_stats['total_size'] if total_stats and total_stats['total_size'] else 0
        
        # 按年份统计
        year_stats = db.query(
            """
            SELECT 
                EXTRACT(YEAR FROM extracted_at) as year,
                COUNT(*) as count,
                SUM(size) as size
            FROM extracted_images
            GROUP BY EXTRACT(YEAR FROM extracted_at)
            ORDER BY year DESC
            """
        )
        
        by_year = {}
        for stat in year_stats:
            year = int(stat['year']) if stat['year'] else 0
            by_year[str(year)] = {
                'count': stat['count'],
                'size': stat['size'] or 0
            }
        
        # 按格式统计
        format_stats = db.query(
            """
            SELECT format, COUNT(*) as count
            FROM extracted_images
            GROUP BY format
            ORDER BY count DESC
            """
        )
        
        by_format = {}
        for stat in format_stats:
            by_format[stat['format']] = stat['count']
        
        return {
            'total_images': total_images,
            'total_size': total_size,
            'by_year': by_year,
            'by_format': by_format
        }
        
    except Exception as e:
        logger.error(f"获取图片统计失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取统计失败: {str(e)}")


@router.get("/images/{file_id}")
async def get_file_images(file_id: str) -> Dict:
    """
    获取指定文件的所有图片
    
    Args:
        file_id: 文件ID
        
    Returns:
        {
            'file_id': 'xxx',
            'image_count': 10,
            'images': [
                {
                    'id': 'uuid',
                    'image_number': 1,
                    'page_number': 2,
                    'format': 'PNG',
                    'size': 123456,
                    'width': 800,
                    'height': 600,
                    'hash': 'abc123',
                    'extracted_at': '2025-01-01 10:00:00'
                },
                ...
            ]
        }
    """
    try:
        images = db.query(
            """
            SELECT 
                id, image_path, image_number, page_number,
                format, size, width, height, hash, extracted_at
            FROM extracted_images
            WHERE file_id = %s
            ORDER BY image_number ASC
            """,
            (file_id,)
        )
        
        if not images:
            return {
                'file_id': file_id,
                'image_count': 0,
                'images': []
            }
        
        # 格式化返回数据
        formatted_images = []
        for img in images:
            formatted_images.append({
                'id': str(img['id']),
                'image_number': img['image_number'],
                'page_number': img.get('page_number'),
                'format': img['format'],
                'size': img['size'],
                'width': img['width'],
                'height': img['height'],
                'hash': img['hash'],
                'extracted_at': str(img['extracted_at']),
                'download_url': f"/api/images/download/{img['id']}"
            })
        
        return {
            'file_id': file_id,
            'image_count': len(formatted_images),
            'images': formatted_images
        }
        
    except Exception as e:
        logger.error(f"获取文件图片失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取图片失败: {str(e)}")


@router.get("/images/year/{year}")
async def get_year_images(
    year: int,
    limit: int = 100,
    offset: int = 0
) -> Dict:
    """
    获取指定年份的所有图片
    
    Args:
        year: 年份
        limit: 返回数量限制
        offset: 偏移量
        
    Returns:
        {
            'year': 2025,
            'total': 500,
            'limit': 100,
            'offset': 0,
            'images': [...]
        }
    """
    try:
        # 获取总数
        count_result = db.query_one(
            """
            SELECT COUNT(*) as total
            FROM extracted_images
            WHERE image_path LIKE %s
            """,
            (f"%/images/{year}/%",)
        )
        total = count_result['total'] if count_result else 0
        
        # 获取图片列表
        images = db.query(
            """
            SELECT 
                id, file_id, image_path, image_number, page_number,
                format, size, width, height, hash, extracted_at
            FROM extracted_images
            WHERE image_path LIKE %s
            ORDER BY extracted_at DESC
            LIMIT %s OFFSET %s
            """,
            (f"%/images/{year}/%", limit, offset)
        )
        
        formatted_images = []
        for img in images:
            formatted_images.append({
                'id': str(img['id']),
                'file_id': str(img['file_id']),
                'image_number': img['image_number'],
                'page_number': img.get('page_number'),
                'format': img['format'],
                'size': img['size'],
                'width': img['width'],
                'height': img['height'],
                'hash': img['hash'],
                'extracted_at': str(img['extracted_at']),
                'download_url': f"/api/images/download/{img['id']}"
            })
        
        return {
            'year': year,
            'total': total,
            'limit': limit,
            'offset': offset,
            'images': formatted_images
        }
        
    except Exception as e:
        logger.error(f"获取年份图片失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取图片失败: {str(e)}")


@router.get("/images/download/{image_id}")
async def download_image(image_id: str):
    """
    下载指定图片
    
    Args:
        image_id: 图片ID
        
    Returns:
        图片文件
    """
    try:
        # 从数据库获取图片信息
        image = db.query_one(
            "SELECT image_path, format FROM extracted_images WHERE id = %s",
            (image_id,)
        )
        
        if not image:
            raise HTTPException(status_code=404, detail="图片不存在")
        
        image_path = image['image_path']
        
        # 检查文件是否存在
        if not os.path.exists(image_path):
            logger.error(f"图片文件不存在: {image_path}")
            raise HTTPException(status_code=404, detail="图片文件不存在")
        
        # 返回文件
        file_format = image['format'].lower()
        media_type = f"image/{file_format}"
        if file_format == 'jpg':
            media_type = "image/jpeg"
        
        return FileResponse(
            path=image_path,
            media_type=media_type,
            filename=os.path.basename(image_path)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"下载图片失败: {e}")
        raise HTTPException(status_code=500, detail=f"下载失败: {str(e)}")


@router.delete("/images/{file_id}")
async def delete_file_images(file_id: str) -> Dict:
    """
    删除指定文件的所有图片（物理文件+数据库记录）
    
    Args:
        file_id: 文件ID
        
    Returns:
        {'deleted_count': 10, 'message': '已删除10张图片'}
    """
    try:
        # 获取所有图片路径
        images = db.query(
            "SELECT id, image_path FROM extracted_images WHERE file_id = %s",
            (file_id,)
        )
        
        if not images:
            return {'deleted_count': 0, 'message': '没有找到图片'}
        
        deleted_count = 0
        
        # 删除物理文件
        for img in images:
            image_path = img['image_path']
            if os.path.exists(image_path):
                try:
                    os.remove(image_path)
                    deleted_count += 1
                    logger.info(f"删除图片文件: {image_path}")
                except Exception as e:
                    logger.warning(f"删除图片文件失败 {image_path}: {e}")
        
        # 删除目录（如果为空）
        if images:
            first_image_path = Path(images[0]['image_path'])
            file_dir = first_image_path.parent
            try:
                if file_dir.exists() and not any(file_dir.iterdir()):
                    file_dir.rmdir()
                    logger.info(f"删除空目录: {file_dir}")
            except Exception as e:
                logger.warning(f"删除目录失败 {file_dir}: {e}")
        
        # 删除数据库记录
        db.execute(
            "DELETE FROM extracted_images WHERE file_id = %s",
            (file_id,)
        )
        
        return {
            'deleted_count': deleted_count,
            'message': f'已删除 {deleted_count} 张图片'
        }
        
    except Exception as e:
        logger.error(f"删除图片失败: {e}")
        raise HTTPException(status_code=500, detail=f"删除失败: {str(e)}")
