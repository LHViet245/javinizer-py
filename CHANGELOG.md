# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

## [Unreleased]

### Added

- **GUI Redesign (Web Station)**:
  - **View Toggle**: Switch between Grid and Table views in the file grid panel.
  - **Phase 4 Implemented**:
    - **Main Grid View**: Dynamic grid displaying folder contents with HTMX-powered navigation.
    - **Metadata Inspector**: Interactive panel for viewing and manual editing of movie metadata.
    - **Live Metadata Scraping**: Auto-fetching metadata for selected JAV files using all active scrapers and aggregator.
  - **Phase 5 Implemented**:
    - **Real-time Log Streaming**: Implemented SSE (Server-Sent Events) to stream backend logs to the UI.
    - **Terminal HUD**: Fixed-bottom workspace console with auto-scroll and Alpine.js integration.
    - **LogBroadcaster Service**: Singleton for managing SSE connections and broadcasting log records.
  - **Phase 6 Implemented**:
    - **HTMX Search Integration**: Live filtering of Grid View using search-as-you-type with HTMX and Alpine.js.
    - **Bulk Actions**: Implemented selection state management and Action Toolbar for multi-item operations.
    - **Batch Operations**: Added backend endpoints for concurrent sorting and metadata updates on multiple paths.
    - **Toast Notifications**: Built-in notification system for real-time job feedback (Success/Error/Warning).
    - **Final Integration**: Connected "Start Processing" button and unified UI component communication.
  - Comprehensive security, code quality, performance, and documentation audit.
  - Generated report at `docs/reports/audit_2026-01-18.md`.
  - **Results**: 0 critical issues, 19 warnings (18 unused imports/vars, 1 duplicate code), 3 suggestions.
  - **Health Score**: 85/100 ✅
  - **Fixed (2026-01-20)**:
    - **GUI Folder Navigation**: Fixed typo in `file_tree.html` (`grid_grid_fragment`) and added double-click handler for proper directory navigation.
    - **Start Processing Button**: Resolved AlpineJS scope isolation issue between Header and Main content by moving state to global scope.
    - **Terminal HUD Logging**: Fixed SSE log streaming by adding `logger.info()` to `JobManager.update_job()` for real-time terminal output.
  - **Fixed (2026-01-19)**:
    - Resolved 9 ruff errors (unused variables, duplicate logic, import order).
    - Passed all 194 tests.
  - **Security Hardening (2026-01-19)**:
    - **Path Traversal Protection**: Added `validate_path()` function to block `..` and null bytes in filesystem API.
    - **XSS Prevention**: Implemented `html.escape()` for all user input in HTML responses (`apply_metadata` endpoint).
    - **CORS Configuration**: Replaced wildcard (`*`) with environment-based config via `ALLOWED_ORIGINS`.
    - **Settings Authentication**: Protected POST `/api/settings` with token-based auth (`X-Admin-Token` header).
    - **Job Cleanup**: Added `cleanup_old_jobs()` method to prevent memory leaks in `JobManager`.
    - Created comprehensive security test suite (`tests/test_web_security.py`) with 13 tests.
    - Generated security audit report at `docs/reports/audit_2026-01-19.md`.
    - **Test Results**: 207 tests passed (13 new security tests added).

### Changed

- **GUI Architecture**:
  - **Consolidated GUI folders**: Removed legacy `javinizer/gui/` (165 lines simple GUI).
  - **CLI Updated**: `javinizer gui` command now launches full-featured Web Station (`javinizer/web/server.py`).
  - Added `run_server()` function to `web/server.py` for CLI integration.

- **Type Safety**:
  - Achieved **100% Mypy Compliance** (fixed 158 type errors).
  - Added strict type guards for `console.print()`.
  - Fixed Playwright type incompatibility in `dmm_new.py`.
- **Performance**:
  - Implemented **Parallel Directory Update** (`javinizer update-dir`) using `ThreadPoolExecutor` (4 workers).
  - Significantly faster batch processing for large libraries.
- **GUI**:
  - Implemented actual **Search Functionality** (`/search?q=...`) accessing live scrapers.
  - Fixed startup crash on Windows console (UnicodeEncodeError).
- **Maintenance**:
  - Refactored `thumbs.py` to cleanly handle forced re-downloads.
- **Project Structure**:
  - Cleaned up debug files (`error.txt`, `*_debug.html`).
  - Updated `.gitignore` to include IDE and cache directories.

### Fixed

- **Core/Config**:
  - Resolved circular import issues by moving global `settings` initialization to the end of `config.py`.
  - Added `settings.model_dump()` and `settings.model_validate()` calls for Pydantic v2 compatibility.
- **Web API**:
  - Fixed `ImportError` in `api/settings.py` due to missing `settings` object.
- **Playwright**: Resolved invalid proxy type configuration.
- **CLI**: Fixed potential `NoneType` errors in `scrape_parallel`.

## [0.2.0-beta.1] - 2026-01-15

### Added

- **Multi-level Folder Sorting**:
  - Added `output_folder` config to support nested structures (e.g., `["<ACTORS>", "<YEAR>"]`).
  - Updates to `SortSettings` and `SortConfig`.
- **GUI Redesign (Web Station)**:
  - **Phase 1-3 Implemented**:
    - Modern "Liquid Glass" UI styling.
    - Recursive File Explorer API & Component.
    - Background Job Manager for non-blocking operations.
    - Decoupled `SortService` API.

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
