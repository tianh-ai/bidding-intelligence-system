"""
CacheManager Skill - 缓存管理Skill

基于core/cache.py的CacheManager，提供Skill标准接口：
1. 缓存CRUD操作
2. 批量操作
3. 模式匹配删除
4. 统计信息
5. 健康检查

版本：1.0.0
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field
from datetime import datetime
from core.cache import cache, CacheManager as CoreCacheManager
from core.logger import logger


class CacheOperation(BaseModel):
    """缓存操作模型"""
    operation: str = Field(..., description="操作类型: get, set, delete, clear, stats")
    key: Optional[str] = Field(None, description="缓存键")
    value: Optional[Any] = Field(None, description="缓存值")
    ttl: Optional[int] = Field(None, description="过期时间（秒）")
    pattern: Optional[str] = Field(None, description="键模式（用于批量删除）")


class CacheResult(BaseModel):
    """缓存操作结果"""
    success: bool
    operation: str
    key: Optional[str] = None
    value: Optional[Any] = None
    stats: Optional[Dict] = None
    error: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class CacheManagerSkill:
    """缓存管理Skill"""
    
    def __init__(self, config: Optional[Dict] = None):
        """初始化"""
        self.config = config or {}
        self.cache = cache  # 使用全局cache实例
        logger.info("CacheManagerSkill initialized")
    
    def execute(self, input_data: CacheOperation) -> CacheResult:
        """执行缓存操作"""
        try:
            operation_map = {
                'get': self._get,
                'set': self._set,
                'delete': self._delete,
                'clear': self._clear,
                'stats': self._stats,
            }
            
            handler = operation_map.get(input_data.operation)
            if not handler:
                raise ValueError(f"不支持的操作: {input_data.operation}")
            
            return handler(input_data)
            
        except Exception as e:
            logger.error(f"缓存操作失败: {e}")
            return CacheResult(
                success=False,
                operation=input_data.operation,
                error=str(e)
            )
    
    def _get(self, input_data: CacheOperation) -> CacheResult:
        """获取缓存"""
        value = self.cache.get(input_data.key)
        return CacheResult(
            success=value is not None,
            operation='get',
            key=input_data.key,
            value=value,
            metadata={"timestamp": datetime.now().isoformat()}
        )
    
    def _set(self, input_data: CacheOperation) -> CacheResult:
        """设置缓存"""
        success = self.cache.set(input_data.key, input_data.value, input_data.ttl)
        return CacheResult(
            success=success,
            operation='set',
            key=input_data.key,
            value=input_data.value,
            metadata={"ttl": input_data.ttl, "timestamp": datetime.now().isoformat()}
        )
    
    def _delete(self, input_data: CacheOperation) -> CacheResult:
        """删除缓存"""
        pattern = input_data.pattern or input_data.key
        count = self.cache.delete(pattern)
        return CacheResult(
            success=count > 0,
            operation='delete',
            key=pattern,
            metadata={"deleted_count": count}
        )
    
    def _clear(self, input_data: CacheOperation) -> CacheResult:
        """清空所有缓存"""
        success = self.cache.clear_all()
        return CacheResult(
            success=success,
            operation='clear',
            metadata={"warning": "所有缓存已清空"}
        )
    
    def _stats(self, input_data: CacheOperation) -> CacheResult:
        """获取缓存统计"""
        stats = self.cache.get_stats()
        return CacheResult(
            success=True,
            operation='stats',
            stats=stats
        )
    
    def validate(self, input_data: CacheOperation) -> bool:
        """验证输入"""
        if input_data.operation in ['get', 'delete'] and not input_data.key and not input_data.pattern:
            return False
        if input_data.operation == 'set' and (not input_data.key or input_data.value is None):
            return False
        return True
    
    def get_metadata(self) -> Dict[str, Any]:
        """获取Skill元数据"""
        return {
            "name": "CacheManagerSkill",
            "version": "1.0.0",
            "description": "Redis缓存管理Skill",
            "operations": ["get", "set", "delete", "clear", "stats"],
            "cache_status": "available" if self.cache.is_available() else "unavailable"
        }


# 便捷函数
def manage_cache(operation: str, **kwargs) -> CacheResult:
    """便捷的缓存管理函数"""
    skill = CacheManagerSkill()
    input_data = CacheOperation(operation=operation, **kwargs)
    return skill.execute(input_data)


if __name__ == '__main__':
    print("=== CacheManager Skill 测试 ===\n")
    
    # 测试设置缓存
    print("1. 设置缓存:")
    result = manage_cache('set', key='test:key1', value={'data': 'Hello'}, ttl=60)
    print(f"   Success: {result.success}, Key: {result.key}\n")
    
    # 测试获取缓存
    print("2. 获取缓存:")
    result = manage_cache('get', key='test:key1')
    print(f"   Success: {result.success}, Value: {result.value}\n")
    
    # 测试统计
    print("3. 缓存统计:")
    result = manage_cache('stats')
    print(f"   Stats: {result.stats}\n")
    
    # 测试删除
    print("4. 删除缓存:")
    result = manage_cache('delete', pattern='test:*')
    print(f"   Success: {result.success}, Deleted: {result.metadata.get('deleted_count')}\n")
