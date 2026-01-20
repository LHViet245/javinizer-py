from fastapi import APIRouter, BackgroundTasks
from pydantic import BaseModel
from typing import List, Optional
from javinizer.web.services.job_manager import job_manager

router = APIRouter()

class BatchRequest(BaseModel):
    paths: List[str]
    dest: Optional[str] = None
    recursive: bool = False
    dry_run: bool = True

class SortRequest(BaseModel):
    path: str
    dest: Optional[str] = None
    recursive: bool = False
    dry_run: bool = True

@router.post("/sort")
async def trigger_sort(request: SortRequest, background_tasks: BackgroundTasks):
    """Trigger a sort operation (Dry run or Execute)"""
    job_type = "sort_preview" if request.dry_run else "sort_execute"
    job_id = job_manager.create_job(job_type)
    
    # Add to background tasks
    background_tasks.add_task(run_sort_job, job_id, [request.path], request.dest, request.recursive, request.dry_run)
    
    return {"job_id": job_id, "status": "pending"}

@router.post("/batch/sort")
async def trigger_batch_sort(request: BatchRequest, background_tasks: BackgroundTasks):
    """Trigger a batch sort operation"""
    job_type = "batch_sort_preview" if request.dry_run else "batch_sort_execute"
    job_id = job_manager.create_job(job_type)
    
    background_tasks.add_task(run_sort_job, job_id, request.paths, request.dest, request.recursive, request.dry_run)
    
    return {"job_id": job_id, "status": "pending"}

@router.get("/job/{job_id}")
async def get_job_status(job_id: str):
    job = job_manager.get_job(job_id)
    if not job:
        return {"error": "Job not found"}
    return job

@router.post("/batch/update")
async def trigger_batch_update(request: BatchRequest, background_tasks: BackgroundTasks):
    """Trigger a batch update operation"""
    job_id = job_manager.create_job("batch_update")
    background_tasks.add_task(run_update_job, job_id, request.paths)
    return {"job_id": job_id, "status": "pending"}

async def run_sort_job(job_id: str, paths: List[str], dest: Optional[str], recursive: bool, dry_run: bool):
    """Background task wrapper for sort logic"""
    job_manager.update_job(job_id, status="running", progress=0, message="Starting sort...")
    
    try:
        from javinizer.web.services.sort_service import SortService

        # Process each path
        total = len(paths)
        for i, path in enumerate(paths):
            current_dest = dest if dest else path
            job_manager.update_job(job_id, message=f"Processing {i+1}/{total}: {path}")
            
            await SortService.process_directory(
                job_id=job_id,
                input_dir=path,
                dest_dir=current_dest, 
                recursive=recursive,
                dry_run=dry_run
            )
            job_manager.update_job(job_id, progress=int(((i+1)/total)*100))
            
        job_manager.update_job(job_id, status="completed", message="Batch sort finished")
        
    except Exception as e:
        job_manager.update_job(job_id, status="failed", message=str(e))

async def run_update_job(job_id: str, paths: List[str]):
    """Background task wrapper for update logic"""
    job_manager.update_job(job_id, status="running", progress=0, message="Starting batch update...")
    
    try:
        from javinizer.web.services.update_service import UpdateService

        total = len(paths)
        for i, path in enumerate(paths):
            job_manager.update_job(job_id, message=f"Updating {i+1}/{total}: {path}")
            
            # Assuming UpdateService has a similar process_directory or process_file
            await UpdateService.process_path(
                job_id=job_id,
                target_path=path
            )
            job_manager.update_job(job_id, progress=int(((i+1)/total)*100))
            
        job_manager.update_job(job_id, status="completed", message="Batch update finished")
        
    except Exception as e:
        job_manager.update_job(job_id, status="failed", message=str(e))
