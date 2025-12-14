"""
文档解析引擎
支持PDF和Word文档的解析,自动分割章节
"""
from pypdf import PdfReader
import docx
import re
import uuid
import os
import json
from typing import Dict, List, Optional
from engines.parse_engine_v2 import EnhancedChapterExtractor
from engines.image_extractor import ImageExtractor
from database import db


class ParseEngine:
    """文档解析引擎"""
    
    def __init__(self):
        """初始化解析引擎"""
        self.db = db
        self.enhanced_extractor = EnhancedChapterExtractor()
        self.image_extractor = ImageExtractor()
        self._ocr_extractor = None  # 延迟初始化OCR
        # 改进的章节模式识别
        self.chapter_patterns = [
            # 中文章节号：第一章、第一节
            (r'^第([一二三四五六七八九十百]+)章[\s　]*(.+)$', 1),
            (r'^第([一二三四五六七八九十百]+)节[\s　]*(.+)$', 1),
            # 数字编号：优先级从高到低
            (r'^(\d+\.\d+\.\d+\.\d+)[\s　]+(.+)$', 2),  # 4级编号 (1.1.1.1)
            (r'^(\d+\.\d+\.\d+)[\s　]+(.+)$', 2),       # 3级编号 (1.1.1)
            (r'^(\d+\.\d+)[\s　]+(.+)$', 2),            # 2级编号 (1.1)
            # 单个数字：需要更多限制
            # - 范围1-99
            # - 标题至少8个字符
            # - 不以时间单位结尾（日、月、年、天、小时等）
            (r'^([1-9]|[1-9]\d)[\s　]+((?!.*[日月年天小时分秒分钟$]).{8,})$', 2),
        ]
    
    def parse(self, file_path: str, doc_type: str, save_to_db: bool = True, file_id: str = None) -> Dict:
        """
        解析文件并存入数据库
        
        Args:
            file_path: 文件路径
            doc_type: 文档类型(tender/proposal/reference)
            save_to_db: 是否保存到数据库
            file_id: 文件ID(用于图片提取)
            
        Returns:
            dict: {file_id, filename, content, chapters, images}
        """
        # 1. 提取文本
        if file_path.endswith('.pdf'):
            content = self._parse_pdf(file_path)
        elif file_path.endswith(('.docx', '.doc')):
            content = self._parse_docx(file_path)
        else:
            raise ValueError(f"不支持的文件格式: {file_path}")
        
        # 2. 从正文识别条款结构（新策略）
        chapters = self._extract_from_content(content)
        
        # 2.1 边界检查:如果没有识别到章节,创建默认章节
        if not chapters:
            chapters = [{
                'chapter_number': '1',
                'chapter_title': '全文',
                'chapter_level': 1,
                'content': content
            }]
        
        # 3. 统一文档类型，避免违反数据库约束
        allowed_doc_types = {"tender", "proposal", "reference"}
        safe_doc_type = doc_type if doc_type in allowed_doc_types else "reference"

        # 4. 提取并保存图片(不进行OCR,只保存原始图片)
        extracted_images = []
        if file_id:
            from datetime import datetime
            
            # 尝试从数据库获取文件年份信息
            year = datetime.now().year  # 默认当前年份
            try:
                result = self.db.query_one(
                    "SELECT created_at FROM uploaded_files WHERE id = %s",
                    (file_id,)
                )
                if result and result['created_at']:
                    year = result['created_at'].year
            except Exception as e:
                from core.logger import logger
                logger.warning(f"无法从数据库获取文件年份，使用当前年份: {e}")
            
            if file_path.endswith('.pdf'):
                extracted_images = self.image_extractor.extract_from_pdf(file_path, file_id, year)
            elif file_path.endswith(('.docx', '.doc')):
                extracted_images = self.image_extractor.extract_from_docx(file_path, file_id, year)
            
            from core.logger import logger
            logger.info(f"📷 提取并保存了 {len(extracted_images)} 张图片到 /images/{year}/{file_id}/")

        # 5. 保存到数据库（可选）
        if save_to_db and not file_id:
            file_id = self._save_to_db(file_path, safe_doc_type, content, chapters)
        elif save_to_db and file_id:
            # 只更新章节信息
            self._update_chapters(file_id, chapters)
        
        return {
            'file_id': file_id,
            'filename': os.path.basename(file_path),
            'content': content,
            'total_chapters': len(chapters),
            'chapters': chapters,
            'images': extracted_images,  # 新增: 图片列表
            'image_count': len(extracted_images)
        }
    
    def _parse_pdf(self, file_path: str) -> str:
        """
        解析PDF文件（使用OCR支持扫描文档）
        
        Args:
            file_path: PDF文件路径
            
        Returns:
            str: 提取的文本内容
        """
        # 延迟初始化OCR提取器
        if self._ocr_extractor is None:
            try:
                from engines.ocr_extractor import HybridTextExtractor
                import os
                use_ocr = os.getenv('OCR_ENABLED', 'true').lower() == 'true'
                self._ocr_extractor = HybridTextExtractor(use_paddle_ocr=use_ocr)
                from core.logger import logger
                logger.info(f"OCR提取器初始化成功 (OCR={'启用' if use_ocr else '禁用'})")
            except Exception as e:
                from core.logger import logger
                logger.warning(f"OCR初始化失败,使用基础提取: {e}")
                self._ocr_extractor = None
        
        # 使用OCR增强的提取器
        if self._ocr_extractor:
            try:
                import asyncio
                # 同步调用异步方法
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                results = loop.run_until_complete(
                    self._ocr_extractor.extract_document(file_path)
                )
                loop.close()
                
                # 合并所有页面文本
                text_parts = [r['text'] for r in results if r.get('text')]
                return '\n'.join(text_parts)
            except Exception as e:
                from core.logger import logger
                logger.warning(f"OCR提取失败,回退到基础提取: {e}")
        
        # 回退: 基础PDF文本提取
        reader = PdfReader(file_path)
        text_parts = []
        
        for page in reader.pages:
            text = page.extract_text()
            if text:
                text_parts.append(text)
        
        return '\n'.join(text_parts)
    
    def _clean_pdf_line_breaks(self, text: str) -> str:
        """
        清理PDF提取时产生的不合理换行
        
        注意：不做过度清理，保留段落结构
        只合并明显的分词错误（如"词语\n定义"这种超短行）
        
        Args:
            text: 原始PDF文本
            
        Returns:
            str: 清理后的文本
        """
        # 暂不做清理，直接返回原文
        # PDF层面的清理容易误合并正文段落
        return text
    
    def _parse_docx(self, file_path: str) -> str:
        """
        解析Word文档（支持提取嵌入图片并OCR识别）
        
        Args:
            file_path: Word文件路径
            
        Returns:
            str: 提取的文本内容（包含OCR识别的图片文字）
        """
        import os
        from core.logger import logger
        
        doc = docx.Document(file_path)
        text_parts = []
        
        # 1. 提取段落文本
        for paragraph in doc.paragraphs:
            if paragraph.text.strip():
                text_parts.append(paragraph.text)
        
        # 2. 提取并OCR识别嵌入的图片（如果启用OCR）
        use_ocr = os.getenv('OCR_ENABLED', 'true').lower() == 'true'
        if use_ocr and hasattr(doc, 'part'):
            try:
                # 延迟初始化OCR
                if self._ocr_extractor is None:
                    from engines.ocr_extractor import HybridTextExtractor
                    self._ocr_extractor = HybridTextExtractor(use_paddle_ocr=True)
                    logger.info("OCR提取器初始化成功")
                
                from engines.ocr_extractor import PaddleOCRExtractor
                ocr = PaddleOCRExtractor()
                
                # 遍历文档中的图片关系
                image_count = 0
                for rel in doc.part.rels.values():
                    if "image" in rel.target_ref:
                        try:
                            image_data = rel.target_part.blob
                            
                            # 使用Tesseract OCR识别图片
                            import pytesseract
                            from PIL import Image
                            import io
                            
                            img = Image.open(io.BytesIO(image_data))
                            ocr_text = pytesseract.image_to_string(img, lang='chi_sim+eng')
                            
                            if ocr_text and len(ocr_text.strip()) > 10:
                                text_parts.append(f"\n[图片内容-{image_count+1}]\n{ocr_text}")
                                image_count += 1
                                logger.info(f"成功识别图片 {image_count}: {len(ocr_text)} 字符")
                        except Exception as img_err:
                            logger.warning(f"图片OCR识别失败: {img_err}")
                            continue
                
                if image_count > 0:
                    logger.info(f"文档 {os.path.basename(file_path)} 共识别 {image_count} 张图片")
            
            except Exception as e:
                logger.warning(f"文档图片提取失败: {e}")
        
        return '\n'.join(text_parts)
    
    def _extract_from_content(self, content: str) -> List[Dict]:
        """
        从正文识别条款结构（智能、多阶段识别）
        
        识别策略：
        1. 跳过目录部分（大量"一、二、三"但编号不连续）
        2. 识别编号的连续性（1. 1.1 1.1.1 等序列）
        3. 基于编号前缀识别层级关系
        4. 确保识别的条款与目录内容一致
        
        支持的格式：
        - 1. 条款标题 (L1主条款)
        - 1.1 子条款 或 1.1子条款 (L2, 允许没有空格)
        - 1.1.1 子子条款 (L3)
        - 1.1.1.1 详细定义 (L4)
        - 一、二、三 等目录格式（仅在开头）
        
        Args:
            content: 文档全文
            
        Returns:
            list: 章节列表，只包含实际的条款编号
        """
        # 优先使用增强版提取器（支持“第X部分/中文编号/主章节/附件”全层级）
        try:
            enhanced = self.enhanced_extractor.extract_chapters(content)
            if enhanced:
                return enhanced
        except Exception:
            # 回退到旧版逻辑
            pass

        lines = content.split('\n')
        
        # ===== 第一阶段：找到第一个"主条款"（通常是1.）=====
        main_clause_idx = self._find_first_main_clause(lines)
        if main_clause_idx < 0:
            return []
        
        # ===== 第二阶段：从主条款开始收集所有编号条款 =====
        chapters = []
        seen_numbers = set()  # 防止重复
        
        # 条款编号的正则模式（按优先级，允许编号和标题之间没有空格）
        patterns = [
            # 4级: 1.1.1.1 (可选空格) 标题
            (r'^(\d+)\.(\d+)\.(\d+)\.(\d+)[\s　]*(.+)$', 4),
            # 3级: 1.1.1 (可选空格) 标题
            (r'^(\d+)\.(\d+)\.(\d+)[\s　]*(.+)$', 3),
            # 2级: 1.1 (可选空格) 标题
            (r'^(\d+)\.(\d+)[\s　]*(.+)$', 2),
            # 1级: 1. 或 1 . (强制有空格/点号)
            (r'^(\d+)[\s　]\.[\s　]*(.+)$', 1),
        ]
        
        for line_idx in range(main_clause_idx, len(lines)):
            line = lines[line_idx].strip()
            
            if not line or len(line) < 3:
                continue
            
            # 尝试匹配编号模式
            matched = False
            for pattern, level in patterns:
                match = re.match(pattern, line)
                if not match:
                    continue
                
                # 提取编号和标题
                if level == 1:
                    number = match.group(1)
                    title = match.group(2).strip()
                elif level in [2, 3, 4]:
                    # 获取所有数字部分组成编号
                    groups = match.groups()[:-1]  # 去掉标题
                    number = '.'.join(str(g) for g in groups)
                    title = match.groups()[-1].strip()
                else:
                    continue
                
                # 过滤无效标题
                if len(title) < 2 or title in ['。', '，', '、', '；', '：', '…']:
                    break
                
                # ===== 新增：过滤数字相关的无效章节 =====
                # 1. 标题只有1-3个字符且包含单位词的，不是章节标题（如"万元"、"米"、"天"）
                if len(title) <= 3:
                    if any(unit in title for unit in ['元', '米', '天', '年', '月', '日', '吨', '个', '次', '项']):
                        break
                
                # 2. 标题以"款"、"条"等法律用词开头，且后面跟着中文括号，很可能是正文片段
                if title.startswith(('款', '条', '项')) and ('〔' in title or '【' in title or '（' in title):
                    break
                
                # 3. 编号不合理：超过50（一般合同最多21-30章）且level=2
                if level == 2:
                    try:
                        first_num = int(number.split('.')[0])
                        if first_num > 50:  # 超过50章明显不对
                            break
                    except:
                        pass
                
                # 4. 标题开头是括号、数字（但允许正常的中文标题）
                if title[0] in ['(', '（', '[', '【', ')', '）', ']', '】']:
                    break
                if title[0].isdigit() and len(title) <= 5:  # 纯数字开头且短标题才过滤
                    break
                
                # 防止重复
                if number in seen_numbers:
                    break
                
                seen_numbers.add(number)
                
                # 从标题中去掉尾部的定义内容（冒号之后）
                # 但要保持一定的标题长度（防止过度裁剪）
                if '：' in title:
                    before_colon = title.split('：')[0].strip()
                    # 只在冒号前部分足够长时才使用
                    if len(before_colon) > 1:
                        title = before_colon
                
                # 清理标题中可能存在的多行内容
                # PDF提取时经常将标题分成多行
                title = title.replace('\n', '').replace('　', ' ').replace('  ', ' ').strip()
                
                # 创建章节条目
                chapter = {
                    'chapter_number': number,
                    'chapter_title': title,
                    'chapter_level': level,
                    'content': ''
                }
                chapters.append(chapter)
                matched = True
                break
        
        # ===== 第三阶段：验证识别结果 =====
        # 至少需要3个条款
        if len(chapters) >= 3:
            # 第四阶段：后处理 - 修复被分割的标题
            chapters = self._repair_split_titles(chapters)
            return chapters
        
        return []
    
    def _repair_split_titles(self, chapters: List[Dict]) -> List[Dict]:
        """
        修复被PDF分割导致的标题碎片化（保守版）
        
        策略：只清理每个标题内部的换行和空格，不合并不同的条款
        
        Args:
            chapters: 原始条款列表
            
        Returns:
            list: 修复后的条款列表
        """
        repaired = []
        
        for chapter in chapters:
            cleaned = chapter.copy()
            # 清理标题：去除换行、多余空格
            title = chapter['chapter_title']
            title = title.replace('\n', '').replace('  ', ' ').strip()
            cleaned['chapter_title'] = title
            repaired.append(cleaned)
        
        return repaired
    
    def _find_first_main_clause(self, lines: List[str]) -> int:
        """
        找到第一个主条款（1. 开头）的行索引
        这标志着正文条款内容的真正开始
        
        关键：需要区分两种"1."格式：
        1. 目录中的"1. 条款......页码"（有大量点号）
        2. 正文中的"1. 条款" （无点号）
        
        策略：
        - 找所有"1."开头的行
        - 后面跟着"1.1"等子条款的才是真正的正文
        
        Args:
            lines: 分行的文本
            
        Returns:
            int: 第一个主条款的行索引，未找到返回-1
        """
        # 第一步：找到所有可能是"1."的行索引
        candidate_indices = []
        for idx, line in enumerate(lines):
            line_stripped = line.strip()
            if not line_stripped:
                continue
            # "1."开头，不要求后面一定有空格
            if re.match(r'^1[\s　]*\.', line_stripped):
                candidate_indices.append(idx)
        
        # 第二步：对每个候选者，检查后续是否有"1.1"等子条款
        # 这是区分目录和正文的关键
        for idx in candidate_indices:
            # 检查后续30行中是否有"1.1"子条款
            has_sub_clause = False
            for check_idx in range(idx + 1, min(idx + 30, len(lines))):
                check_line = lines[check_idx].strip()
                # 寻找1.1开头的行（带或不带空格）
                if re.match(r'^1\.1[\s　]*', check_line):
                    has_sub_clause = True
                    break
            
            # 如果找到子条款，那么这个候选者就是真正的正文开始
            if has_sub_clause:
                return idx
        
        return -1
    
    def _clean_text(self, text: str) -> str:
        """
        文本清理：去除中文字符间的空格

        Args:
            text: 原始文本

        Returns:
            str: 清理后的文本
        """
        # 1. 去除中文字符间的空格和全角空格
        text = re.sub(r'([\u4e00-\u9fff])[\s　]+([\u4e00-\u9fff])', r'\1\2', text)
        
        # 2. 去除中英文间过多的空格（保留一个）
        text = re.sub(r'([\u4e00-\u9fff])[\s　]{2,}([A-Za-z0-9])', r'\1 \2', text)
        text = re.sub(r'([A-Za-z0-9])[\s　]{2,}([\u4e00-\u9fff])', r'\1 \2', text)
        
        # 3. 合并多个空格为单个
        text = re.sub(r' {2,}', ' ', text)
        
        return text
    
    def _save_to_db(self, file_path: str, doc_type: str, content: str, chapters: List[Dict]) -> str:
        """
        保存文件和章节到数据库
        
        Args:
            file_path: 文件路径
            doc_type: 文档类型
            content: 全文内容
            chapters: 章节列表
            
        Returns:
            str: 文件ID
        """
        filename = os.path.basename(file_path)
        filetype = os.path.splitext(filename)[1][1:]  # 去掉点号
        
        # 1. 插入文件记录
        allowed_doc_types = {"tender", "proposal", "reference"}
        safe_doc_type = doc_type if doc_type in allowed_doc_types else "reference"

        file_id = self.db.execute("""
            INSERT INTO files (filename, filepath, filetype, doc_type, content, metadata)
            VALUES (%s, %s, %s, %s, %s, %s)
            RETURNING id
        """, (filename, file_path, filetype, safe_doc_type, content, json.dumps({'total_chapters': len(chapters)})))
        
        # 2. 批量插入章节
        for idx, chapter in enumerate(chapters, start=1):
            self.db.execute("""
                INSERT INTO chapters (
                    file_id, chapter_number, chapter_title, chapter_level, 
                    content, position_order, structure_data
                ) VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (
                file_id,
                chapter['chapter_number'],
                chapter['chapter_title'],
                chapter['chapter_level'],
                chapter['content'],
                idx,
                json.dumps({'word_count': len(chapter['content'])})
            ))
        
        return file_id
