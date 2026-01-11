"""Tests for javinizer.models module"""

import pytest
from javinizer.models import MovieMetadata, Actress, Rating

def test_movie_metadata_creation():
    data = {
        "id": "IPX-486",
        "title": "Test Movie",
        "maker": "IdeaPocket",
        "label": "IdeaPocket",
        "series": "Test Series",
        "director": "Test Director",
        "release_date": "2024-01-01",
        "runtime": 120,
        "genres": ["Genre1", "Genre2"],
        "actresses": [
            {"first_name": "Test", "last_name": "Actor", "thumb_url": "http://example.com/actor.jpg"}
        ],
        "rating": {"rating": 4.5, "votes": 100},
        "source": "dmm"
    }
    
    model = MovieMetadata(**data)
    
    assert model.id == "IPX-486"
    assert model.title == "Test Movie"
    assert model.runtime == 120
    assert len(model.actresses) == 1
    assert model.actresses[0].full_name == "Test Actor"
    
    # Check rating
    assert model.rating is not None
    assert model.rating.rating == 4.5
    assert model.rating.votes == 100
    
    assert str(model.release_date) == "2024-01-01"

def test_movie_metadata_optional_fields():
    # Only required fields should work if model allows (all are optional basically)
    data = {
        "id": "IPX-486",
        "title": "Minimal Movie",
        "source": "test"
    }
    model = MovieMetadata(**data)
    assert model.id == "IPX-486"
    assert model.actresses == []
    assert model.genres == []
