"""Thumbnail Database Management"""

import csv
from pathlib import Path
from typing import Optional, List
from dataclasses import dataclass

import httpx
from rich.console import Console

from javinizer.config import load_settings, get_config_path
from javinizer.models import MovieMetadata

console = Console()


@dataclass
class ActressProfile:
    name: str
    aliases: List[str]
    image_url: Optional[str] = None
    local_path: Optional[str] = None


class ActressDB:
    def __init__(self) -> None:
        self.settings = load_settings()
        self.thumbs_config = self.settings.thumbs

        # Resolve paths relative to config file if possible
        # Since config.py was updated to prefer project root, get_config_path() returns absolute path
        # Resolve paths relative to config file if possible
        # Since config.py was updated to prefer project root, get_config_path() returns absolute path
        config_dir = get_config_path().parent

        # CSV Path
        self.csv_path = Path(self.thumbs_config.csv_file)
        if not self.csv_path.is_absolute():
            self.csv_path = config_dir / self.csv_path

        # Thumbs Storage Path
        self.storage_path = Path(self.thumbs_config.storage_path)
        if not self.storage_path.is_absolute():
            self.storage_path = config_dir / self.storage_path

        self.profiles: dict[str, ActressProfile] = {}
        self.alias_map: dict[str, str] = {}  # Alias -> Canonical Name
        self._load()

    def _load(self) -> None:
        """Load database from CSV"""
        if not self.csv_path.exists():
            return

        try:
            with open(self.csv_path, "r", encoding="utf-8", newline="") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    name = row["name"].strip()
                    if not name:
                        continue

                    aliases = [
                        a.strip()
                        for a in row.get("aliases", "").split("|")
                        if a.strip()
                    ]

                    # Handle local path - resolve relative to absolute
                    local_path = row.get("local_path")
                    if local_path:
                        # Fix windows backslashes
                        local_path = local_path.replace("\\", "/")
                        try:
                            local_path_obj = Path(local_path)
                            if not local_path_obj.is_absolute():
                                local_path = str(self.storage_path / local_path)
                        except Exception:
                            pass

                    profile = ActressProfile(
                        name=name,
                        aliases=aliases,
                        image_url=row.get("image_url"),
                        local_path=local_path,
                    )
                    self.profiles[name.lower()] = profile

                    # Map aliases
                    self.alias_map[name.lower()] = name
                    for alias in aliases:
                        self.alias_map[alias.lower()] = name

        except Exception as e:
            console.print(f"[red]Error loading actress DB: {e}[/]")

    def save(self) -> None:
        """Save database to CSV"""
        fieldnames = ["name", "aliases", "image_url", "local_path"]

        # Ensure directory exists
        self.csv_path.parent.mkdir(parents=True, exist_ok=True)

        try:
            with open(self.csv_path, "w", encoding="utf-8", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                for profile in self.profiles.values():
                    # Save local_path as relative if possible
                    local_path_str = ""
                    if profile.local_path:
                        try:
                            abs_path = Path(profile.local_path).resolve()
                            storage_abs = self.storage_path.resolve()
                            if abs_path.is_relative_to(storage_abs):
                                local_path_str = str(
                                    abs_path.relative_to(storage_abs)
                                ).replace("\\", "/")
                            else:
                                local_path_str = str(abs_path)
                        except Exception:
                            local_path_str = profile.local_path

                    writer.writerow(
                        {
                            "name": profile.name,
                            "aliases": "|".join(profile.aliases),
                            "image_url": profile.image_url or "",
                            "local_path": local_path_str,
                        }
                    )
        except Exception as e:
            console.print(f"[red]Error saving actress DB: {e}[/]")

    def find(self, name: str) -> Optional[ActressProfile]:
        """Find actress by name or alias"""
        name_lower = name.lower().strip()
        canonical_name = self.alias_map.get(name_lower)
        if canonical_name:
            return self.profiles.get(canonical_name.lower())
        return None

    def add_or_update(
        self, name: str, image_url: Optional[str] = None, alias: Optional[str] = None
    ) -> ActressProfile:
        """Add new actress or update existing"""
        profile = self.find(name)

        if profile:
            # Update existing
            if image_url and not profile.image_url:
                profile.image_url = image_url
            if alias and alias.lower() not in [a.lower() for a in profile.aliases]:
                if alias.lower() != profile.name.lower():
                    profile.aliases.append(alias)
                    self.alias_map[alias.lower()] = profile.name
            self.save()
            return profile

        # Create new
        profile = ActressProfile(
            name=name, aliases=[alias] if alias else [], image_url=image_url
        )
        self.profiles[name.lower()] = profile
        self.alias_map[name.lower()] = name
        if alias:
            self.alias_map[alias.lower()] = name

        self.save()
        return profile

    async def get_local_path(self, profile: ActressProfile) -> Optional[str]:
        """Get local path for NFO, downloading if necessary"""
        if not self.thumbs_config.enabled:
            return None

        # Determine target path: thumbs/N/Name/folder.jpg
        # Use first letter folder for organization
        first_letter = profile.name[0].upper() if profile.name else "#"
        if not first_letter.isalpha():
            first_letter = "#"

        target_dir = self.storage_path / first_letter / profile.name
        target_file = target_dir / "folder.jpg"

        # Check if file exists
        # Check if file exists
        if target_file.exists():
            # Auto-repair: Update DB if path was missing or different
            try:
                if (
                    not profile.local_path
                    or Path(profile.local_path).resolve() != target_file.resolve()
                ):
                    profile.local_path = str(target_file)
                    self.save()
            except Exception:
                pass
            return self._map_path(target_file)

        # Download if enabled
        if self.thumbs_config.download_on_sort and profile.image_url:
            success = await self._download_image(profile.image_url, target_file)
            if success:
                profile.local_path = str(
                    target_file
                )  # Store absolute path in DB for reference
                self.save()
                return self._map_path(target_file)

        return None

    def _map_path(self, path: Path) -> str:
        """Apply path mapping for cross-OS support"""
        abs_path_str = str(path.resolve()).replace("\\", "/")

        for local_prefix, remote_prefix in self.thumbs_config.path_mapping.items():
            # Normalize prefix
            local_prefix = local_prefix.replace("\\", "/")
            if abs_path_str.lower().startswith(local_prefix.lower()):
                # Case-insensitive replacement of prefix
                return remote_prefix + abs_path_str[len(local_prefix) :]

        return str(path.resolve())

    async def _download_image(self, url: str, dest: Path) -> bool:
        """Download image to destination"""
        dest.parent.mkdir(parents=True, exist_ok=True)

        proxy = self.settings.proxy.httpx_proxy
        verify = self.thumbs_config.verify_ssl

        try:
            async with httpx.AsyncClient(
                proxy=proxy, verify=verify, timeout=self.settings.timeout
            ) as client:
                resp = await client.get(url, follow_redirects=True)
                resp.raise_for_status()
                # Simple check for image content type
                if "image" not in resp.headers.get("content-type", ""):
                    console.print(
                        f"[yellow]Warning: URL did not return an image: {url}[/]"
                    )
                    # Still write it? Maybe. Let's write it.

                dest.write_bytes(resp.content)
                console.print(f"[green]Downloaded thumb:[/] {dest.parent.name}")
                return True
        except Exception as e:
            console.print(
                f"[yellow]Failed to download thumb for {dest.parent.name}: {e}[/]"
            )
            return False

    async def process_metadata(self, metadata: MovieMetadata) -> None:
        """
        Process metadata to build/update actress DB.
        Downloads thumbnails locally for caching but does NOT modify
        metadata.thumb_url - NFO will use the original online URL for portability.
        """
        if not self.thumbs_config.enabled:
            return

        for actress in metadata.actresses:
            # 1. Add/Update dictionary with actress info
            if self.thumbs_config.auto_download:
                profile = self.add_or_update(
                    name=actress.japanese_name or actress.full_name,
                    image_url=actress.thumb_url,
                    alias=actress.full_name if actress.japanese_name else None,
                )
            else:
                found = self.find(actress.japanese_name or actress.full_name)
                if found is None:
                    continue
                profile = found

            # 2. Download to local cache (but don't modify metadata)
            # This keeps a local backup without affecting NFO portability
            await self.get_local_path(profile)
            # NOTE: We do NOT replace actress.thumb_url with local path
            # Jellyfin will download from the online URL and cache internally
