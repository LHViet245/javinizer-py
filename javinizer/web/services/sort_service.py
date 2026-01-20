from pathlib import Path
from typing import Optional, Dict, Any

# Javinizer Core Imports
from javinizer.config import settings as global_settings
from javinizer.matcher import extract_movie_id, find_video_files
from javinizer.sorter import SortConfig, generate_sort_paths, execute_sort
from javinizer.downloader import ImageDownloader
from javinizer.nfo import generate_nfo
from javinizer.cli_helpers import process_thumbnails, translate_metadata_if_enabled
from javinizer.cli_common import scrape_parallel
from javinizer.aggregator import aggregate_metadata
from javinizer.web.services.job_manager import job_manager

class SortService:
    @staticmethod
    async def process_directory(
        job_id: str,
        input_dir: str, 
        dest_dir: str, 
        recursive: bool = False, 
        dry_run: bool = True
    ):
        """
        Process a directory of videos.
        Updates job progress via job_manager.
        """
        input_path = Path(input_dir)
        videos = find_video_files(input_path, recursive=recursive)
        
        total = len(videos)
        if total == 0:
            job_manager.update_job(job_id, status="completed", message="No videos found", result={"processed": 0})
            return

        results = []
        processed = 0
        
        for video in videos:
            if not job_manager.get_job(job_id).status == "running":
                 # Handle cancellation if needed
                 break

            processed += 1
            progress = int((processed / total) * 100)
            job_manager.update_job(job_id, progress=progress, message=f"Processing {video.name}...")

            try:
                # Process single video
                res = await SortService.process_single_video(
                    video_path=video,
                    dest_path=Path(dest_dir),
                    dry_run=dry_run
                )
                results.append(res)
            except Exception as e:
                results.append({"file": video.name, "status": "error", "error": str(e)})

        job_manager.update_job(
            job_id, 
            status="completed", 
            message=f"Processed {total} files", 
            result={"items": results}
        )

    @staticmethod
    async def process_single_video(
        video_path: Path, 
        dest_path: Optional[Path] = None, 
        dry_run: bool = True
    ) -> Dict[str, Any]:
        """
        Process a single video: Scrape -> Sort -> Post-process.
        """
        movie_id = extract_movie_id(video_path.name)
        if not movie_id:
            return {"file": video_path.name, "status": "skipped", "reason": "No ID found"}

        # 1. Scrape
        # For simplicity, using global settings and console print (which will be captured by log broadcaster later)
        # In a real impl, we should pass a custom logger or capture stdout.
        
        # sources = ["r18dev", "dmm_new"] # Default sources, should come from request
        sources = ["r18dev", "dmm_new"] 
        
        scrape_results = scrape_parallel(movie_id, sources, global_settings.proxy, global_settings, None) # None console to suppress?
        
        if not scrape_results:
             return {"file": video_path.name, "status": "skipped", "reason": "Metadata not found"}
        
        metadata = list(scrape_results.values())[0] if len(scrape_results) == 1 else aggregate_metadata(scrape_results, global_settings.priority)
        
        if not metadata:
             return {"file": video_path.name, "status": "error", "error": "Aggregation failed"}

        # 2. Config
        sort_config = SortConfig(
             folder_format=global_settings.sort.folder_format,
             file_format=global_settings.sort.file_format,
             nfo_format=global_settings.sort.nfo_format,
             output_folder=global_settings.sort.output_folder,
             poster_filename=global_settings.sort.poster_filename,
             backdrop_filename=global_settings.sort.backdrop_filename,
             max_title_length=global_settings.sort.max_title_length,
             move_to_folder=True,
             rename_file=True,
             create_nfo=global_settings.sort.create_nfo,
             download_images=global_settings.sort.download_images,
             move_subtitles=global_settings.sort.move_subtitles,
        )

        dest = dest_path if dest_path else video_path.parent
        paths = generate_sort_paths(video_path, dest, metadata, sort_config)

        result_info = {
            "file": video_path.name,
            "movie_id": movie_id,
            "title": metadata.title,
            "source": str(paths.video_path),
            "destination": str(paths.folder_path),
            "preview": {
                "folder": str(paths.folder_path),
                "video": paths.video_path.name,
                "nfo": paths.nfo_path.name if paths.nfo_path else None
            }
        }

        if dry_run:
            result_info["status"] = "preview"
            return result_info

        # 3. Execute
        success = execute_sort(paths, move=True, dry_run=False) # Configurable move/copy
        if not success:
            return {"file": video_path.name, "status": "error", "error": "File move failed"}

        # 4. Post-process (Downloads, NFO)
        # Simplified Async Download
        if sort_config.download_images and metadata.cover_url:
             downloader = ImageDownloader(timeout=global_settings.timeout)
             if paths.backdrop_path and paths.poster_path:
                 await downloader.download_cover_and_poster(
                     metadata.cover_url, paths.backdrop_path, paths.poster_path
                 )

        process_thumbnails(metadata, global_settings)
        translate_metadata_if_enabled(metadata, global_settings)

        if sort_config.create_nfo and paths.nfo_path:
            nfo_content = generate_nfo(
                metadata,
                poster_filename=sort_config.poster_filename,
                backdrop_filename=sort_config.backdrop_filename,
                use_japanese_names=global_settings.sort.actress_language_ja,
            )
            paths.nfo_path.write_text(nfo_content, encoding="utf-8")

        result_info["status"] = "success"
        return result_info
