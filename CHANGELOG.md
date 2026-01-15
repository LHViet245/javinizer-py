# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

## [0.2.0-beta.1] - 2026-01-15

### Added

#### New Scrapers

- **JavBus Scraper** (`javbus.py`) - Multi-language support (EN/JP/CN)
  - Chrome impersonation via curl_cffi to bypass region detection
  - Age verification cookies bypass
  - Note: Requires Japan IP for best results
  
- **MGStage Scraper** (`mgstage.py`) - Japanese-only site
  - Age verification handling
  - Note: Requires Japan proxy

#### GUI Dashboard

- **FastAPI Web UI** (`javinizer gui`)
  - Home page with search
  - Search page for movie lookup
  - Settings management page
  - API endpoints: `/api/find/{id}`, `/api/health`, `/api/settings`
  - Modern dark theme design
  
#### CSV Settings

- **Genre Mapping** (`genres.csv`) - Map/filter Japanese genres to English
- **Studio Mapping** (`studios.csv`) - Normalize studio names
- `CSVSettings` configuration in settings

#### Advanced Features

- **Multi-level Folder Sorting** - Support `output_folder` as array for nested structure
  - Example: `["<ACTORS>", "<YEAR>", "<ID>"]` creates `Actor/2024/ABC-123/`
- **Direct URL Scraping** - `javinizer find --url <URL>` for direct scraping
- **Custom Regex Patterns** - `CustomPatternSettings` for custom movie ID extraction
- **Advanced Rate Limiting** - burst_limit, cooldown_multiplier, max_delay

### Fixed

- JavBus and MGStage missing from SCRAPERS dict in `cli_common.py`
- Test mocking for JavBus curl_cffi client
- **Code Quality & Stability:**
  - Refactored `SortConfig` to use immutable default factories (fixed lint warnings).
  - Removed global `console` instance to prevent side-effects in library usage.
  - Improved filename sanitization (now handles colons `:`).
  - Cleaned up unused imports in tests.

### Changed

- JavBus scraper uses curl_cffi with Chrome impersonation (bypasses SOCKS limitation)
- Enhanced RateLimitSettings with burst control

---

## Session Summary (2026-01-14 to 2026-01-15)

### Commits

| Hash | Description |
|------|-------------|
| 89860f9 | curl_cffi browser impersonation for JavBus |
| 5e99bbc | Japan IP requirement documentation |
| 602acef | Age verification cookies |
| 0458b07 | Add javbus/mgstage to SCRAPERS |
| 605a3e4 | GUI dashboard |
| e6e270f | CSV settings |
| 3948e4b | Custom patterns, rate limiting |
| 2709d11 | Direct URL scraping |
| 7af583e | Multi-level folder sorting |
| a68af65 | MGStage scraper |
| b16ac69 | JavBus scraper |

### Files Created/Modified

- `javinizer/scrapers/javbus.py` (350+ lines)
- `javinizer/scrapers/mgstage.py` (340+ lines)
- `javinizer/gui/` (app.py + 4 templates)
- `javinizer/commands/gui.py`
- `javinizer/csv_utils.py` (190 lines)
- `genres.csv`, `studios.csv`
- `tests/test_javbus.py`, `tests/test_mgstage.py`, `tests/test_csv_utils.py`

### Test Status

- 213 tests passing
- All Ruff checks passing
