"""
Asynchronous tasks for document processing using Celery.
"""

import time
from pathlib import Path
from typing import Dict, Any
from backend.worker import celery_app
from backend.core.logger import logger, log_task_start, log_task_complete, log_task_error


@celery_app.task(bind=True, name="tasks.process_uploaded_document")
def process_uploaded_document(self, file_path: str, doc_id: str, doc_type: str) -> Dict[str, Any]:
    """
    Process uploaded document: parse, extract, and store.
    
    Args:
        self: Celery task instance
        file_path: Path to uploaded file
        doc_id: Document ID
        doc_type: Document type (tender/proposal/reference)
        
    Returns:
        Processing result with status and metadata
    """
    start_time = time.time()
    log_task_start("process_uploaded_document", self.request.id, doc_id=doc_id)
    
    try:
        # Update task state to PROCESSING
        self.update_state(
            state="PROCESSING",
            meta={"current": 0, "total": 100, "status": "Initializing..."}
        )
        
        # Import here to avoid circular imports
        from backend.engines.parse_engine import HybridParseEngine
        
        # Initialize parser
        parser = HybridParseEngine()
        
        # Step 1: Parse document (40% of progress)
        self.update_state(
            state="PROCESSING",
            meta={"current": 10, "total": 100, "status": "Parsing document..."}
        )
        
        result = parser.parse_file(file_path)
        
        self.update_state(
            state="PROCESSING",
            meta={"current": 40, "total": 100, "status": "Extracting chapters..."}
        )
        
        # Step 2: Extract chapters (30% of progress)
        chapters = result.get("chapters", [])
        tables = result.get("tables", [])
        
        self.update_state(
            state="PROCESSING",
            meta={"current": 70, "total": 100, "status": "Storing to database..."}
        )
        
        # Step 3: Store to database (20% of progress)
        # TODO: Implement database storage
        # from backend.db.crud import save_parsed_document
        # save_parsed_document(doc_id, result)
        
        self.update_state(
            state="PROCESSING",
            meta={"current": 90, "total": 100, "status": "Finalizing..."}
        )
        
        duration = time.time() - start_time
        log_task_complete("process_uploaded_document", self.request.id, duration, doc_id=doc_id)
        
        return {
            "status": "success",
            "doc_id": doc_id,
            "chapters_count": len(chapters),
            "tables_count": len(tables),
            "total_length": result.get("total_length", 0),
            "duration": duration,
        }
        
    except Exception as e:
        log_task_error("process_uploaded_document", self.request.id, e, doc_id=doc_id)
        self.update_state(
            state="FAILURE",
            meta={"error": str(e)}
        )
        raise


@celery_app.task(bind=True, name="tasks.learn_chapter_logic")
def learn_chapter_logic(self, chapter_id: str, learning_mode: str = "standard") -> Dict[str, Any]:
    """
    Learn logic patterns from a chapter.
    
    Args:
        self: Celery task instance
        chapter_id: Chapter ID
        learning_mode: Learning mode (quick/standard/deep)
        
    Returns:
        Learning result
    """
    start_time = time.time()
    log_task_start("learn_chapter_logic", self.request.id, chapter_id=chapter_id)
    
    try:
        # Import here to avoid circular imports
        from backend.engines.chapter_logic_engine import ChapterLogicEngine
        
        self.update_state(
            state="PROCESSING",
            meta={"current": 0, "total": 100, "status": "Loading chapter..."}
        )
        
        # Initialize engine
        engine = ChapterLogicEngine()
        
        self.update_state(
            state="PROCESSING",
            meta={"current": 30, "total": 100, "status": "Analyzing patterns..."}
        )
        
        # Learn logic patterns
        patterns = engine.learn(chapter_id, mode=learning_mode)
        
        self.update_state(
            state="PROCESSING",
            meta={"current": 80, "total": 100, "status": "Storing patterns..."}
        )
        
        duration = time.time() - start_time
        log_task_complete("learn_chapter_logic", self.request.id, duration, chapter_id=chapter_id)
        
        return {
            "status": "success",
            "chapter_id": chapter_id,
            "patterns_count": len(patterns),
            "duration": duration,
        }
        
    except Exception as e:
        log_task_error("learn_chapter_logic", self.request.id, e, chapter_id=chapter_id)
        raise


@celery_app.task(bind=True, name="tasks.learn_global_logic")
def learn_global_logic(self, file_id: str) -> Dict[str, Any]:
    """
    Learn global logic patterns from entire file.
    
    Args:
        self: Celery task instance
        file_id: File ID
        
    Returns:
        Learning result
    """
    start_time = time.time()
    log_task_start("learn_global_logic", self.request.id, file_id=file_id)
    
    try:
        from backend.engines.global_logic_engine import GlobalLogicEngine
        
        self.update_state(
            state="PROCESSING",
            meta={"current": 0, "total": 100, "status": "Loading file..."}
        )
        
        engine = GlobalLogicEngine()
        
        self.update_state(
            state="PROCESSING",
            meta={"current": 20, "total": 100, "status": "Analyzing structure..."}
        )
        
        result = engine.learn(file_id)
        
        duration = time.time() - start_time
        log_task_complete("learn_global_logic", self.request.id, duration, file_id=file_id)
        
        return {
            "status": "success",
            "file_id": file_id,
            "patterns_count": len(result.get("patterns", [])),
            "duration": duration,
        }
        
    except Exception as e:
        log_task_error("learn_global_logic", self.request.id, e, file_id=file_id)
        raise


@celery_app.task(bind=True, name="tasks.generate_proposal")
def generate_proposal(
    self, 
    tender_id: str, 
    template_id: str, 
    options: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Generate proposal document based on tender and template.
    
    Args:
        self: Celery task instance
        tender_id: Tender document ID
        template_id: Template ID
        options: Generation options
        
    Returns:
        Generated document info
    """
    start_time = time.time()
    log_task_start("generate_proposal", self.request.id, tender_id=tender_id)
    
    try:
        from backend.engines.generation_engine import GenerationEngine
        
        self.update_state(
            state="PROCESSING",
            meta={"current": 0, "total": 100, "status": "Initializing..."}
        )
        
        engine = GenerationEngine()
        
        self.update_state(
            state="PROCESSING",
            meta={"current": 30, "total": 100, "status": "Generating content..."}
        )
        
        result = engine.generate(tender_id, template_id, options)
        
        self.update_state(
            state="PROCESSING",
            meta={"current": 80, "total": 100, "status": "Finalizing..."}
        )
        
        duration = time.time() - start_time
        log_task_complete("generate_proposal", self.request.id, duration, tender_id=tender_id)
        
        return {
            "status": "success",
            "tender_id": tender_id,
            "proposal_id": result.get("proposal_id"),
            "duration": duration,
        }
        
    except Exception as e:
        log_task_error("generate_proposal", self.request.id, e, tender_id=tender_id)
        raise
