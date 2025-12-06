"""
文档智能配对引擎 - 使用LLM自动识别和配对招标文件与投标文件

功能：
1. 批量上传文件后，自动识别招标文件和投标文件
2. 使用LLM分析文档结构，提取章节目录
3. 自动匹配同一项目的招标-投标文件对
4. 建立章节级别的对应关系
5. 创建结构化存储目录
"""

import os
import json
from pathlib import Path
from typing import List, Dict, Optional, Tuple, Any
from dataclasses import dataclass, asdict
from datetime import datetime
from enum import Enum

from core.logger import logger
from core.llm_router import get_llm_router, TaskType


class DocumentType(Enum):
    """文档类型"""
    TENDER = "tender"  # 招标文件
    PROPOSAL = "proposal"  # 投标文件
    UNKNOWN = "unknown"  # 未知类型


@dataclass
class Chapter:
    """章节信息"""
    chapter_id: str  # 章节ID，如 "1", "1.1", "2.3"
    title: str  # 章节标题
    page_start: Optional[int] = None  # 起始页码
    page_end: Optional[int] = None  # 结束页码
    content_summary: Optional[str] = None  # 内容摘要
    keywords: List[str] = None  # 关键词
    
    def __post_init__(self):
        if self.keywords is None:
            self.keywords = []


@dataclass
class DocumentInfo:
    """文档信息"""
    file_path: str  # 文件路径
    file_name: str  # 文件名
    document_type: DocumentType  # 文档类型
    project_name: Optional[str] = None  # 项目名称
    project_code: Optional[str] = None  # 项目编号
    chapters: List[Chapter] = None  # 章节列表
    total_pages: Optional[int] = None  # 总页数
    upload_time: Optional[str] = None  # 上传时间
    metadata: Dict[str, Any] = None  # 其他元数据
    
    def __post_init__(self):
        if self.chapters is None:
            self.chapters = []
        if self.metadata is None:
            self.metadata = {}
        if self.upload_time is None:
            self.upload_time = datetime.now().isoformat()


@dataclass
class ChapterPair:
    """章节配对关系"""
    tender_chapter: Chapter  # 招标文件章节
    proposal_chapter: Chapter  # 投标文件章节
    similarity_score: float  # 相似度分数 0-100
    match_reason: str  # 匹配原因
    is_verified: bool = False  # 是否人工验证


@dataclass
class DocumentPair:
    """文档配对关系"""
    pair_id: str  # 配对ID
    tender_doc: DocumentInfo  # 招标文件
    proposal_doc: DocumentInfo  # 投标文件
    chapter_pairs: List[ChapterPair]  # 章节配对列表
    overall_similarity: float  # 整体相似度
    match_confidence: float  # 匹配置信度
    created_time: str  # 创建时间
    storage_path: str  # 存储路径
    
    def __post_init__(self):
        if not self.created_time:
            self.created_time = datetime.now().isoformat()


class DocumentMatcher:
    """文档智能配对引擎"""
    
    def __init__(self, storage_root: str = "data/matched_documents"):
        """
        初始化文档配对引擎
        
        Args:
            storage_root: 配对文档的存储根目录
        """
        self.llm_router = get_llm_router()
        self.storage_root = Path(storage_root)
        self.storage_root.mkdir(parents=True, exist_ok=True)
        
        logger.info("DocumentMatcher initialized", extra={
            "storage_root": str(self.storage_root)
        })
    
    async def classify_document(self, file_path: str) -> DocumentType:
        """
        使用LLM识别文档类型
        
        Args:
            file_path: 文件路径
            
        Returns:
            文档类型
        """
        # 读取文件前几页内容用于分类
        file_name = Path(file_path).name
        
        # 简单的规则检测
        if any(keyword in file_name.lower() for keyword in ['招标', 'tender', '需求']):
            return DocumentType.TENDER
        elif any(keyword in file_name.lower() for keyword in ['投标', 'proposal', '方案']):
            return DocumentType.PROPOSAL
        
        # TODO: 使用LLM进行更精确的分类
        # 这里可以提取文档前1000字，让LLM判断
        prompt = f"""
请判断以下文件是招标文件还是投标文件：

文件名：{file_name}

请仅返回以下之一：
- TENDER（如果是招标文件）
- PROPOSAL（如果是投标文件）
- UNKNOWN（无法判断）
"""
        
        try:
            result = await self.llm_router.generate_text(
                prompt=prompt,
                task_type=TaskType.EXTRACTION,
                max_tokens=10
            )
            
            result = result.strip().upper()
            if "TENDER" in result:
                return DocumentType.TENDER
            elif "PROPOSAL" in result:
                return DocumentType.PROPOSAL
            else:
                return DocumentType.UNKNOWN
                
        except Exception as e:
            logger.warning(f"LLM classification failed, using rule-based: {e}")
            return DocumentType.UNKNOWN
    
    async def extract_document_structure(
        self,
        file_path: str,
        document_type: DocumentType
    ) -> DocumentInfo:
        """
        使用LLM提取文档结构（项目名、章节等）
        
        Args:
            file_path: 文件路径
            document_type: 文档类型
            
        Returns:
            文档信息
        """
        file_name = Path(file_path).name
        
        # 构造提示词
        prompt = f"""
请分析以下{document_type.value}文档，提取结构化信息：

文件名：{file_name}

请以JSON格式返回以下信息：
{{
  "project_name": "项目名称",
  "project_code": "项目编号或招标编号",
  "total_pages": 页数（数字）,
  "chapters": [
    {{
      "chapter_id": "章节编号（如1, 1.1, 2.3）",
      "title": "章节标题",
      "page_start": 起始页码,
      "page_end": 结束页码,
      "content_summary": "简要描述章节内容（20字以内）",
      "keywords": ["关键词1", "关键词2"]
    }}
  ]
}}

注意：
1. 如果无法确定某个字段，设为null
2. chapters至少提取一级章节
3. 返回纯JSON，不要其他说明
"""
        
        try:
            # 调用LLM提取结构
            result = await self.llm_router.generate_text(
                prompt=prompt,
                system_prompt="你是专业的文档结构分析助手，擅长提取招投标文档的结构化信息。",
                task_type=TaskType.EXTRACTION,
                max_tokens=2000
            )
            
            # 解析JSON
            # 去除可能的markdown代码块标记
            result = result.strip()
            if result.startswith("```"):
                result = result.split("```")[1]
                if result.startswith("json"):
                    result = result[4:]
            
            data = json.loads(result)
            
            # 构造DocumentInfo
            chapters = []
            for ch_data in data.get("chapters", []):
                chapter = Chapter(
                    chapter_id=ch_data.get("chapter_id", ""),
                    title=ch_data.get("title", ""),
                    page_start=ch_data.get("page_start"),
                    page_end=ch_data.get("page_end"),
                    content_summary=ch_data.get("content_summary"),
                    keywords=ch_data.get("keywords", [])
                )
                chapters.append(chapter)
            
            doc_info = DocumentInfo(
                file_path=file_path,
                file_name=file_name,
                document_type=document_type,
                project_name=data.get("project_name"),
                project_code=data.get("project_code"),
                chapters=chapters,
                total_pages=data.get("total_pages")
            )
            
            logger.info(f"Extracted document structure: {file_name}", extra={
                "project_name": doc_info.project_name,
                "chapters_count": len(chapters)
            })
            
            return doc_info
            
        except Exception as e:
            logger.error(f"Failed to extract document structure: {e}", exc_info=True)
            
            # 降级：返回基本信息
            return DocumentInfo(
                file_path=file_path,
                file_name=file_name,
                document_type=document_type
            )
    
    async def match_documents(
        self,
        tender_docs: List[DocumentInfo],
        proposal_docs: List[DocumentInfo]
    ) -> List[DocumentPair]:
        """
        自动匹配招标文件和投标文件
        
        Args:
            tender_docs: 招标文件列表
            proposal_docs: 投标文件列表
            
        Returns:
            文档配对列表
        """
        pairs = []
        
        for tender in tender_docs:
            # 为每个招标文件找到最匹配的投标文件
            best_match = None
            best_score = 0
            
            for proposal in proposal_docs:
                score = await self._calculate_document_similarity(tender, proposal)
                
                if score > best_score:
                    best_score = score
                    best_match = proposal
            
            if best_match and best_score > 60:  # 相似度阈值
                # 创建配对
                pair = await self._create_document_pair(tender, best_match, best_score)
                pairs.append(pair)
                
                logger.info(f"Matched documents", extra={
                    "tender": tender.file_name,
                    "proposal": best_match.file_name,
                    "similarity": best_score
                })
        
        return pairs
    
    async def _calculate_document_similarity(
        self,
        doc1: DocumentInfo,
        doc2: DocumentInfo
    ) -> float:
        """
        使用LLM计算两个文档的相似度
        
        Args:
            doc1: 文档1
            doc2: 文档2
            
        Returns:
            相似度分数 0-100
        """
        # 构造比较提示词
        prompt = f"""
请判断以下两个文档是否属于同一个项目：

文档1（招标文件）：
- 文件名：{doc1.file_name}
- 项目名：{doc1.project_name or '未知'}
- 项目编号：{doc1.project_code or '未知'}

文档2（投标文件）：
- 文件名：{doc2.file_name}
- 项目名：{doc2.project_name or '未知'}
- 项目编号：{doc2.project_code or '未知'}

请给出0-100的相似度评分，分数越高表示越可能是同一项目。
仅返回数字，如：85
"""
        
        try:
            result = await self.llm_router.generate_text(
                prompt=prompt,
                task_type=TaskType.COMPARISON,
                max_tokens=10
            )
            
            # 提取数字
            score = float(''.join(filter(str.isdigit, result)))
            return min(max(score, 0), 100)
            
        except Exception as e:
            logger.warning(f"LLM similarity calculation failed: {e}")
            
            # 降级：基于规则的相似度
            score = 0
            
            # 项目编号匹配
            if doc1.project_code and doc2.project_code:
                if doc1.project_code == doc2.project_code:
                    score += 50
            
            # 项目名称匹配
            if doc1.project_name and doc2.project_name:
                name1 = doc1.project_name.lower()
                name2 = doc2.project_name.lower()
                if name1 in name2 or name2 in name1:
                    score += 30
            
            # 文件名相似度
            name1 = Path(doc1.file_name).stem.lower()
            name2 = Path(doc2.file_name).stem.lower()
            common_words = set(name1.split()) & set(name2.split())
            if common_words:
                score += len(common_words) * 5
            
            return min(score, 100)
    
    async def _create_document_pair(
        self,
        tender: DocumentInfo,
        proposal: DocumentInfo,
        similarity: float
    ) -> DocumentPair:
        """
        创建文档配对并匹配章节
        
        Args:
            tender: 招标文件
            proposal: 投标文件
            similarity: 整体相似度
            
        Returns:
            文档配对对象
        """
        # 生成配对ID
        pair_id = f"pair_{datetime.now().strftime('%Y%m%d%H%M%S')}_{tender.project_code or 'unknown'}"
        
        # 匹配章节
        chapter_pairs = await self._match_chapters(tender.chapters, proposal.chapters)
        
        # 计算匹配置信度
        confidence = self._calculate_confidence(similarity, chapter_pairs)
        
        # 创建存储路径
        storage_path = self._create_storage_structure(pair_id, tender, proposal)
        
        pair = DocumentPair(
            pair_id=pair_id,
            tender_doc=tender,
            proposal_doc=proposal,
            chapter_pairs=chapter_pairs,
            overall_similarity=similarity,
            match_confidence=confidence,
            created_time=datetime.now().isoformat(),
            storage_path=storage_path
        )
        
        # 保存配对信息
        await self._save_pair_metadata(pair)
        
        return pair
    
    async def _match_chapters(
        self,
        tender_chapters: List[Chapter],
        proposal_chapters: List[Chapter]
    ) -> List[ChapterPair]:
        """
        使用LLM匹配章节
        
        Args:
            tender_chapters: 招标文件章节列表
            proposal_chapters: 投标文件章节列表
            
        Returns:
            章节配对列表
        """
        if not tender_chapters or not proposal_chapters:
            return []
        
        chapter_pairs = []
        
        # 构造批量匹配提示词
        tender_info = "\n".join([
            f"{ch.chapter_id}. {ch.title}" for ch in tender_chapters
        ])
        
        proposal_info = "\n".join([
            f"{ch.chapter_id}. {ch.title}" for ch in proposal_chapters
        ])
        
        prompt = f"""
请匹配以下招标文件和投标文件的章节对应关系：

招标文件章节：
{tender_info}

投标文件章节：
{proposal_info}

请以JSON数组格式返回匹配结果，每个匹配包含：
[
  {{
    "tender_chapter_id": "招标章节ID",
    "proposal_chapter_id": "投标章节ID",
    "similarity_score": 相似度(0-100),
    "match_reason": "匹配原因（简短说明）"
  }}
]

注意：
1. 只返回相似度>70的配对
2. 一个章节可能对应多个章节
3. 返回纯JSON数组
"""
        
        try:
            result = await self.llm_router.generate_text(
                prompt=prompt,
                system_prompt="你是文档结构分析专家，擅长识别招投标文档的章节对应关系。",
                task_type=TaskType.COMPARISON,
                max_tokens=1500
            )
            
            # 解析JSON
            result = result.strip()
            if result.startswith("```"):
                result = result.split("```")[1]
                if result.startswith("json"):
                    result = result[4:]
            
            matches = json.loads(result)
            
            # 创建章节配对
            tender_dict = {ch.chapter_id: ch for ch in tender_chapters}
            proposal_dict = {ch.chapter_id: ch for ch in proposal_chapters}
            
            for match in matches:
                tender_id = match.get("tender_chapter_id")
                proposal_id = match.get("proposal_chapter_id")
                
                if tender_id in tender_dict and proposal_id in proposal_dict:
                    pair = ChapterPair(
                        tender_chapter=tender_dict[tender_id],
                        proposal_chapter=proposal_dict[proposal_id],
                        similarity_score=match.get("similarity_score", 0),
                        match_reason=match.get("match_reason", "")
                    )
                    chapter_pairs.append(pair)
            
            logger.info(f"Matched {len(chapter_pairs)} chapter pairs")
            
        except Exception as e:
            logger.error(f"Chapter matching failed: {e}", exc_info=True)
            
            # 降级：基于标题相似度的简单匹配
            for t_ch in tender_chapters:
                for p_ch in proposal_chapters:
                    if self._simple_title_similarity(t_ch.title, p_ch.title) > 0.7:
                        pair = ChapterPair(
                            tender_chapter=t_ch,
                            proposal_chapter=p_ch,
                            similarity_score=80,
                            match_reason="标题相似"
                        )
                        chapter_pairs.append(pair)
        
        return chapter_pairs
    
    def _simple_title_similarity(self, title1: str, title2: str) -> float:
        """简单的标题相似度计算"""
        words1 = set(title1.lower().split())
        words2 = set(title2.lower().split())
        
        if not words1 or not words2:
            return 0.0
        
        intersection = words1 & words2
        union = words1 | words2
        
        return len(intersection) / len(union)
    
    def _calculate_confidence(
        self,
        similarity: float,
        chapter_pairs: List[ChapterPair]
    ) -> float:
        """计算匹配置信度"""
        # 基础置信度来自整体相似度
        confidence = similarity * 0.6
        
        # 章节匹配数量加分
        if chapter_pairs:
            avg_chapter_similarity = sum(
                pair.similarity_score for pair in chapter_pairs
            ) / len(chapter_pairs)
            confidence += avg_chapter_similarity * 0.4
        
        return min(confidence, 100)
    
    def _create_storage_structure(
        self,
        pair_id: str,
        tender: DocumentInfo,
        proposal: DocumentInfo
    ) -> str:
        """
        创建存储目录结构
        
        Args:
            pair_id: 配对ID
            tender: 招标文件
            proposal: 投标文件
            
        Returns:
            存储路径
        """
        # 创建配对专属目录
        pair_dir = self.storage_root / pair_id
        pair_dir.mkdir(parents=True, exist_ok=True)
        
        # 创建子目录
        (pair_dir / "tender").mkdir(exist_ok=True)
        (pair_dir / "proposal").mkdir(exist_ok=True)
        (pair_dir / "parsed_data").mkdir(exist_ok=True)
        (pair_dir / "knowledge_base").mkdir(exist_ok=True)
        (pair_dir / "logic_db").mkdir(exist_ok=True)
        
        logger.info(f"Created storage structure: {pair_dir}")
        
        return str(pair_dir)
    
    async def _save_pair_metadata(self, pair: DocumentPair):
        """保存配对元数据到JSON文件"""
        metadata_file = Path(pair.storage_path) / "pair_metadata.json"
        
        # 转换为可序列化的字典
        metadata = {
            "pair_id": pair.pair_id,
            "tender_doc": {
                "file_name": pair.tender_doc.file_name,
                "file_path": pair.tender_doc.file_path,
                "project_name": pair.tender_doc.project_name,
                "project_code": pair.tender_doc.project_code,
                "chapters": [asdict(ch) for ch in pair.tender_doc.chapters]
            },
            "proposal_doc": {
                "file_name": pair.proposal_doc.file_name,
                "file_path": pair.proposal_doc.file_path,
                "project_name": pair.proposal_doc.project_name,
                "project_code": pair.proposal_doc.project_code,
                "chapters": [asdict(ch) for ch in pair.proposal_doc.chapters]
            },
            "chapter_pairs": [
                {
                    "tender_chapter": asdict(cp.tender_chapter),
                    "proposal_chapter": asdict(cp.proposal_chapter),
                    "similarity_score": cp.similarity_score,
                    "match_reason": cp.match_reason,
                    "is_verified": cp.is_verified
                }
                for cp in pair.chapter_pairs
            ],
            "overall_similarity": pair.overall_similarity,
            "match_confidence": pair.match_confidence,
            "created_time": pair.created_time
        }
        
        with open(metadata_file, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, ensure_ascii=False, indent=2)
        
        logger.info(f"Saved pair metadata: {metadata_file}")
    
    async def batch_process_files(
        self,
        file_paths: List[str]
    ) -> List[DocumentPair]:
        """
        批量处理文件：分类、提取结构、配对
        
        Args:
            file_paths: 文件路径列表
            
        Returns:
            文档配对列表
        """
        logger.info(f"Starting batch processing of {len(file_paths)} files")
        
        # Step 1: 分类文档
        tender_docs = []
        proposal_docs = []
        
        for file_path in file_paths:
            doc_type = await self.classify_document(file_path)
            
            if doc_type == DocumentType.UNKNOWN:
                logger.warning(f"Unknown document type: {file_path}")
                continue
            
            # Step 2: 提取文档结构
            doc_info = await self.extract_document_structure(file_path, doc_type)
            
            if doc_type == DocumentType.TENDER:
                tender_docs.append(doc_info)
            else:
                proposal_docs.append(doc_info)
        
        logger.info(f"Classified: {len(tender_docs)} tenders, {len(proposal_docs)} proposals")
        
        # Step 3: 配对文档
        pairs = await self.match_documents(tender_docs, proposal_docs)
        
        logger.info(f"Created {len(pairs)} document pairs")
        
        return pairs
