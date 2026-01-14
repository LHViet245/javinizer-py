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


# ============================================================
# Advanced Sorting Tests - Multi-level folder support
# ============================================================


class TestMultiLevelFolderSorting:
    """Tests for output_folder multi-level folder structure"""

    def test_output_folder_single_level(self, sample_metadata):
        """Test single-level output folder (e.g., by actress)"""
        config = SortConfig(
            folder_format="<ID>",
            output_folder=["<ACTORS>"],
        )
        video_path = Path("video.mp4")
        dest_root = Path("/movies")

        paths = generate_sort_paths(video_path, dest_root, sample_metadata, config)

        # Structure: /movies/Test Actress/IPX-486/
        folder_parts = paths.folder_path.parts
        assert "IPX-486" in folder_parts[-1]  # Movie folder
        assert "Actress" in folder_parts[-2] or "Test" in folder_parts[-2]  # Actress folder

    def test_output_folder_two_levels(self, sample_metadata):
        """Test two-level output folder (e.g., actress + year)"""
        config = SortConfig(
            folder_format="<ID>",
            output_folder=["<ACTORS>", "<YEAR>"],
        )
        video_path = Path("video.mp4")
        dest_root = Path("/movies")

        paths = generate_sort_paths(video_path, dest_root, sample_metadata, config)

        # Structure: /movies/<ACTORS>/<YEAR>/IPX-486/
        folder_parts = paths.folder_path.parts
        assert "IPX-486" in folder_parts[-1]  # Movie folder
        assert "2024" in folder_parts[-2]  # Year folder

    def test_output_folder_by_studio(self, sample_metadata):
        """Test output folder by studio"""
        config = SortConfig(
            folder_format="<ID> - <TITLE>",
            output_folder=["<STUDIO>"],
        )
        video_path = Path("video.mp4")
        dest_root = Path("/movies")

        paths = generate_sort_paths(video_path, dest_root, sample_metadata, config)

        # Structure: /movies/IdeaPocket/IPX-486 - Title/
        folder_parts = paths.folder_path.parts
        assert "IdeaPocket" in folder_parts[-2]

    def test_output_folder_empty_list(self, sample_metadata):
        """Test with empty output_folder (backward compatible)"""
        config = SortConfig(
            folder_format="<ID>",
            output_folder=[],
        )
        video_path = Path("video.mp4")
        dest_root = Path("/movies")

        paths = generate_sort_paths(video_path, dest_root, sample_metadata, config)

        # Structure: /movies/IPX-486/ (flat, like before)
        assert paths.folder_path.parent == dest_root
        assert paths.folder_path.name == "IPX-486"

    def test_output_folder_none_default(self, sample_metadata):
        """Test default behavior (no output_folder)"""
        config = SortConfig(
            folder_format="<ID>",
        )
        video_path = Path("video.mp4")
        dest_root = Path("/movies")

        paths = generate_sort_paths(video_path, dest_root, sample_metadata, config)

        # Default should create flat structure
        assert paths.folder_path.parent == dest_root

    def test_output_folder_three_levels(self, sample_metadata):
        """Test three-level nesting"""
        config = SortConfig(
            folder_format="<ID>",
            output_folder=["<STUDIO>", "<ACTORS>", "<YEAR>"],
        )
        video_path = Path("video.mp4")
        dest_root = Path("/movies")

        paths = generate_sort_paths(video_path, dest_root, sample_metadata, config)

        # Structure: /movies/<STUDIO>/<ACTORS>/<YEAR>/IPX-486/
        folder_parts = paths.folder_path.parts
        assert len(folder_parts) >= 4  # At least 4 levels deep

    def test_output_folder_group_actress(self, sample_metadata):
        """Test group actress with multiple actresses"""
        # Add another actress
        sample_metadata.actresses.append(
            Actress(first_name="Second", last_name="Actress")
        )

        config = SortConfig(
            folder_format="<ID>",
            output_folder=["<ACTORS>"],
            group_actress=True,  # Use @Group for multiple
        )
        video_path = Path("video.mp4")
        dest_root = Path("/movies")

        paths = generate_sort_paths(video_path, dest_root, sample_metadata, config)

        # Should use @Group for multiple actresses
        folder_str = str(paths.folder_path)
        assert "@Group" in folder_str

    def test_output_folder_individual_actresses(self, sample_metadata):
        """Test listing all actresses (no grouping)"""
        sample_metadata.actresses.append(
            Actress(first_name="Second", last_name="Actress")
        )

        config = SortConfig(
            folder_format="<ID>",
            output_folder=["<ACTORS>"],
            group_actress=False,  # List all
        )
        video_path = Path("video.mp4")
        dest_root = Path("/movies")

        paths = generate_sort_paths(video_path, dest_root, sample_metadata, config)

        folder_str = str(paths.folder_path)
        # Should contain actress names, not @Group
        assert "@Group" not in folder_str

