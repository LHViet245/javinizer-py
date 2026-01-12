# Javinizer Python - User Guide

## Installation

### System Requirements

- **Python 3.10+**
- **Google Chrome** (for capturing Javlibrary cookies)

### Quick Install

```bash
cd javinizer-py
pip install -e .
```

Or run **`install.bat`** (Windows) and choose:

- **[1] Standard Install**: Normal installation.
- **[2] Clean Install**: Fresh install (removes old venv, cache, logs) - recommended for troubleshooting.

### Installed Packages

| Package | Function |
| --- | --------- |
| `httpx[socks]` | HTTP client with SOCKS proxy support |
| `beautifulsoup4` | HTML parsing |
| `lxml` | XML/HTML parser |
| `pydantic` | Data validation |
| `click` | CLI framework |
| `rich` | Beautiful Terminal UI |
| `Pillow` | Image processing (cropping posters) |
| `curl_cffi` | **Bypass Cloudflare** (TLS impersonation) |
| `undetected-chromedriver` | Auto-capture Javlibrary cookies |
| `setuptools` | Python 3.12+ support |

### Optional Packages

```bash
# Install Playwright for dmm_new scraper (higher quality metadata)
pip install playwright
playwright install chromium
```

---

## Key Features

| Feature | Status | Description |
|-----------|------------|-------|
| **Scrapers** | ✅ | DMM, DMM New, R18Dev, Javlibrary |
| **File Sorting** | ✅ | Sort videos into folders with metadata |
| **Update System** | ✅ | Update metadata for sorted folders |
| **Thumbnail DB** | ✅ | Local actress image database |
| **Translation** | ✅ | Translate titles to EN/VI/ZH... |
| **Proxy Support** | ✅ | HTTP and SOCKS5 |

---

## Main Commands

### 1. Find Metadata (`find`)

Search for movie metadata by ID.

```bash
# Basic search
javinizer find IPX-486

# Specific source (dmm automatically expands to dmm_new + dmm)
javinizer find IPX-486 --source dmm,r18dev

# Use proxy (Requires Japan IP)
javinizer find IPX-486 --proxy socks5://127.0.0.1:10808

# Output NFO/JSON
javinizer find IPX-486 --nfo
javinizer find IPX-486 --json

# Debug log
javinizer find IPX-486 --verbose --log-file debug.log
```

- `--source, -s`: Scraper sources (default: all).
- `--proxy, -p`: Proxy URL.
- `--no-aggregate`: Disable result aggregation, use first match only.

### 2. File Sorting (`sort`)

Sort a video file into the specific folder structure.

```bash
# Sort 1 file (in-place)
javinizer sort "D:/Videos/IPX-486.mp4"

# Sort to destination
javinizer sort "D:/Videos/IPX-486.mp4" --dest "D:/Movies"

# Preview (dry-run)
javinizer sort "video.mp4" --dry-run
```

- `--dest, -d`: Destination folder.
- `--source, -s`: Scraper sources.
- `--proxy, -p`: Proxy URL.
- `--copy`: Copy file instead of moving.
- `--dry-run`: Preview changes without executing.

### 3. Batch Sort (`sort-dir`)

Scan and sort all videos in a directory.

```bash
# Sort entire directory
javinizer sort-dir "D:/Videos" --dest "D:/Movies" --recursive
```

- `--dest, -d`: Destination folder (Required).
- `--recursive, -r`: Scan subdirectories.
- `--min-size`: Minimum file size (MB) to process (default: 100).
- `--source, -s`: Scraper sources.
- `--proxy, -p`: Proxy URL.

### 4. Update Metadata (`update`)

Refresh metadata for an existing sorted folder.

```bash
# Update sorted folder
javinizer update "D:/Movies/SDDE-761"

# Only update NFO (skip images)
javinizer update "D:/Movies/SDDE-761" --nfo-only
```

- `--source, -s`: Scraper sources.
- `--proxy, -p`: Proxy URL.
- `--nfo-only`: Only regenerate NFO.
- `--dry-run`: Preview changes.

### 5. Batch Update (`update-dir`)

Update all movie folders in a directory.

```bash
javinizer update-dir "D:/Movies" --recursive
```

- `--recursive, -r`: Scan subdirectories.
- `--nfo-only`: Only update NFOs.

### 6. Thumbnail Database (`thumbs`)

```bash
# List actresses
javinizer thumbs list

# Filter by name
javinizer thumbs list --filter "Yua"

# Update images from database
javinizer thumbs update
```

### 7. Configuration (`config`)

```bash
# Show config
javinizer config show

# Set default proxy
javinizer config set-proxy socks5://127.0.0.1:10808

# Disable proxy
javinizer config set-proxy --disable

# Capture Javlibrary cookies (Browser)
javinizer config get-javlibrary-cookies
```

---

## Configuration (jvSettings.json)

Settings are stored in `javinizer-py/jvSettings.json`.

### Main Sections

```json
{
  "scraper_dmm": true,
  "scraper_r18dev": true,
  "scraper_javlibrary": true,

  "log_file": "javinizer.log",

  "proxy": {
    "enabled": true,
    "url": "socks5://127.0.0.1:10808"
  },

  "sort": {
    "folder_format": "<ID>",
    "file_format": "<ID>",
    "poster_filename": "cover.jpg",
    "backdrop_filename": "backdrop.jpg"
  },

  "thumbs": {
    "enabled": true,
    "auto_download": true
  },

  "translation": {
    "enabled": true,
    "provider": "google",
    "target_language": "en"
  }
}
```

---

## Translation

Javinizer supports translating titles and descriptions from Japanese to other languages.

### Supported Providers

| Provider | Free | Quality | Notes |
|----------|----------|------------|---------|
| `google` | ✅ Yes | Good | Default, no API key required |
| `deepl` | Free tier | Very Good | Requires API key from deepl.com |

### Configuration

```json
"translation": {
  "enabled": true,
  "provider": "google",
  "target_language": "en",
  "deepl_api_key": null,
  "translate_title": true,
  "translate_description": true
}
```

### Target Languages

| Code | Language |
|----|----------|
| `en` | English |
| `vi` | Vietnamese |
| `zh` | Chinese |
| `ko` | Korean |

---

## Javlibrary - Bypass Cloudflare

Javlibrary is protected by Cloudflare. To use it:

### Step 1: Capture Cookies

```bash
# If NOT using proxy:
javinizer config get-javlibrary-cookies

# If USING proxy (IMPORTANT):
javinizer config get-javlibrary-cookies --proxy socks5://127.0.0.1:10808
```

> 💡 **Tip**: If you run a scrape command and get blocked, the tool will **automatically** suggest the exact command you need to run.

> ⚠️ **NOTE**: Cloudflare cookies are tied to IP! You must use the SAME proxy when capturing cookies and when scraping.

### Step 2: Use

```bash
javinizer find SDDE-761 --source javlibrary
```

---

## Thumbnail Database

Javinizer automatically saves actress images to the `thumbs/` folder when sorting videos.

### Structure

```
javinizer-py/
├── jvSettings.json
├── actresses.csv      # Actress database
└── thumbs/            # Actress images
    ├── 皆/
    │   └── 皆月ひかる/
    │       └── folder.jpg
    └── 南/
        └── 南日菜乃/
            └── folder.jpg
```

> 🛡️ **Portable Feature**: Image paths are stored as **relative paths**. You can freely copy the `thumbs` folder to another machine or drive.

---

## Format Templates

| Placeholder | Value | Example |
|-------------|---------|-------|
| `<ID>` | Movie ID | IPX-486 |
| `<TITLE>` | Title | Beautiful Girl... |
| `<STUDIO>` | Studio | Idea Pocket |
| `<YEAR>` | Year | 2020 |
| `<ACTORS>` | Actresses | Sakura Momo |
| `<LABEL>` | Label | - |

**Example formats:**

```text
<ID>                          → IPX-486
<ID> - <TITLE>                → IPX-486 - Beautiful Girl...
<TITLE> (<YEAR>) [<ID>]       → Beautiful Girl... (2020) [IPX-486]
```

---

## Output Structure (Jellyfin)

```text
D:/Movies/
  SDDE-761/
    SDDE-761.mp4
    SDDE-761.nfo
    cover.jpg       ← Poster (cropped)
    backdrop.jpg    ← Full cover
```
