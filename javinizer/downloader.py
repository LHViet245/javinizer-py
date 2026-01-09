"""Image downloading and poster creation for JAV covers"""

import asyncio
from pathlib import Path
from typing import Optional
from urllib.parse import urlparse

import httpx

# Try to import Pillow for image cropping
try:
    from PIL import Image
    PILLOW_AVAILABLE = True
except ImportError:
    PILLOW_AVAILABLE = False

# Poster crop ratio for JAV covers
# JAV covers are typically ~800x538px, with the actress on the right ~52.8%
# This ratio (1.895734597) gives us the right 52.8% of the image for the poster
POSTER_CROP_RATIO = 1.895734597


class ImageDownloader:
    """Download images with proxy support and create posters"""

    def __init__(
        self,
        proxy: Optional[str] = None,
        timeout: float = 30.0,
        user_agent: str = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    ):
        """
        Initialize image downloader.

        Args:
            proxy: Proxy URL (e.g., "socks5://127.0.0.1:1080")
            timeout: Request timeout in seconds
            user_agent: User-Agent header
        """
        self.proxy = proxy
        self.timeout = timeout
        self.user_agent = user_agent

    def _get_client(self) -> httpx.AsyncClient:
        """Create HTTP client with configured settings"""
        return httpx.AsyncClient(
            proxy=self.proxy,
            timeout=self.timeout,
            headers={"User-Agent": self.user_agent},
            follow_redirects=True,
        )

    async def download_image(self, url: str, dest_path: Path) -> bool:
        """
        Download image from URL to destination path.

        Args:
            url: Image URL
            dest_path: Destination file path

        Returns:
            True if successful, False otherwise
        """
        if not url:
            return False

        try:
            async with self._get_client() as client:
                response = await client.get(url)
                response.raise_for_status()

                # Ensure parent directory exists
                dest_path.parent.mkdir(parents=True, exist_ok=True)

                # Write image data
                dest_path.write_bytes(response.content)
                return True

        except Exception as e:
            print(f"Error downloading image from {url}: {e}")
            return False

    async def download_cover_and_poster(
        self,
        cover_url: str,
        backdrop_path: Path,
        poster_path: Path
    ) -> tuple[bool, bool]:
        """
        Download cover image as backdrop and create cropped poster.

        Args:
            cover_url: Cover image URL (full cover)
            backdrop_path: Destination for backdrop (full image)
            poster_path: Destination for poster (cropped right side)

        Returns:
            Tuple of (backdrop_success, poster_success)
        """
        # Download backdrop first
        backdrop_ok = await self.download_image(cover_url, backdrop_path)

        if not backdrop_ok:
            return False, False

        # Create poster by cropping
        poster_ok = self.create_poster(backdrop_path, poster_path)

        return backdrop_ok, poster_ok

    def create_poster(self, source_path: Path, poster_path: Path) -> bool:
        """
        Create poster by cropping right portion of cover image.

        JAV covers typically have the actress on the right side.
        We crop approximately 52.8% from the right (ratio 1.895734597).

        Args:
            source_path: Source image path (full cover)
            poster_path: Destination poster path

        Returns:
            True if successful, False otherwise
        """
        if not PILLOW_AVAILABLE:
            print("Pillow not installed. Cannot create poster.")
            return False

        if not source_path.exists():
            return False

        try:
            with Image.open(source_path) as img:
                width, height = img.size

                # Crop right portion of image using standard poster ratio
                left = width / POSTER_CROP_RATIO

                top = 0
                right = width
                bottom = height

                cropped = img.crop((int(left), int(top), int(right), int(bottom)))

                # Ensure parent directory exists
                poster_path.parent.mkdir(parents=True, exist_ok=True)

                # Save as JPEG
                if cropped.mode in ('RGBA', 'P'):
                    cropped = cropped.convert('RGB')
                cropped.save(poster_path, 'JPEG', quality=95)

                return True

        except Exception as e:
            print(f"Error creating poster: {e}")
            return False

    async def download_screenshots(
        self,
        urls: list[str],
        dest_folder: Path,
        prefix: str = "screenshot"
    ) -> int:
        """
        Download multiple screenshot images.

        Args:
            urls: List of screenshot URLs
            dest_folder: Destination folder
            prefix: Filename prefix

        Returns:
            Number of successfully downloaded images
        """
        if not urls:
            return 0

        dest_folder.mkdir(parents=True, exist_ok=True)
        success_count = 0

        for i, url in enumerate(urls, 1):
            ext = self._get_extension(url)
            dest_path = dest_folder / f"{prefix}-{i:02d}{ext}"

            if await self.download_image(url, dest_path):
                success_count += 1

        return success_count

    def _get_extension(self, url: str) -> str:
        """Extract file extension from URL"""
        parsed = urlparse(url)
        path = parsed.path.lower()

        if path.endswith('.jpg') or path.endswith('.jpeg'):
            return '.jpg'
        elif path.endswith('.png'):
            return '.png'
        elif path.endswith('.webp'):
            return '.webp'
        else:
            return '.jpg'  # Default


def download_image_sync(
    url: str,
    dest_path: Path,
    proxy: Optional[str] = None,
    timeout: float = 30.0
) -> bool:
    """
    Synchronous wrapper for downloading a single image.

    Args:
        url: Image URL
        dest_path: Destination file path
        proxy: Optional proxy URL
        timeout: Request timeout

    Returns:
        True if successful, False otherwise
    """
    downloader = ImageDownloader(proxy=proxy, timeout=timeout)
    return asyncio.run(downloader.download_image(url, dest_path))


def create_poster_sync(source_path: Path, poster_path: Path) -> bool:
    """
    Synchronous wrapper for creating poster.

    Args:
        source_path: Source image path
        poster_path: Destination poster path

    Returns:
        True if successful, False otherwise
    """
    downloader = ImageDownloader()
    return downloader.create_poster(source_path, poster_path)
