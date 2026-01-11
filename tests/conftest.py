"""pytest configuration and shared fixtures"""

import pytest
from pathlib import Path
from datetime import date

from javinizer.models import MovieMetadata, Actress, Rating, Settings


@pytest.fixture
def sample_movie_metadata() -> MovieMetadata:
    """Standard movie metadata fixture for tests"""
    return MovieMetadata(
        id="IPX-486",
        title="Test Movie Title",
        original_title="テスト映画タイトル",
        release_date=date(2024, 1, 15),
        runtime=120,
        maker="Test Studio",
        label="Test Label",
        actresses=[
            Actress(
                first_name="Momo",
                last_name="Sakura",
                japanese_name="桜もも",
            )
        ],
        genres=["Beautiful Girl", "Featured Actress"],
        rating=Rating(rating=8.5, votes=100),
        source="test",
    )


@pytest.fixture
def default_settings() -> Settings:
    """Default settings fixture"""
    return Settings()


@pytest.fixture
def fixtures_dir() -> Path:
    """Path to test fixtures directory"""
    return Path(__file__).parent / "fixtures"


@pytest.fixture
def dmm_fixtures_dir(fixtures_dir) -> Path:
    """Path to DMM fixtures directory"""
    return fixtures_dir / "dmm"


@pytest.fixture
def r18dev_fixtures_dir(fixtures_dir) -> Path:
    """Path to R18Dev fixtures directory"""
    return fixtures_dir / "r18dev"


@pytest.fixture
def javlibrary_fixtures_dir(fixtures_dir) -> Path:
    """Path to Javlibrary fixtures directory"""
    return fixtures_dir / "javlibrary"
