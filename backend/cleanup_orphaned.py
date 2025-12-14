#!/usr/bin/env python
"""
清理孤立的数据库记录
这些记录指向已删除的文件（被早期文件覆盖bug影响）
"""
import os
from database import db

def cleanup_orphaned_records():
    """查找并删除物理文件不存在的记录"""
    
    # 1. 查找所有有archive_path的记录
    all_records = db.query('''
        SELECT id, filename, semantic_filename, archive_path, category, created_at
        FROM uploaded_files
        WHERE archive_path IS NOT NULL
        ORDER BY created_at DESC
    ''')
    
    print(f"📊 总共找到 {len(all_records)} 条有archive_path的记录\n")
    
    # 2. 检查物理文件是否存在
    missing = []
    exists = []
    
    for record in all_records:
        archive_path = record['archive_path']
        if os.path.exists(archive_path):
            exists.append(record)
        else:
            missing.append(record)
    
    print(f"✅ 物理文件存在: {len(exists)} 个")
    print(f"❌ 物理文件缺失: {len(missing)} 个\n")
    
    if not missing:
        print("🎉 没有孤立记录需要清理!")
        return
    
    # 3. 显示缺失的记录
    print("=" * 80)
    print("以下记录将被删除（物理文件已永久丢失）:")
    print("=" * 80)
    
    for i, record in enumerate(missing, 1):
        print(f"\n{i}. 文件: {record['filename']}")
        print(f"   ID: {record['id']}")
        print(f"   分类: {record['category']}")
        print(f"   语义名: {record['semantic_filename']}")
        print(f"   缺失路径: {record['archive_path']}")
        print(f"   上传时间: {record['created_at']}")
    
    # 4. 确认删除
    print("\n" + "=" * 80)
    response = input(f"\n确认删除这 {len(missing)} 条孤立记录吗? (yes/no): ").strip().lower()
    
    if response not in ['yes', 'y']:
        print("❌ 已取消操作")
        return
    
    # 5. 执行删除
    deleted_count = 0
    orphaned_ids = [r['id'] for r in missing]
    
    for record_id in orphaned_ids:
        try:
            # 删除关联的chapters
            db.execute(
                "DELETE FROM chapters WHERE file_id = %s",
                (record_id,)
            )
            
            # 删除关联的parsed content
            db.execute(
                "DELETE FROM files WHERE id = %s",
                (record_id,)
            )
            
            # 删除uploaded_files记录
            db.execute(
                "DELETE FROM uploaded_files WHERE id = %s",
                (record_id,)
            )
            
            deleted_count += 1
            print(f"✅ 已删除记录: {record_id}")
            
        except Exception as e:
            print(f"❌ 删除失败 {record_id}: {e}")
    
    print(f"\n🎉 清理完成! 共删除 {deleted_count} 条孤立记录")
    
    # 6. 验证结果
    remaining = db.query('''
        SELECT id, archive_path
        FROM uploaded_files
        WHERE archive_path IS NOT NULL
    ''')
    
    missing_after = [r for r in remaining if not os.path.exists(r['archive_path'])]
    
    print(f"\n📊 清理后状态:")
    print(f"   - 总记录数: {len(remaining)}")
    print(f"   - 物理文件缺失: {len(missing_after)}")
    
    if missing_after:
        print("⚠️  警告: 仍有孤立记录!")
    else:
        print("✅ 所有记录都有对应的物理文件")

if __name__ == "__main__":
    cleanup_orphaned_records()
