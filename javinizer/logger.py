"""Logging configuration for Javinizer"""

import logging
from pathlib import Path
from typing import Optional

from rich.logging import RichHandler
from rich.console import Console

# Create centralized console (shared with CLI)
console = Console()

def configure_logging(
    verbose: bool = False,
    log_file: Optional[str] = None,
    console_output: bool = False
) -> logging.Logger:
    """
    Configure global logging

    Args:
        verbose: Enable DEBUG level logging
        log_file: Path to log file (if None, no file logging)
        console_output: Enable console logging via RichHandler
                        (usually disabled for CLI tools that manage their own output,
                         but useful for debugging)
    """
    root_logger = logging.getLogger("javinizer")
    root_logger.setLevel(logging.DEBUG if verbose else logging.INFO)

    # Clear existing handlers
    root_logger.handlers = []

    # File Handler
    if log_file:
        try:
            file_path = Path(log_file)
            # Ensure directory exists
            file_path.parent.mkdir(parents=True, exist_ok=True)
            
            file_handler = logging.FileHandler(file_path, encoding="utf-8")
            file_handler.setLevel(logging.DEBUG)  # Always log everything to file
            
            # Format: Time - Level - Module:Line - Message
            formatter = logging.Formatter(
                "%(asctime)s - %(levelname)s - %(name)s:%(lineno)d - %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S"
            )
            file_handler.setFormatter(formatter)
            root_logger.addHandler(file_handler)
        except Exception as e:
            console.print(f"[red]Failed to setup log file '{log_file}': {e}[/]")

    # Console Handler (Rich) - Optional
    # For CLI tools, we often want to control output manually with console.print,
    # so we might not add this handler by default unless --verbose is used
    # or specifically requested.
    if verbose or console_output:
        rich_handler = RichHandler(
            console=console,
            show_time=False,
            show_path=False,
            rich_tracebacks=True,
            markup=True
        )
        rich_handler.setLevel(logging.DEBUG if verbose else logging.INFO)
        root_logger.addHandler(rich_handler)

    # Silence other libraries
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("undetected_chromedriver").setLevel(logging.WARNING)

    return root_logger

def get_logger(name: str) -> logging.Logger:
    """Get a child logger for a module"""
    return logging.getLogger(f"javinizer.{name}")
