"""Tests for javinizer.matcher module"""

import pytest
from javinizer.matcher import extract_movie_id, normalize_movie_id

@pytest.mark.parametrize("filename, expected", [
    # Standard patterns
    ("IPX-486.mp4", "IPX-486"),
    ("ipx-486.mp4", "IPX-486"),
    ("IPX486.mp4", "IPX-486"),
    ("ipx486.mp4", "IPX-486"),
    
    # SSNI pattern
    ("SSNI-123.mkv", "SSNI-123"),
    ("ssni123.avi", "SSNI-123"),
    
    # 3-letter prefix
    ("ABC-123.mp4", "ABC-123"),
    
    # 4-digit number
    ("IPX-1234.mp4", "IPX-1234"),
    ("ipx1234.mp4", "IPX-1234"),
    
    # With junk
    ("[Sub] IPX-486.mp4", "IPX-486"),
    ("(2024) IPX-486.mp4", "IPX-486"),
    ("IPX-486_uncensored.mp4", "IPX-486"),
    ("IPX-486-C.mp4", "IPX-486"),
    
    # FC2
    ("FC2-PPV-123456.mp4", "FC2-PPV-123456"),
    ("FC2PPV-123456.mp4", "FC2-PPV-123456"),
    ("FC2-123456.mp4", "FC2-PPV-123456"),
    
    # HEYZO
    ("HEYZO-1234.mp4", "HEYZO-1234"),
    ("heyzo_1234.mp4", "HEYZO-1234"),
    
    # Caribbeancom
    ("010123-123.mp4", "010123-123"),
    ("010123_123.mp4", "010123-123"),
    
    # T28 / Special
    ("T28-123.mp4", "T28-123"),
    ("S1-123.mp4", "S1-123"),
    
    # No match
    ("vacation_video.mp4", None),
    ("random_file.txt", None),
])
def test_extract_movie_id(filename, expected):
    assert extract_movie_id(filename) == expected


@pytest.mark.parametrize("input_id, expected", [
    ("ipx486", "IPX-486"),
    ("IPX-486", "IPX-486"),
    ("ssni123", "SSNI-123"),
    ("abc-123", "ABC-123"),
    ("FC2-PPV-123456", "FC2-PPV-123456"),
])
def test_normalize_movie_id(input_id, expected):
    assert normalize_movie_id(input_id) == expected
