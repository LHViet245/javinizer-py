import logging
import uuid
from datetime import datetime
from typing import Dict, Optional
from pydantic import BaseModel

logger = logging.getLogger("javinizer")

class JobStatus(BaseModel):
    id: str
    type: str
    status: str  # "pending", "running", "completed", "failed"
    progress: int = 0
    message: str = ""
    created_at: datetime
    result: Optional[dict] = None

class JobManager:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(JobManager, cls).__new__(cls)
            cls._instance.jobs: Dict[str, JobStatus] = {}
        return cls._instance

    def create_job(self, job_type: str) -> str:
        job_id = str(uuid.uuid4())
        self.jobs[job_id] = JobStatus(
            id=job_id,
            type=job_type,
            status="pending",
            created_at=datetime.now()
        )
        return job_id

    def update_job(self, job_id: str, status: str = None, progress: int = None, message: str = None, result: dict = None):
        if job_id in self.jobs:
            job = self.jobs[job_id]
            if status:
                job.status = status
            if progress is not None:
                job.progress = progress
            if message:
                job.message = message
                # Broadcast message via logger for SSE stream
                logger.info(f"[{job.type}] {message}")
            if result:
                job.result = result

    def get_job(self, job_id: str) -> Optional[JobStatus]:
        return self.jobs.get(job_id)

    def list_jobs(self):
        return list(self.jobs.values())

    def cleanup_old_jobs(self, max_age_hours: int = 24) -> int:
        """
        Remove completed/failed jobs older than max_age_hours.
        Returns the number of jobs cleaned up.
        """
        from datetime import timedelta
        cutoff = datetime.now() - timedelta(hours=max_age_hours)
        
        old_job_ids = [
            job_id for job_id, job in self.jobs.items()
            if job.created_at < cutoff and job.status in ["completed", "failed"]
        ]
        
        for job_id in old_job_ids:
            del self.jobs[job_id]
        
        return len(old_job_ids)

    def get_stats(self) -> dict:
        """Get job manager statistics"""
        from collections import Counter
        status_counts = Counter(job.status for job in self.jobs.values())
        return {
            "total_jobs": len(self.jobs),
            "pending": status_counts.get("pending", 0),
            "running": status_counts.get("running", 0),
            "completed": status_counts.get("completed", 0),
            "failed": status_counts.get("failed", 0),
        }

job_manager = JobManager()
