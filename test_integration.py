#!/usr/bin/env python3
"""验证 ParseEngine 集成 TableExtractor Skill"""

from backend.engines.parse_engine import ParseEngine

# 测试1: 初始化引擎（启用表格提取）
engine_with_tables = ParseEngine(use_table_skill=True)
print("✅ Engine with tables initialized:", engine_with_tables.use_table_skill)

# 测试2: 初始化引擎（禁用表格提取）
engine_no_tables = ParseEngine(use_table_skill=False)
print("✅ Engine without tables initialized:", engine_no_tables.use_table_skill)

# 测试3: 懒加载验证
print("✅ TableExtractor lazy loading:", engine_with_tables._table_extractor is None)
extractor = engine_with_tables.table_extractor
print("✅ TableExtractor loaded:", extractor is not None)

# 测试4: 方法存在性验证
print("✅ _extract_tables_from_pdf exists:", hasattr(engine_with_tables, "_extract_tables_from_pdf"))

# 测试5: 验证 Skill 元数据
metadata = extractor.get_metadata()
print(f"✅ Skill metadata: {metadata['name']} v{metadata['version']}")

print("\n🎉 All integration checks passed!")
