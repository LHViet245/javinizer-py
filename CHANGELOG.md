# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

## [0.2.0-beta.1] - 2026-01-15

### Added

- **MGStage Scraper** (`javinizer/scrapers/mgstage.py`)
  - Full support for metadata extraction (Title, Release Date, Actresses, Maker, Label).
  - **Smart ID Search**: Automatically resolves truncated IDs (e.g., `START-469` → `107START-469`).
  - **Robustness**: Handles varying HTML attribute orders for cover images.
- **Documentation**
  - New `GUIDE.md`: Comprehensive usage guide (English/Vietnamese).
  - New `docs/comparison-original-vs-py.md`: Detailed feature comparison.
  - Updated `README.md`: Reflects current feature set.

### Changed

- **Removed JavBus**: Completely removed JavBus scraper due to persistent region blocking and anti-bot measures.
- **Refactoring**:
  - `MGStageScraper`: Improved URL resolution and search fallback.
  - `javinizer/cli_common.py`: Cleaned up imports.
- **Tests**:
  - Removed outdated tests (`test_javbus.py`).
  - Updated `test_mgstage.py` to match new logic.
  - Achieved **100% Pass Rate** (190 tests) on valid codebase.

### Fixed

- **CLI Crash**: Resolved `ImportError` in `find` command caused by deleted JavBus module.
- **Linting**: Fixed various formatting issues in markdown docs.

---
