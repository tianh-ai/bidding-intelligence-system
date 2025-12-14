# -*- coding: utf-8 -*-
"""
integrated_parser_with_tracking.py - 集成验证脚本
演示verify_new_parser.py与init_database.py的完整关系

工作流程:
1. 从uploaded_files表读取待处理的文件
2. 调用verify_new_parser进行验证
3. 将验证结果存入parsing_results和verification_tracking
4. 从解析结果提取知识条项到knowledge_base
"""

import asyncio
import asyncpg
import sys
import time
from datetime import datetime
from typing import Dict, List, Optional
from uuid import uuid4
from loguru import logger

# 配置
DB_HOST = "localhost"
DB_PORT = 5432
DB_NAME = "bidding_db"
DB_USER = "postgres"
DB_PASSWORD = "postgres"

logger.add(
    "/Volumes/ssd/bidding-data/logs/integrated_parser.log",
    rotation="500 MB",
    level="INFO"
)


class VerificationResult:
    """verify_new_parser.py的输出数据结构"""
    def __init__(self, file_path: str):
        self.file_path = file_path
        self.total_toc_items = 16
        self.matched_count = 0
        self.toc_items = []  # 参考TOC
        self.extracted_chapters = []  # 实际提取的章节
        self.verification_details = []
        self.parsing_time = 0.0
        
    def to_dict(self):
        """转换为字典，用于JSON存储"""
        return {
            "file_path": self.file_path,
            "total_toc_items": self.total_toc_items,
            "matched_count": self.matched_count,
            "success_rate": (self.matched_count / self.total_toc_items * 100) if self.total_toc_items > 0 else 0,
            "extracted_chapter_count": len(self.extracted_chapters),
            "verification_details": self.verification_details,
            "toc_verification": self._generate_toc_verification(),
            "timestamp": datetime.now().isoformat()
        }
    
    def _generate_toc_verification(self):
        """生成TOC验证详情"""
        return [
            {
                "toc_item": item,
                "matched": item in self.extracted_chapters,
                "extracted_chapter": item if item in self.extracted_chapters else None,
                "similarity_score": 0.95 if item in self.extracted_chapters else 0.0
            }
            for item in self.toc_items
        ]


class IntegratedParserTracker:
    """集成解析和追踪系统"""
    
    def __init__(self):
        self.db = None
        
    async def connect(self):
        """连接数据库"""
        self.db = await asyncpg.connect(
            host=DB_HOST,
            port=DB_PORT,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD
        )
        logger.info("✓ 数据库连接成功")
    
    async def disconnect(self):
        """断开连接"""
        if self.db:
            await self.db.close()
    
    async def get_pending_files(self) -> List[Dict]:
        """从uploaded_files表获取待处理的文件"""
        query = """
        SELECT id, file_name, file_path, file_size, created_at
        FROM uploaded_files
        WHERE parse_status = 'pending'
        LIMIT 10
        """
        rows = await self.db.fetch(query)
        return [dict(row) for row in rows]
    
    async def simulate_verify_parser(self, file_path: str) -> VerificationResult:
        """模拟verify_new_parser.py的执行
        
        在实际应用中，这里应该调用真实的ParseEngine和EnhancedChapterExtractor
        """
        logger.info(f"🔍 开始验证: {file_path}")
        
        # 模拟处理时间
        await asyncio.sleep(0.5)
        
        # 模拟验证结果
        result = VerificationResult(file_path)
        result.toc_items = [
            "第一部分  投标邀请",
            "一、投标说明",
            "二、投标人资格要求",
            "三、投标人应具备的条件",
            "四、招标人联系方式",
            "第二部分  投标人须知",
            "五、投标前的准备",
            "六、投标文件的构成",
            "七、投标文件的制作",
            "八、投标文件的送交",
            "第三部分  技术规格",
            "九、技术要求",
            "十、性能指标",
            "十一、质量标准",
            "十二、验收条件",
            "十三、服务要求"
        ]
        
        # 模拟提取的章节 (14/16匹配)
        result.extracted_chapters = result.toc_items[:-2]  # 缺少最后两项
        result.matched_count = len(result.extracted_chapters)
        result.parsing_time = 3.45
        
        logger.info(f"✓ 验证完成: {result.matched_count}/{result.total_toc_items} 匹配 (成功率: {result.matched_count/result.total_toc_items*100:.1f}%)")
        
        return result
    
    async def save_verification_result(self, file_id: str, file_name: str, 
                                      verify_result: VerificationResult) -> str:
        """保存验证结果到数据库
        
        这个函数演示了verify_new_parser.py输出与init_database.py表结构的关系
        
        流程:
        1. 更新uploaded_files的parse_status
        2. 创建parsing_results记录
        3. 创建verification_tracking记录
        4. 创建mapping关系
        5. 从验证结果提取知识条项到knowledge_base
        """
        start_time = time.time()
        verification_result_id = str(uuid4())
        parsing_result_id = str(uuid4())
        
        try:
            # Step 1: 更新uploaded_files的parse_status
            logger.info(f"📝 Step 1: 更新 uploaded_files (file_id: {file_id})")
            update_query = """
            UPDATE uploaded_files
            SET parse_status = 'processing', updated_at = NOW()
            WHERE id = $1
            """
            await self.db.execute(update_query, file_id)
            
            # Step 2: 创建parsing_results记录
            logger.info(f"📝 Step 2: 创建 parsing_results 记录")
            parsing_query = """
            INSERT INTO parsing_results 
            (id, file_id, chapter_count, parsing_time, parsing_status, 
             result_json, accuracy_score, matched_toc_items, total_toc_items)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
            """
            
            result_dict = verify_result.to_dict()
            accuracy = (verify_result.matched_count / verify_result.total_toc_items * 100)
            
            await self.db.execute(
                parsing_query,
                parsing_result_id,  # id
                file_id,  # file_id (FK)
                len(verify_result.extracted_chapters),  # chapter_count
                verify_result.parsing_time,  # parsing_time
                "completed",  # parsing_status
                result_dict,  # result_json (完整验证结果)
                accuracy,  # accuracy_score
                verify_result.matched_count,  # matched_toc_items
                verify_result.total_toc_items  # total_toc_items
            )
            logger.info(f"✓ parsing_results created: {parsing_result_id}")
            
            # Step 3: 创建verification_tracking记录
            logger.info(f"📝 Step 3: 创建 verification_tracking 记录")
            verify_tracking_query = """
            INSERT INTO verification_tracking
            (id, file_id, parsing_result_id, verification_status,
             verification_start_time, verification_end_time,
             total_toc_items, matched_toc_items, success_rate,
             extracted_chapter_count, toc_verification_details)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
            """
            
            await self.db.execute(
                verify_tracking_query,
                verification_result_id,  # id
                file_id,  # file_id (FK)
                parsing_result_id,  # parsing_result_id (FK)
                "completed",  # verification_status
                datetime.now(),  # verification_start_time
                datetime.now(),  # verification_end_time
                verify_result.total_toc_items,  # total_toc_items
                verify_result.matched_count,  # matched_toc_items
                accuracy,  # success_rate
                len(verify_result.extracted_chapters),  # extracted_chapter_count
                result_dict.get("toc_verification")  # toc_verification_details
            )
            logger.info(f"✓ verification_tracking created: {verification_result_id}")
            
            # Step 4: 创建mapping关系
            logger.info(f"📝 Step 4: 创建 parsing_verification_mapping 关系")
            mapping_query = """
            INSERT INTO parsing_verification_mapping
            (file_id, parsing_result_id, verification_tracking_id,
             overall_quality_score)
            VALUES ($1, $2, $3, $4)
            """
            
            await self.db.execute(
                mapping_query,
                file_id,  # file_id
                parsing_result_id,  # parsing_result_id
                verification_result_id,  # verification_tracking_id
                accuracy / 100.0  # overall_quality_score (0-1)
            )
            logger.info("✓ mapping created")
            
            # Step 5: 从验证结果提取知识条项到knowledge_base
            logger.info(f"📝 Step 5: 提取知识条项到 knowledge_base")
            
            knowledge_count = 0
            for i, chapter in enumerate(verify_result.extracted_chapters):
                # 只插入匹配的章节
                kb_query = """
                INSERT INTO knowledge_base
                (file_id, title, content, category, file_name,
                 chapter_source, extraction_confidence)
                VALUES ($1, $2, $3, $4, $5, $6, $7)
                """
                
                await self.db.execute(
                    kb_query,
                    file_id,  # file_id (FK)
                    f"{chapter}",  # title
                    f"内容详情: {chapter}",  # content
                    "招标条款",  # category
                    file_name,  # file_name
                    chapter,  # chapter_source
                    0.95  # extraction_confidence (高置信度)
                )
                knowledge_count += 1
            
            logger.info(f"✓ {knowledge_count} 条知识条项已创建")
            
            # Step 6: 最后更新uploaded_files的parse_status为completed
            logger.info(f"📝 Step 6: 完成处理，更新 uploaded_files")
            final_update_query = """
            UPDATE uploaded_files
            SET parse_status = 'completed', updated_at = NOW()
            WHERE id = $1
            """
            await self.db.execute(final_update_query, file_id)
            
            elapsed_time = time.time() - start_time
            logger.info(f"✅ 文件处理完成! 耗时: {elapsed_time:.2f}秒")
            
            return parsing_result_id
            
        except Exception as e:
            logger.error(f"❌ 保存结果失败: {e}")
            # 回滚: 更新parse_status为failed
            await self.db.execute(
                "UPDATE uploaded_files SET parse_status = 'failed' WHERE id = $1",
                file_id
            )
            raise
    
    async def query_file_lifecycle(self, file_id: str):
        """查询单个文件的完整生命周期"""
        query = """
        SELECT 
            uf.id as file_id,
            uf.file_name,
            uf.upload_status,
            uf.parse_status,
            uf.created_at as upload_time,
            uf.updated_at as last_updated,
            
            pr.id as parsing_result_id,
            pr.chapter_count,
            pr.parsing_time,
            pr.accuracy_score,
            pr.matched_toc_items,
            pr.total_toc_items,
            
            vt.id as verification_tracking_id,
            vt.verification_status,
            vt.success_rate,
            
            COUNT(DISTINCT kb.id) as knowledge_items_count
            
        FROM uploaded_files uf
        LEFT JOIN parsing_results pr ON uf.id = pr.file_id
        LEFT JOIN verification_tracking vt ON pr.id = vt.parsing_result_id
        LEFT JOIN knowledge_base kb ON uf.id = kb.file_id
        
        WHERE uf.id = $1
        GROUP BY uf.id, pr.id, vt.id
        """
        
        result = await self.db.fetchval(query, file_id)
        return dict(result) if result else None


async def demonstrate_relationship():
    """演示verify_new_parser.py与init_database.py的完整关系"""
    
    tracker = IntegratedParserTracker()
    await tracker.connect()
    
    try:
        print("="*70)
        print("📊 verify_new_parser.py ↔ init_database.py 关系演示")
        print("="*70)
        print()
        
        # 获取待处理文件
        pending_files = await tracker.get_pending_files()
        
        if not pending_files:
            logger.info("⚠️ 没有待处理的文件")
            print("提示: 请先使用文件上传功能将PDF文件上传到系统")
            print("      或使用测试脚本创建测试数据")
            return
        
        logger.info(f"发现 {len(pending_files)} 个待处理文件")
        
        for file_info in pending_files[:1]:  # 只处理第一个文件作为演示
            file_id = file_info['id']
            file_name = file_info['file_name']
            file_path = file_info['file_path']
            
            print(f"\n📁 处理文件: {file_name}")
            print(f"   Path: {file_path}")
            print(f"   FileID: {file_id}")
            print()
            
            # 1. 执行verify_new_parser验证
            verify_result = await tracker.simulate_verify_parser(file_path)
            
            # 2. 保存验证结果到数据库 (演示完整的关系流程)
            print()
            print("💾 保存验证结果到数据库...")
            parsing_result_id = await tracker.save_verification_result(
                file_id, file_name, verify_result
            )
            
            # 3. 查询文件的完整生命周期
            print()
            print("📊 查询文件生命周期...")
            lifecycle = await tracker.query_file_lifecycle(file_id)
            
            if lifecycle:
                print(f"\n文件处理流程:")
                print(f"  上传时间: {lifecycle['upload_time']}")
                print(f"  上传状态: {lifecycle['upload_status']}")
                print(f"  解析状态: {lifecycle['parse_status']}")
                print(f"  最后更新: {lifecycle['last_updated']}")
                print(f"\n解析结果:")
                print(f"  解析耗时: {lifecycle['parsing_time']}秒")
                print(f"  章节数: {lifecycle['chapter_count']}")
                print(f"  准确率: {lifecycle['accuracy_score']:.1f}% ({lifecycle['matched_toc_items']}/{lifecycle['total_toc_items']})")
                print(f"\n追踪信息:")
                print(f"  验证状态: {lifecycle['verification_status']}")
                print(f"  知识条项: {lifecycle['knowledge_items_count']}条")
        
        print()
        print("="*70)
        print("✅ 关系演示完成")
        print("="*70)
        
    finally:
        await tracker.disconnect()


if __name__ == "__main__":
    asyncio.run(demonstrate_relationship())
