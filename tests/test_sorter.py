"""Tests for javinizer.sorter module"""

import pytest
from pathlib import Path
from datetime import date
from javinizer.sorter import SortConfig, generate_sort_paths
from javinizer.models import MovieMetadata, Actress


@pytest.fixture
def sample_metadata():
    return MovieMetadata(
        id="IPX-486",
        title="Test Movie Title 2024",
        maker="IdeaPocket",
        release_date=date(2024, 1, 1),  # Use proper date object
        actresses=[
            Actress(first_name="Test", last_name="Actress")
        ],  # Use Actress object
        source="dmm",
    )


@pytest.fixture
def default_config():
    return SortConfig(
        folder_format="<ID> - <TITLE> (<YEAR>)",
        file_format="<ID>",
        nfo_format="<ID>",
        # Removed: move_to_folder and rename_file (don't exist in SortConfig)
    )


def test_generate_sort_paths_basic(sample_metadata, default_config):
    video_path = Path("D:/Downloads/raw_video.mp4")
    dest_root = Path("D:/Movies")

    paths = generate_sort_paths(video_path, dest_root, sample_metadata, default_config)

    # Expected folder name: IPX-486 - Test Movie Title 2024 (2024)
    # Check folder name only to avoid drive letter issues
    expected_name = "IPX-486 - Test Movie Title 2024 (2024)"
    assert paths.folder_path.name == expected_name
    assert paths.folder_path.parent == dest_root

    # Expected file name: IPX-486.mp4
    assert paths.video_path.name == "IPX-486.mp4"
    assert paths.nfo_path.name == "IPX-486.nfo"
    assert paths.poster_path.name == "cover.jpg"


def test_generate_sort_paths_sanitization(sample_metadata, default_config):
    # Title with illegal chars
    sample_metadata.title = "Test: Movie / With * Illegal ? Chars"
    video_path = Path("video.mp4")
    dest_root = Path("output")

    paths = generate_sort_paths(video_path, dest_root, sample_metadata, default_config)

    # Colons and slashes should be replaced or removed
    # Sanitization usually replaces : with - or similar, / with -
    assert ":" not in str(paths.folder_path)
    assert "?" not in str(paths.folder_path)
    assert "*" not in str(paths.folder_path)


def test_generate_sort_paths_length_limit(sample_metadata, default_config):
    # Very long title
    long_title = "A" * 300
    sample_metadata.title = long_title
    default_config.max_title_length = 50

    video_path = Path("video.mp4")
    dest_root = Path("output")

    paths = generate_sort_paths(video_path, dest_root, sample_metadata, default_config)

    # Check if folder name is reasonable length (ID + Title + Year)
    folder_name = paths.folder_path.name
    # ID (7) + " - " (3) + Title (50) + " (" (2) + Year (4) + ")" (1) ~ 67 chars
    assert len(folder_name) < 100
    assert "AAAA" in folder_name
