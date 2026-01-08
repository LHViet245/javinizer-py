"""Configuration management for Javinizer"""

import json
from pathlib import Path
from typing import Optional

from javinizer.models import Settings


# Default config locations
DEFAULT_CONFIG_FILENAME = "jvSettings.json"


def get_config_path() -> Path:
    """Get the default config file path"""
    # 1. Check current working directory (user override)
    cwd_config = Path.cwd() / DEFAULT_CONFIG_FILENAME
    if cwd_config.exists():
        return cwd_config

    # 2. Check project root (portable mode) - parent of 'javinizer' package
    project_root = Path(__file__).parent.parent
    project_config = project_root / DEFAULT_CONFIG_FILENAME
    if project_config.exists():
        return project_config

    # 3. Default to project root for new files (Enforce Portable)
    return project_config


def load_settings(config_path: Optional[Path] = None) -> Settings:
    """
    Load settings from JSON file

    Args:
        config_path: Path to config file. If None, uses default location.

    Returns:
        Settings object
    """
    if config_path is None:
        config_path = get_config_path()

    if not config_path.exists():
        # Return default settings if no config file
        return Settings()

    try:
        with open(config_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return Settings.model_validate(data)
    except Exception as e:
        from rich.console import Console
        Console().print(f"[yellow]Warning: Could not load config from {config_path}: {e}[/]")
        return Settings()


def save_settings(settings: Settings, config_path: Optional[Path] = None) -> Path:
    """
    Save settings to JSON file

    Args:
        settings: Settings object to save
        config_path: Path to save to. If None, uses default location.

    Returns:
        Path where config was saved
    """
    if config_path is None:
        config_path = get_config_path()

    # Create parent directory if needed
    config_path.parent.mkdir(parents=True, exist_ok=True)

    # Convert to dict (excluding None values for cleaner JSON)
    data = settings.model_dump(mode="json", exclude_none=True)

    with open(config_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    return config_path


def create_default_config(config_path: Optional[Path] = None) -> Path:
    """Create a default config file"""
    settings = Settings()
    return save_settings(settings, config_path)


def update_proxy(proxy_url: Optional[str], config_path: Optional[Path] = None) -> Settings:
    """
    Update proxy settings

    Args:
        proxy_url: Proxy URL (e.g., "socks5://127.0.0.1:1080") or None to disable
        config_path: Config file path

    Returns:
        Updated settings
    """
    settings = load_settings(config_path)

    if proxy_url:
        settings.proxy.enabled = True
        settings.proxy.url = proxy_url
    else:
        settings.proxy.enabled = False
        settings.proxy.url = None

    save_settings(settings, config_path)
    return settings
