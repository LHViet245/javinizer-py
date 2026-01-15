"""Tests for csv_utils module"""


from javinizer.csv_utils import (
    CSVMapper,
    GenreMapper,
    StudioMapper,
    map_genres,
    map_studio,
)


class TestCSVMapper:
    """Tests for CSVMapper class"""

    def test_empty_mapper(self):
        """Test mapper with no CSV file"""
        mapper = CSVMapper()
        assert mapper.map("Test") == "Test"
        assert not mapper.is_loaded

    def test_load_valid_csv(self, tmp_path):
        """Test loading valid CSV file"""
        csv_content = """Original,Replacement
美少女,Beautiful Girl
素人,Amateur"""
        csv_file = tmp_path / "test.csv"
        csv_file.write_text(csv_content, encoding="utf-8")

        mapper = CSVMapper(csv_file)
        assert mapper.is_loaded
        assert mapper.map("美少女") == "Beautiful Girl"
        assert mapper.map("素人") == "Amateur"

    def test_case_insensitive(self, tmp_path):
        """Test case-insensitive matching"""
        csv_content = "TEST,Replaced"
        csv_file = tmp_path / "test.csv"
        csv_file.write_text(csv_content, encoding="utf-8")

        mapper = CSVMapper(csv_file)
        assert mapper.map("TEST") == "Replaced"
        assert mapper.map("test") == "Replaced"
        assert mapper.map("Test") == "Replaced"

    def test_filter_empty_replacement(self, tmp_path):
        """Test filtering items with empty replacement"""
        csv_content = """Original,Replacement
Good,Nice
Bad,"""
        csv_file = tmp_path / "test.csv"
        csv_file.write_text(csv_content, encoding="utf-8")

        mapper = CSVMapper(csv_file)
        assert mapper.map("Good") == "Nice"
        assert mapper.map("Bad") is None  # Filtered

    def test_comment_lines_ignored(self, tmp_path):
        """Test that comment lines are ignored"""
        csv_content = """# This is a comment
Original,Replacement
#Another comment
Test,Replaced"""
        csv_file = tmp_path / "test.csv"
        csv_file.write_text(csv_content, encoding="utf-8")

        mapper = CSVMapper(csv_file)
        assert mapper.map("Test") == "Replaced"
        assert mapper.map("# This is a comment") == "# This is a comment"

    def test_map_list(self, tmp_path):
        """Test mapping a list of values"""
        csv_content = """Original,Replacement
A,Alpha
B,
C,Gamma"""
        csv_file = tmp_path / "test.csv"
        csv_file.write_text(csv_content, encoding="utf-8")

        mapper = CSVMapper(csv_file)
        result = mapper.map_list(["A", "B", "C", "D"])
        
        assert "Alpha" in result
        assert "Gamma" in result
        assert "D" in result
        assert "B" not in result  # Filtered

    def test_nonexistent_file(self, tmp_path):
        """Test with non-existent CSV file"""
        mapper = CSVMapper(tmp_path / "nonexistent.csv")
        assert not mapper.is_loaded
        assert mapper.map("Test") == "Test"


class TestGenreMapper:
    """Tests for GenreMapper class"""

    def test_genre_mapper_inherits_csvmapper(self, tmp_path):
        """Test GenreMapper inherits from CSVMapper"""
        csv_content = "美少女,Beautiful Girl"
        csv_file = tmp_path / "genres.csv"
        csv_file.write_text(csv_content, encoding="utf-8")

        mapper = GenreMapper(csv_file)
        assert mapper.map("美少女") == "Beautiful Girl"


class TestStudioMapper:
    """Tests for StudioMapper class"""

    def test_studio_mapper_inherits_csvmapper(self, tmp_path):
        """Test StudioMapper inherits from CSVMapper"""
        csv_content = "S1 NO.1 STYLE,S1"
        csv_file = tmp_path / "studios.csv"
        csv_file.write_text(csv_content, encoding="utf-8")

        mapper = StudioMapper(csv_file)
        assert mapper.map("S1 NO.1 STYLE") == "S1"


class TestHelperFunctions:
    """Tests for helper functions"""

    def test_map_genres(self, tmp_path):
        """Test map_genres function"""
        csv_content = """美少女,Beautiful Girl
素人,Amateur
HD,"""
        csv_file = tmp_path / "genres.csv"
        csv_file.write_text(csv_content, encoding="utf-8")

        genres = ["美少女", "素人", "HD", "Other"]
        result = map_genres(genres, csv_file)

        assert "Beautiful Girl" in result
        assert "Amateur" in result
        assert "Other" in result
        assert "HD" not in result  # Filtered

    def test_map_studio(self, tmp_path):
        """Test map_studio function"""
        csv_content = "S1 NO.1 STYLE,S1"
        csv_file = tmp_path / "studios.csv"
        csv_file.write_text(csv_content, encoding="utf-8")

        assert map_studio("S1 NO.1 STYLE", csv_file) == "S1"
        assert map_studio("Other Studio", csv_file) == "Other Studio"


class TestUTF8BOM:
    """Tests for UTF-8 BOM handling"""

    def test_utf8_bom_file(self, tmp_path):
        """Test reading UTF-8 file with BOM"""
        csv_content = "美少女,Beautiful Girl"
        csv_file = tmp_path / "test.csv"
        # Write with BOM
        with open(csv_file, "w", encoding="utf-8-sig") as f:
            f.write(csv_content)

        mapper = CSVMapper(csv_file)
        assert mapper.map("美少女") == "Beautiful Girl"
