"""
文档解析引擎 - 解析配对文档并生成知识库和数据库

功能：
1. 解析招标-投标配对文档
2. 提取结构化数据（需求、技术、价格、商务等）
3. 生成知识库（文本片段 + 向量）
4. 生成文件数据库schema
5. 建立章节内容的向量索引
"""

import json
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, asdict
from pathlib import Path
from datetime import datetime

from core.logger import logger
from core.llm_router import get_llm_router, TaskType
from engines.document_matcher import DocumentPair, ChapterPair


@dataclass
class ParsedChapter:
    """解析后的章节数据"""
    chapter_id: str
    chapter_title: str
    
    # 结构化字段
    requirements: List[str]  # 需求列表
    technical_specs: List[Dict[str, Any]]  # 技术规格
    business_terms: List[Dict[str, Any]]  # 商务条款
    evaluation_criteria: List[Dict[str, Any]]  # 评分标准
    
    # 文本内容
    raw_text: str  # 原始文本
    summary: str  # 摘要
    
    # 知识点
    key_points: List[str]  # 关键要点
    constraints: List[str]  # 约束条件
    
    # 向量表示
    embedding: Optional[List[float]] = None  # 向量嵌入


@dataclass
class ParsedDocument:
    """解析后的文档"""
    doc_id: str
    doc_type: str  # "tender" or "proposal"
    project_name: str
    project_code: str
    chapters: List[ParsedChapter]
    metadata: Dict[str, Any]
    parse_time: str
    
    def __post_init__(self):
        if not self.parse_time:
            self.parse_time = datetime.now().isoformat()


@dataclass
class KnowledgeEntry:
    """知识库条目"""
    entry_id: str

    # 来源信息
    source_doc_type: str  # "tender" or "proposal"
    source_chapter_id: str

    # 知识内容
    content_type: str  # "requirement", "technical", "business", "evaluation"
    content: str  # 文本内容
    structured_data: Dict[str, Any]  # 结构化数据

    # 关联关系
    related_entries: List[str]  # 关联的其他条目ID

    # 元数据（无默认值字段必须在前）
    keywords: List[str]
    importance_score: float  # 0-100
    created_time: str

    # 向量表示（有默认值的字段放最后）
    embedding: Optional[List[float]] = None

    def __post_init__(self):
        if not self.created_time:
            self.created_time = datetime.now().isoformat()


@dataclass
class KnowledgeBase:
    """知识库"""
    kb_id: str
    pair_id: str  # 关联的文档配对ID
    entries: List[KnowledgeEntry]
    
    # 统计信息
    total_entries: int
    entry_types: Dict[str, int]  # 各类型条目数量
    
    # 存储路径
    storage_path: str
    created_time: str
    
    def __post_init__(self):
        if not self.created_time:
            self.created_time = datetime.now().isoformat()
        if not self.total_entries:
            self.total_entries = len(self.entries)


class DocumentParser:
    """文档解析引擎"""
    
    def __init__(self):
        """初始化解析引擎"""
        self.llm_router = get_llm_router()
        logger.info("DocumentParser initialized")
    
    async def parse_chapter(
        self,
        chapter_text: str,
        chapter_title: str,
        chapter_id: str,
        doc_type: str
    ) -> ParsedChapter:
        """
        使用LLM解析章节内容
        
        Args:
            chapter_text: 章节原始文本
            chapter_title: 章节标题
            chapter_id: 章节ID
            doc_type: 文档类型 "tender" or "proposal"
            
        Returns:
            解析后的章节数据
        """
        # 构造解析提示词
        prompt = f"""
请深入分析以下{doc_type}文档的章节内容，提取结构化信息：

章节：{chapter_id} - {chapter_title}

内容：
{chapter_text[:2000]}  # 限制长度

请以JSON格式返回：
{{
  "requirements": ["需求1", "需求2"],  # 明确的需求项
  "technical_specs": [  # 技术规格
    {{"item": "CPU", "spec": ">=8核", "mandatory": true}}
  ],
  "business_terms": [  # 商务条款
    {{"term": "付款方式", "value": "分三期", "notes": ""}}
  ],
  "evaluation_criteria": [  # 评分标准
    {{"criterion": "技术方案", "weight": 0.4, "scoring_method": "综合评分"}}
  ],
  "summary": "本章节主要内容概述（50字以内）",
  "key_points": ["要点1", "要点2"],  # 关键要点
  "constraints": ["约束1", "约束2"]  # 约束条件
}}

注意：
1. 提取所有明确的需求和规格
2. 识别硬性约束（must）和软性约束（should）
3. 返回纯JSON
"""
        
        try:
            result = await self.llm_router.generate_text(
                prompt=prompt,
                system_prompt="你是专业的招投标文档分析专家，擅长提取结构化需求和规格。",
                task_type=TaskType.EXTRACTION,
                max_tokens=2000
            )
            
            # 解析JSON
            result = result.strip()
            if result.startswith("```"):
                result = result.split("```")[1]
                if result.startswith("json"):
                    result = result[4:]
            
            data = json.loads(result)
            
            parsed = ParsedChapter(
                chapter_id=chapter_id,
                chapter_title=chapter_title,
                requirements=data.get("requirements", []),
                technical_specs=data.get("technical_specs", []),
                business_terms=data.get("business_terms", []),
                evaluation_criteria=data.get("evaluation_criteria", []),
                raw_text=chapter_text,
                summary=data.get("summary", ""),
                key_points=data.get("key_points", []),
                constraints=data.get("constraints", [])
            )
            
            logger.info(f"Parsed chapter: {chapter_id}", extra={
                "requirements": len(parsed.requirements),
                "technical_specs": len(parsed.technical_specs)
            })
            
            return parsed
            
        except Exception as e:
            logger.error(f"Failed to parse chapter {chapter_id}: {e}", exc_info=True)
            
            # 降级：返回基本信息
            return ParsedChapter(
                chapter_id=chapter_id,
                chapter_title=chapter_title,
                requirements=[],
                technical_specs=[],
                business_terms=[],
                evaluation_criteria=[],
                raw_text=chapter_text,
                summary=chapter_title,
                key_points=[],
                constraints=[]
            )
    
    async def parse_document_pair(
        self,
        pair: DocumentPair
    ) -> tuple[ParsedDocument, ParsedDocument]:
        """
        解析配对文档
        
        Args:
            pair: 文档配对对象
            
        Returns:
            (招标文档解析结果, 投标文档解析结果)
        """
        logger.info(f"Parsing document pair: {pair.pair_id}")
        
        # 解析招标文档
        tender_chapters = []
        for chapter in pair.tender_doc.chapters:
            # TODO: 这里需要实际读取章节内容
            # 现在使用占位文本
            chapter_text = f"[章节内容待读取: {chapter.title}]"
            
            parsed = await self.parse_chapter(
                chapter_text=chapter_text,
                chapter_title=chapter.title,
                chapter_id=chapter.chapter_id,
                doc_type="tender"
            )
            tender_chapters.append(parsed)
        
        tender_doc = ParsedDocument(
            doc_id=f"tender_{pair.pair_id}",
            doc_type="tender",
            project_name=pair.tender_doc.project_name or "Unknown",
            project_code=pair.tender_doc.project_code or "Unknown",
            chapters=tender_chapters,
            metadata={},
            parse_time=datetime.now().isoformat()
        )
        
        # 解析投标文档
        proposal_chapters = []
        for chapter in pair.proposal_doc.chapters:
            chapter_text = f"[章节内容待读取: {chapter.title}]"
            
            parsed = await self.parse_chapter(
                chapter_text=chapter_text,
                chapter_title=chapter.title,
                chapter_id=chapter.chapter_id,
                doc_type="proposal"
            )
            proposal_chapters.append(parsed)
        
        proposal_doc = ParsedDocument(
            doc_id=f"proposal_{pair.pair_id}",
            doc_type="proposal",
            project_name=pair.proposal_doc.project_name or "Unknown",
            project_code=pair.proposal_doc.project_code or "Unknown",
            chapters=proposal_chapters,
            metadata={},
            parse_time=datetime.now().isoformat()
        )
        
        logger.info(f"Parsed {len(tender_chapters)} tender chapters and {len(proposal_chapters)} proposal chapters")
        
        return tender_doc, proposal_doc
    
    async def generate_knowledge_base(
        self,
        tender_doc: ParsedDocument,
        proposal_doc: ParsedDocument,
        pair_id: str,
        storage_path: str
    ) -> KnowledgeBase:
        """
        从解析后的文档生成知识库
        
        Args:
            tender_doc: 解析后的招标文档
            proposal_doc: 解析后的投标文档
            pair_id: 配对ID
            storage_path: 存储路径
            
        Returns:
            知识库对象
        """
        logger.info(f"Generating knowledge base for pair: {pair_id}")
        
        entries = []
        entry_id_counter = 1
        
        # 从招标文档提取知识
        for chapter in tender_doc.chapters:
            # 提取需求类知识
            for req in chapter.requirements:
                entry = KnowledgeEntry(
                    entry_id=f"kb_{pair_id}_{entry_id_counter:04d}",
                    source_doc_type="tender",
                    source_chapter_id=chapter.chapter_id,
                    content_type="requirement",
                    content=req,
                    structured_data={"requirement": req},
                    related_entries=[],
                    keywords=self._extract_keywords(req),
                    importance_score=80,
                    created_time=datetime.now().isoformat()
                )
                entries.append(entry)
                entry_id_counter += 1
            
            # 提取技术规格
            for spec in chapter.technical_specs:
                entry = KnowledgeEntry(
                    entry_id=f"kb_{pair_id}_{entry_id_counter:04d}",
                    source_doc_type="tender",
                    source_chapter_id=chapter.chapter_id,
                    content_type="technical",
                    content=f"{spec.get('item', '')}: {spec.get('spec', '')}",
                    structured_data=spec,
                    related_entries=[],
                    keywords=[spec.get('item', '')],
                    importance_score=90 if spec.get('mandatory') else 70,
                    created_time=datetime.now().isoformat()
                )
                entries.append(entry)
                entry_id_counter += 1
            
            # 提取评分标准
            for criterion in chapter.evaluation_criteria:
                entry = KnowledgeEntry(
                    entry_id=f"kb_{pair_id}_{entry_id_counter:04d}",
                    source_doc_type="tender",
                    source_chapter_id=chapter.chapter_id,
                    content_type="evaluation",
                    content=f"{criterion.get('criterion', '')}: 权重{criterion.get('weight', 0)}",
                    structured_data=criterion,
                    related_entries=[],
                    keywords=[criterion.get('criterion', '')],
                    importance_score=100,
                    created_time=datetime.now().isoformat()
                )
                entries.append(entry)
                entry_id_counter += 1
        
        # 从投标文档提取知识（特别是如何响应需求）
        for chapter in proposal_doc.chapters:
            # 提取技术方案
            for spec in chapter.technical_specs:
                entry = KnowledgeEntry(
                    entry_id=f"kb_{pair_id}_{entry_id_counter:04d}",
                    source_doc_type="proposal",
                    source_chapter_id=chapter.chapter_id,
                    content_type="technical",
                    content=f"{spec.get('item', '')}: {spec.get('spec', '')}",
                    structured_data=spec,
                    related_entries=[],
                    keywords=[spec.get('item', '')],
                    importance_score=85,
                    created_time=datetime.now().isoformat()
                )
                entries.append(entry)
                entry_id_counter += 1
        
        # 统计各类型条目
        entry_types = {}
        for entry in entries:
            entry_types[entry.content_type] = entry_types.get(entry.content_type, 0) + 1
        
        kb = KnowledgeBase(
            kb_id=f"kb_{pair_id}",
            pair_id=pair_id,
            entries=entries,
            total_entries=len(entries),
            entry_types=entry_types,
            storage_path=storage_path,
            created_time=datetime.now().isoformat()
        )
        
        # 保存知识库
        await self._save_knowledge_base(kb, storage_path)
        
        logger.info(f"Generated knowledge base with {len(entries)} entries", extra={
            "entry_types": entry_types
        })
        
        return kb
    
    def _extract_keywords(self, text: str, max_keywords: int = 5) -> List[str]:
        """简单的关键词提取"""
        # 简化版：分词后取最长的几个词
        words = text.split()
        # 过滤掉常见停用词
        stopwords = {'的', '了', '在', '是', '和', '与', '等', '及', '或'}
        keywords = [w for w in words if w not in stopwords and len(w) > 1]
        return keywords[:max_keywords]
    
    async def _save_knowledge_base(self, kb: KnowledgeBase, storage_path: str):
        """保存知识库到文件"""
        kb_dir = Path(storage_path) / "knowledge_base"
        kb_dir.mkdir(parents=True, exist_ok=True)
        
        kb_file = kb_dir / f"{kb.kb_id}.json"
        
        # 转换为可序列化格式
        kb_data = {
            "kb_id": kb.kb_id,
            "pair_id": kb.pair_id,
            "total_entries": kb.total_entries,
            "entry_types": kb.entry_types,
            "created_time": kb.created_time,
            "entries": [
                {
                    "entry_id": e.entry_id,
                    "source_doc_type": e.source_doc_type,
                    "source_chapter_id": e.source_chapter_id,
                    "content_type": e.content_type,
                    "content": e.content,
                    "structured_data": e.structured_data,
                    "keywords": e.keywords,
                    "importance_score": e.importance_score,
                    "created_time": e.created_time
                }
                for e in kb.entries
            ]
        }
        
        with open(kb_file, 'w', encoding='utf-8') as f:
            json.dump(kb_data, f, ensure_ascii=False, indent=2)
        
        logger.info(f"Saved knowledge base: {kb_file}")
