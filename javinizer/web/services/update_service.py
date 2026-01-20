from pathlib import Path
from javinizer.web.services.job_manager import job_manager
from javinizer.matcher import find_video_files
from javinizer.updater import update_video_metadata
from javinizer.config import settings as global_settings

class UpdateService:
    @staticmethod
    async def process_path(job_id: str, target_path: str):
        """
        Process a path (file or directory) for metadata update.
        """
        path = Path(target_path)
        if path.is_dir():
            videos = find_video_files(path, recursive=False)
            total = len(videos)
            if total == 0:
                return
            
            for i, video in enumerate(videos):
                job_manager.update_job(job_id, message=f"Updating {video.name}...")
                await UpdateService.update_file(video)
                # Note: Progress is handled by the calling run_update_job for the batch
        else:
            job_manager.update_job(job_id, message=f"Updating {path.name}...")
            await UpdateService.update_file(path)

    @staticmethod
    async def update_file(video_path: Path):
        """
        Update metadata for a single video file.
        """
        # This is a synchronous operation in the core, so we wrap it or just call it
        # In a real async app, we'd use run_in_executor
        try:
            # update_video_metadata handles the scraping and NFO/Image update
            update_video_metadata(video_path, global_settings)
        except Exception as e:
            import logging
            logger = logging.getLogger("javinizer")
            logger.error(f"Failed to update {video_path}: {e}")
            raise e
