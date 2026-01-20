import os
from pathlib import Path
from typing import List, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter()

class FileItem(BaseModel):
    name: str
    path: str
    type: str  # "directory" or "file"
    size: Optional[int] = None
    has_children: bool = False


def validate_path(path: str) -> Path:
    """
    Validate and sanitize file path to prevent path traversal attacks.
    
    Security checks:
    1. Block explicit '..' in path
    2. Resolve to absolute path and verify it's a real directory
    3. Prevent null bytes and other injection attempts
    """
    # Block null bytes (common injection attack)
    if '\x00' in path:
        raise HTTPException(status_code=400, detail="Invalid path: null bytes not allowed")
    
    # Block explicit path traversal attempts
    if '..' in path:
        raise HTTPException(status_code=400, detail="Invalid path: traversal not allowed")
    
    # Resolve to absolute path (this also normalizes the path)
    try:
        target = Path(path).resolve(strict=False)
    except (OSError, ValueError) as e:
        raise HTTPException(status_code=400, detail=f"Invalid path: {e}")
    
    # On Windows, verify drive letter exists
    if os.name == 'nt':
        drive = target.drive
        if not drive or not Path(drive + "\\").exists():
            raise HTTPException(status_code=404, detail="Drive not found")
    
    return target


@router.get("/list", response_model=List[FileItem])
async def list_directory(path: Optional[str] = None, q: Optional[str] = None):
    """
    List contents of a directory.
    If path is None, lists available drives (Windows) or root (Linux).
    """
    items = []
    
    if path is None:
        # List Drives on Windows
        if os.name == 'nt':
            import string
            drives = []
            bitmask = None
            try:
                # Use ctypes to get available drives
                import ctypes
                bitmask = ctypes.windll.kernel32.GetLogicalDrives()
                for letter in string.ascii_uppercase:
                    if bitmask & 1:
                        drives.append(f"{letter}:\\")
                    bitmask >>= 1
                
                for drive in drives:
                     items.append(FileItem(
                        name=drive,
                        path=drive,
                        type="drive",
                        has_children=True
                    ))
                return items
            except Exception:
                # Fallback if ctypes fails, just start at C:\
                return [FileItem(name="C:\\", path="C:\\", type="drive", has_children=True)]
        else:
            # On Linux/Mac, start at /
             return [FileItem(name="/", path="/", type="directory", has_children=True)]

    # Validate and sanitize path (SECURITY FIX)
    target_path = validate_path(path)
    if not target_path.exists() or not target_path.is_dir():
        raise HTTPException(status_code=404, detail="Directory not found")


    try:
        # Scan directory
        with os.scandir(target_path) as it:
            entries = list(it)
            # Sort: Directories first, then files
            entries.sort(key=lambda e: (not e.is_dir(), e.name.lower()))
            
            for entry in entries:
                # Skip hidden files/dirs
                if entry.name.startswith('.'):
                    continue

                # Filter by query if provided
                if q and q.lower() not in entry.name.lower():
                    continue
                
                # Basic info
                is_dir = entry.is_dir()
                item = FileItem(
                    name=entry.name,
                    path=entry.path,
                    type="directory" if is_dir else "file",
                    size=entry.stat().st_size if not is_dir else None,
                    has_children=is_dir # Simplification: Assume all dirs have children for lazyness
                )
                items.append(item)
                
    except PermissionError:
        raise HTTPException(status_code=403, detail="Permission denied")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    return items
