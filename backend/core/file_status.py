"""
文件状态枚举定义
定义文件在生命周期中的各个状态
"""
from enum import Enum


class FileStatus(str, Enum):
    """文件处理状态"""
    
    # 阶段1: 临时上传
    UPLOADED = "uploaded"              # 已上传到temp/
    UPLOAD_FAILED = "upload_failed"    # 上传失败
    
    # 阶段2: 解析处理
    PARSING = "parsing"                # 正在解析
    PARSED = "parsed"                  # 解析完成
    PARSE_FAILED = "parse_failed"      # 解析失败
    
    # 阶段3: 归档存储
    ARCHIVING = "archiving"            # 正在归档
    ARCHIVED = "archived"              # 已归档
    ARCHIVE_FAILED = "archive_failed"  # 归档失败
    
    # 阶段4: 知识库索引
    INDEXING = "indexing"              # 正在建立索引
    INDEXED = "indexed"                # 已建立索引（最终状态）
    INDEX_FAILED = "index_failed"      # 索引失败
    
    # 特殊状态
    DUPLICATE = "duplicate"            # 重复文件（等待用户决策）
    DELETED = "deleted"                # 已删除（软删除）


class DuplicateAction(str, Enum):
    """重复文件处理策略"""
    
    OVERWRITE = "overwrite"   # 覆盖原文件
    UPDATE = "update"         # 更新（保留原文件，创建新版本）
    SKIP = "skip"            # 跳过（放弃上传）


class FileCategory(str, Enum):
    """文档分类"""
    
    TENDER = "tender"         # 招标文件
    PROPOSAL = "proposal"     # 投标文件
    REFERENCE = "reference"   # 参考资料
    CONTRACT = "contract"     # 合同文件
    REPORT = "report"        # 报告文档
    OTHER = "other"          # 其他
