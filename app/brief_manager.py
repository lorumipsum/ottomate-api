"""
Brief and Job Management System for OttoMate API.
"""

import json
import uuid
import time
import logging
from typing import Dict, Any, Optional, List
from pathlib import Path
from dataclasses import dataclass, asdict
from enum import Enum
from threading import Lock

logger = logging.getLogger(__name__)

class JobStatus(Enum):
    """Job status enumeration."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"

@dataclass
class Brief:
    """Brief data structure."""
    id: str
    content: str
    created_at: float
    metadata: Dict[str, Any]

@dataclass
class Job:
    """Job data structure."""
    id: str
    brief_id: str
    status: JobStatus
    created_at: float
    started_at: Optional[float] = None
    completed_at: Optional[float] = None
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

class BriefManager:
    """Manages brief storage and job tracking."""
    
    def __init__(self, storage_dir: str = "data"):
        self.storage_dir = Path(storage_dir)
        self.briefs_dir = self.storage_dir / "briefs"
        self.jobs_dir = self.storage_dir / "jobs"
        
        # Create directories if they don't exist
        self.briefs_dir.mkdir(parents=True, exist_ok=True)
        self.jobs_dir.mkdir(parents=True, exist_ok=True)
        
        # Thread safety
        self.lock = Lock()
        
        logger.info(f"BriefManager initialized with storage at {self.storage_dir}")
    
    def create_brief(self, content: str, metadata: Optional[Dict[str, Any]] = None) -> Brief:
        """Create and store a new brief."""
        with self.lock:
            brief_id = str(uuid.uuid4())
            brief = Brief(
                id=brief_id,
                content=content.strip(),
                created_at=time.time(),
                metadata=metadata or {}
            )
            
            # Save to file
            brief_file = self.briefs_dir / f"{brief_id}.json"
            with open(brief_file, 'w') as f:
                json.dump(asdict(brief), f, indent=2)
            
            logger.info(f"Created brief {brief_id}")
            return brief
    
    def get_brief(self, brief_id: str) -> Optional[Brief]:
        """Retrieve a brief by ID."""
        brief_file = self.briefs_dir / f"{brief_id}.json"
        
        if not brief_file.exists():
            return None
        
        try:
            with open(brief_file, 'r') as f:
                data = json.load(f)
            return Brief(**data)
        except Exception as e:
            logger.error(f"Failed to load brief {brief_id}: {e}")
            return None
    
    def list_briefs(self, limit: int = 50) -> List[Brief]:
        """List all briefs, most recent first."""
        briefs = []
        
        try:
            # Get all brief files
            brief_files = list(self.briefs_dir.glob("*.json"))
            
            # Sort by modification time (most recent first)
            brief_files.sort(key=lambda f: f.stat().st_mtime, reverse=True)
            
            # Load briefs up to limit
            for brief_file in brief_files[:limit]:
                try:
                    with open(brief_file, 'r') as f:
                        data = json.load(f)
                    briefs.append(Brief(**data))
                except Exception as e:
                    logger.warning(f"Failed to load brief from {brief_file}: {e}")
                    
        except Exception as e:
            logger.error(f"Failed to list briefs: {e}")
        
        return briefs
    
    def create_job(self, brief_id: str) -> Optional[Job]:
        """Create a new job for a brief."""
        # Verify brief exists
        if not self.get_brief(brief_id):
            logger.warning(f"Cannot create job: brief {brief_id} not found")
            return None
        
        with self.lock:
            job_id = str(uuid.uuid4())
            job = Job(
                id=job_id,
                brief_id=brief_id,
                status=JobStatus.PENDING,
                created_at=time.time()
            )
            
            # Save to file
            job_file = self.jobs_dir / f"{job_id}.json"
            with open(job_file, 'w') as f:
                json.dump(self._job_to_dict(job), f, indent=2)
            
            logger.info(f"Created job {job_id} for brief {brief_id}")
            return job
    
    def get_job(self, job_id: str) -> Optional[Job]:
        """Retrieve a job by ID."""
        job_file = self.jobs_dir / f"{job_id}.json"
        
        if not job_file.exists():
            return None
        
        try:
            with open(job_file, 'r') as f:
                data = json.load(f)
            return self._dict_to_job(data)
        except Exception as e:
            logger.error(f"Failed to load job {job_id}: {e}")
            return None
    
    def update_job(self, job: Job) -> bool:
        """Update a job's status and data."""
        try:
            with self.lock:
                job_file = self.jobs_dir / f"{job.id}.json"
                with open(job_file, 'w') as f:
                    json.dump(self._job_to_dict(job), f, indent=2)
                
                logger.info(f"Updated job {job.id} status to {job.status.value}")
                return True
        except Exception as e:
            logger.error(f"Failed to update job {job.id}: {e}")
            return False
    
    def list_jobs(self, brief_id: Optional[str] = None, limit: int = 50) -> List[Job]:
        """List jobs, optionally filtered by brief ID."""
        jobs = []
        
        try:
            # Get all job files
            job_files = list(self.jobs_dir.glob("*.json"))
            
            # Sort by modification time (most recent first)
            job_files.sort(key=lambda f: f.stat().st_mtime, reverse=True)
            
            # Load jobs up to limit
            for job_file in job_files[:limit * 2]:  # Load extra in case we need to filter
                try:
                    with open(job_file, 'r') as f:
                        data = json.load(f)
                    job = self._dict_to_job(data)
                    
                    # Filter by brief_id if specified
                    if brief_id is None or job.brief_id == brief_id:
                        jobs.append(job)
                        
                    # Stop if we have enough
                    if len(jobs) >= limit:
                        break
                        
                except Exception as e:
                    logger.warning(f"Failed to load job from {job_file}: {e}")
                    
        except Exception as e:
            logger.error(f"Failed to list jobs: {e}")
        
        return jobs
    
    def _job_to_dict(self, job: Job) -> Dict[str, Any]:
        """Convert Job object to dictionary for JSON serialization."""
        data = asdict(job)
        data['status'] = job.status.value  # Convert enum to string
        return data
    
    def _dict_to_job(self, data: Dict[str, Any]) -> Job:
        """Convert dictionary to Job object."""
        data['status'] = JobStatus(data['status'])  # Convert string to enum
        return Job(**data)

# Global instance
brief_manager = BriefManager()
