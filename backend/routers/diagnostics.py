"""Diagnostics routes.

仅用于定位解析一致性/知识库链路问题：
- 不改变业务规则（不做章节去重等“掩盖式修复”）
- 提供可复现的解析预览、章节摘要、单文件重解析

注意：这些端点不应该对公网暴露；当前用于本地/内网调试。
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Any, Dict, List, Optional

from core.logger import logger
from database import db
from engines.parse_engine import ParseEngine


router = APIRouter(prefix="/api/diagnostics", tags=["diagnostics"])


class ReparseResponse(BaseModel):
    status: str
    file_id: str
    file_path: str
    doc_type: str
    total_chapters: int


def _get_file_record(file_id: str) -> Dict[str, Any]:
    file_row = db.query_one("SELECT id, filename, filepath, doc_type FROM files WHERE id = %s", (file_id,))
    if not file_row:
        raise HTTPException(status_code=404, detail="文件不存在(files表)")

    file_path = file_row.get("filepath")
    if not file_path:
        raise HTTPException(status_code=400, detail="文件缺少 filepath")

    doc_type = file_row.get("doc_type") or "reference"
    return {
        "file_id": str(file_row.get("id")),
        "filename": file_row.get("filename"),
        "file_path": file_path,
        "doc_type": doc_type,
    }


@router.get("/chapters-summary/{file_id}")
async def chapters_summary(file_id: str) -> Dict[str, Any]:
    """返回章节摘要（用于目录对比，不返回大段正文）。"""
    rows = db.query(
        """
        SELECT chapter_number, chapter_title, chapter_level, position_order
        FROM chapters
        WHERE file_id = %s
        ORDER BY position_order
        """,
        (file_id,),
    ) or []

    return {
        "status": "success",
        "file_id": file_id,
        "total": len(rows),
        "chapters": [
            {
                "chapter_level": r.get("chapter_level"),
                "chapter_number": r.get("chapter_number"),
                "chapter_title": r.get("chapter_title"),
                "position_order": r.get("position_order"),
            }
            for r in rows
        ],
    }


@router.get("/extract-preview/{file_id}")
async def extract_preview(file_id: str, max_lines: int = 80) -> Dict[str, Any]:
    """直接从归档文件重新抽取文本并返回前 N 行，定位“标题缺失/落在表格里”等问题。"""
    rec = _get_file_record(file_id)

    engine = ParseEngine()
    file_path = rec["file_path"]
    try:
        if str(file_path).lower().endswith(".pdf"):
            content = engine._parse_pdf(file_path)
        elif str(file_path).lower().endswith((".docx", ".doc")):
            content = engine._parse_docx(file_path)
        else:
            raise HTTPException(status_code=400, detail=f"不支持的文件格式: {file_path}")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"extract_preview failed: file_id={file_id}, err={e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

    lines = [ln for ln in (content or "").splitlines()]
    head = [ln for ln in lines if ln.strip()][:max_lines]

    return {
        "status": "success",
        **rec,
        "content_length": len(content or ""),
        "head_lines": head,
    }


@router.post("/reparse/{file_id}", response_model=ReparseResponse)
async def reparse_file(file_id: str) -> ReparseResponse:
    """对单文件执行一次重解析，并更新 chapters 表（用于验证解析修复）。"""
    rec = _get_file_record(file_id)

    engine = ParseEngine()
    try:
        result = engine.parse(
            file_path=rec["file_path"],
            doc_type=rec["doc_type"],
            save_to_db=True,
            file_id=file_id,
        )
    except Exception as e:
        logger.error(f"reparse failed: file_id={file_id}, err={e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

    return ReparseResponse(
        status="success",
        file_id=file_id,
        file_path=rec["file_path"],
        doc_type=rec["doc_type"],
        total_chapters=int(result.get("total_chapters", 0) or 0),
    )


@router.get("/reparse/{file_id}", response_model=ReparseResponse)
async def reparse_file_get(file_id: str) -> ReparseResponse:
    """GET 别名：与 POST /reparse/{file_id} 等价，仅用于调试便利。"""
    return await reparse_file(file_id)


@router.get("/compare-chapters")
async def compare_chapters(file_id1: str, file_id2: str) -> Dict[str, Any]:
    """对比两个文件的章节标题序列（用于快速定位目录分叉点）。"""

    def _load(fid: str) -> List[Dict[str, Any]]:
        rows = db.query(
            """
            SELECT chapter_level, chapter_number, chapter_title, position_order
            FROM chapters
            WHERE file_id = %s
            ORDER BY position_order
            """,
            (fid,),
        ) or []
        return [
            {
                "chapter_level": r.get("chapter_level"),
                "chapter_number": r.get("chapter_number"),
                "chapter_title": r.get("chapter_title"),
                "position_order": r.get("position_order"),
            }
            for r in rows
        ]

    a = _load(file_id1)
    b = _load(file_id2)

    # 只给出一个“第一处差异”提示，避免误导为“业务比较逻辑”
    first_diff: Optional[Dict[str, Any]] = None
    for idx in range(min(len(a), len(b))):
        if (a[idx].get("chapter_level"), a[idx].get("chapter_number"), a[idx].get("chapter_title")) != (
            b[idx].get("chapter_level"),
            b[idx].get("chapter_number"),
            b[idx].get("chapter_title"),
        ):
            first_diff = {"index": idx, "a": a[idx], "b": b[idx]}
            break

    return {
        "status": "success",
        "file_id1": file_id1,
        "file_id2": file_id2,
        "total1": len(a),
        "total2": len(b),
        "first_diff": first_diff,
    }
