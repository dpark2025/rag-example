"""Document processing status tracker."""

import time
from datetime import datetime
from typing import Dict, List, Optional
from enum import Enum
from dataclasses import dataclass, asdict


class ProcessingStatus(Enum):
    QUEUED = "queued"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class ProcessingTask:
    """Represents a document processing task."""
    doc_id: str
    filename: str
    status: ProcessingStatus
    progress: float = 0.0
    created_at: datetime = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    chunks_created: int = 0
    file_size: int = 0
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization."""
        result = asdict(self)
        result['status'] = self.status.value
        result['created_at'] = self.created_at.isoformat() if self.created_at else None
        result['started_at'] = self.started_at.isoformat() if self.started_at else None
        result['completed_at'] = self.completed_at.isoformat() if self.completed_at else None
        return result


class DocumentProcessingTracker:
    """Tracks document processing status and progress."""
    
    def __init__(self):
        self.tasks: Dict[str, ProcessingTask] = {}
        self.processing_queue: List[str] = []
    
    def create_task(self, doc_id: str, filename: str, file_size: int = 0) -> ProcessingTask:
        """Create a new processing task."""
        task = ProcessingTask(
            doc_id=doc_id,
            filename=filename,
            status=ProcessingStatus.QUEUED,
            file_size=file_size
        )
        self.tasks[doc_id] = task
        self.processing_queue.append(doc_id)
        return task
    
    def start_processing(self, doc_id: str) -> bool:
        """Mark a task as started."""
        if doc_id not in self.tasks:
            return False
        
        task = self.tasks[doc_id]
        task.status = ProcessingStatus.PROCESSING
        task.started_at = datetime.now()
        task.progress = 10.0  # Started
        
        # Remove from queue
        if doc_id in self.processing_queue:
            self.processing_queue.remove(doc_id)
        
        return True
    
    def update_progress(self, doc_id: str, progress: float, message: str = None):
        """Update task progress."""
        if doc_id not in self.tasks:
            return False
        
        task = self.tasks[doc_id]
        task.progress = min(progress, 100.0)
        
        if message:
            task.error_message = message
        
        return True
    
    def complete_task(self, doc_id: str, chunks_created: int = 0):
        """Mark a task as completed."""
        if doc_id not in self.tasks:
            return False
        
        task = self.tasks[doc_id]
        task.status = ProcessingStatus.COMPLETED
        task.completed_at = datetime.now()
        task.progress = 100.0
        task.chunks_created = chunks_created
        
        return True
    
    def fail_task(self, doc_id: str, error_message: str):
        """Mark a task as failed."""
        if doc_id not in self.tasks:
            return False
        
        task = self.tasks[doc_id]
        task.status = ProcessingStatus.FAILED
        task.completed_at = datetime.now()
        task.error_message = error_message
        
        # Remove from queue
        if doc_id in self.processing_queue:
            self.processing_queue.remove(doc_id)
        
        return True
    
    def get_task(self, doc_id: str) -> Optional[ProcessingTask]:
        """Get a specific task."""
        return self.tasks.get(doc_id)
    
    def get_all_tasks(self) -> List[ProcessingTask]:
        """Get all tasks."""
        return list(self.tasks.values())
    
    def get_tasks_by_status(self, status: ProcessingStatus) -> List[ProcessingTask]:
        """Get tasks filtered by status."""
        return [task for task in self.tasks.values() if task.status == status]
    
    def get_queue_status(self) -> Dict:
        """Get processing queue status."""
        return {
            "queued": len(self.get_tasks_by_status(ProcessingStatus.QUEUED)),
            "processing": len(self.get_tasks_by_status(ProcessingStatus.PROCESSING)),
            "completed": len(self.get_tasks_by_status(ProcessingStatus.COMPLETED)),
            "failed": len(self.get_tasks_by_status(ProcessingStatus.FAILED)),
            "total": len(self.tasks)
        }
    
    def cleanup_old_tasks(self, max_age_hours: int = 24):
        """Clean up old completed/failed tasks."""
        cutoff_time = datetime.now().timestamp() - (max_age_hours * 3600)
        
        to_remove = []
        for doc_id, task in self.tasks.items():
            if task.status in [ProcessingStatus.COMPLETED, ProcessingStatus.FAILED]:
                if task.completed_at and task.completed_at.timestamp() < cutoff_time:
                    to_remove.append(doc_id)
        
        for doc_id in to_remove:
            del self.tasks[doc_id]
        
        return len(to_remove)


# Global tracker instance
processing_tracker = DocumentProcessingTracker()