"""
Job Runner for asynchronous blueprint generation.
"""

import time
import logging
import threading
from typing import Optional

from app.brief_manager import brief_manager, Job, JobStatus
from app.blueprint_generator import blueprint_generator

logger = logging.getLogger(__name__)

class JobRunner:
    """Runs blueprint generation jobs asynchronously."""
    
    def __init__(self):
        self.running_jobs = {}  # job_id -> thread
        
    def start_job(self, job_id: str) -> bool:
        """Start a blueprint generation job."""
        # Get the job
        job = brief_manager.get_job(job_id)
        if not job:
            logger.error(f"Job {job_id} not found")
            return False
        
        # Check if job is already running
        if job_id in self.running_jobs:
            logger.warning(f"Job {job_id} is already running")
            return False
        
        # Check if job is in correct state
        if job.status != JobStatus.PENDING:
            logger.warning(f"Job {job_id} is not in pending state (current: {job.status.value})")
            return False
        
        # Get the brief
        brief = brief_manager.get_brief(job.brief_id)
        if not brief:
            logger.error(f"Brief {job.brief_id} not found for job {job_id}")
            self._fail_job(job, "Brief not found")
            return False
        
        # Start the job in a separate thread
        thread = threading.Thread(
            target=self._run_job,
            args=(job, brief.content),
            daemon=True
        )
        
        self.running_jobs[job_id] = thread
        thread.start()
        
        logger.info(f"Started job {job_id} for brief {job.brief_id}")
        return True
    
    def _run_job(self, job: Job, brief_content: str):
        """Run a blueprint generation job."""
        try:
            # Update job status to running
            job.status = JobStatus.RUNNING
            job.started_at = time.time()
            brief_manager.update_job(job)
            
            logger.info(f"Running job {job.id}")
            
            # Generate blueprint
            success, result = blueprint_generator.generate_blueprint(brief_content)
            
            if success:
                # Job completed successfully
                job.status = JobStatus.COMPLETED
                job.completed_at = time.time()
                job.result = {
                    "blueprint": result["blueprint"],
                    "generated_at": job.completed_at
                }
                logger.info(f"Job {job.id} completed successfully")
            else:
                # Job failed
                job.status = JobStatus.FAILED
                job.completed_at = time.time()
                job.error = result["error"]
                job.result = {
                    "violations": result.get("violations", []),
                    "failed_at": job.completed_at
                }
                logger.error(f"Job {job.id} failed: {job.error}")
            
            # Update job in storage
            brief_manager.update_job(job)
            
        except Exception as e:
            logger.error(f"Exception in job {job.id}: {e}")
            self._fail_job(job, f"Internal error: {str(e)}")
        
        finally:
            # Remove from running jobs
            if job.id in self.running_jobs:
                del self.running_jobs[job.id]
    
    def _fail_job(self, job: Job, error_message: str):
        """Mark a job as failed."""
        job.status = JobStatus.FAILED
        job.completed_at = time.time()
        job.error = error_message
        job.result = {
            "failed_at": job.completed_at
        }
        brief_manager.update_job(job)
        
        # Remove from running jobs if present
        if job.id in self.running_jobs:
            del self.running_jobs[job.id]
    
    def get_running_jobs(self) -> list:
        """Get list of currently running job IDs."""
        return list(self.running_jobs.keys())
    
    def is_job_running(self, job_id: str) -> bool:
        """Check if a job is currently running."""
        return job_id in self.running_jobs

# Global instance
job_runner = JobRunner()
