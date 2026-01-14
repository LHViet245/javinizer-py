"""CSV utilities for genre and studio mapping/replacement

Supports loading CSV files for:
- genres.csv: Map/replace/filter genre names
- studios.csv: Map/replace studio names

CSV Format:
    Original,Replacement
    美少女,Beautiful Girl
    素人,Amateur
    #Comment (ignored)

If Replacement is empty, the Original will be filtered out.
"""

import csv
from pathlib import Path
from typing import Optional

from javinizer.logger import get_logger

logger = get_logger(__name__)


class CSVMapper:
    """Generic CSV-based name mapper/replacer"""

    def __init__(self, csv_path: Optional[Path] = None):
        """Initialize mapper with optional CSV file path
        
        Args:
            csv_path: Path to CSV file, or None to use no mapping
        """
        self.mappings: dict[str, str] = {}
        self.filters: set[str] = set()  # Items to filter out (empty replacement)
        self._loaded = False
        self._csv_path = csv_path

        if csv_path and csv_path.exists():
            self.load(csv_path)

    def load(self, csv_path: Path) -> bool:
        """Load mappings from CSV file
        
        Args:
            csv_path: Path to CSV file
            
        Returns:
            True if loaded successfully
        """
        try:
            with open(csv_path, "r", encoding="utf-8-sig") as f:
                reader = csv.reader(f)
                for row in reader:
                    # Skip empty rows and comments
                    if not row or row[0].startswith("#"):
                        continue
                    
                    original = row[0].strip()
                    if not original:
                        continue
                        
                    replacement = row[1].strip() if len(row) > 1 else ""
                    
                    if replacement:
                        self.mappings[original.lower()] = replacement
                    else:
                        # Empty replacement = filter out
                        self.filters.add(original.lower())

            self._loaded = True
            logger.debug(f"Loaded {len(self.mappings)} mappings, {len(self.filters)} filters from {csv_path}")
            return True
            
        except Exception as e:
            logger.warning(f"Failed to load CSV {csv_path}: {e}")
            return False

    def map(self, name: str) -> Optional[str]:
        """Map a name to its replacement
        
        Args:
            name: Original name
            
        Returns:
            Mapped name, original if no mapping, or None if filtered
        """
        name_lower = name.lower().strip()
        
        # Check if filtered
        if name_lower in self.filters:
            return None
            
        # Check if mapped
        if name_lower in self.mappings:
            return self.mappings[name_lower]
            
        # Return original
        return name

    def map_list(self, names: list[str]) -> list[str]:
        """Map a list of names, filtering out None results
        
        Args:
            names: List of original names
            
        Returns:
            List of mapped names (filtered items removed)
        """
        result = []
        for name in names:
            mapped = self.map(name)
            if mapped is not None:
                result.append(mapped)
        return result

    @property
    def is_loaded(self) -> bool:
        """Check if CSV was loaded successfully"""
        return self._loaded


class GenreMapper(CSVMapper):
    """Mapper specifically for genre names"""
    pass


class StudioMapper(CSVMapper):
    """Mapper specifically for studio/maker names"""
    pass


# Global instances (lazy loaded)
_genre_mapper: Optional[GenreMapper] = None
_studio_mapper: Optional[StudioMapper] = None


def get_genre_mapper(csv_path: Optional[Path] = None) -> GenreMapper:
    """Get or create the global genre mapper
    
    Args:
        csv_path: Optional path to genres.csv
        
    Returns:
        GenreMapper instance
    """
    global _genre_mapper
    if _genre_mapper is None or csv_path:
        _genre_mapper = GenreMapper(csv_path)
    return _genre_mapper


def get_studio_mapper(csv_path: Optional[Path] = None) -> StudioMapper:
    """Get or create the global studio mapper
    
    Args:
        csv_path: Optional path to studios.csv
        
    Returns:
        StudioMapper instance
    """
    global _studio_mapper
    if _studio_mapper is None or csv_path:
        _studio_mapper = StudioMapper(csv_path)
    return _studio_mapper


def map_genres(genres: list[str], csv_path: Optional[Path] = None) -> list[str]:
    """Map genre names using genres.csv
    
    Args:
        genres: List of original genre names
        csv_path: Optional path to genres.csv
        
    Returns:
        List of mapped genre names
    """
    mapper = get_genre_mapper(csv_path)
    return mapper.map_list(genres)


def map_studio(studio: str, csv_path: Optional[Path] = None) -> str:
    """Map studio name using studios.csv
    
    Args:
        studio: Original studio name
        csv_path: Optional path to studios.csv
        
    Returns:
        Mapped studio name
    """
    mapper = get_studio_mapper(csv_path)
    result = mapper.map(studio)
    return result if result else studio
