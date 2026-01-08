# Javinizer Python - User Guide

## Installation

### System Requirements

- **Python 3.10+**
- **Chrome browser** (for capturing Javlibrary cookies)

### Quick Install

```bash
cd javinizer-py
pip install -e .
```

Or run `install.bat` (Windows).

### Installed Python Packages

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

### 1. Find Metadata

```bash
# Basic search
javinizer find IPX-486

# Specific source (dmm automatically expands to dmm_new + dmm)
javinizer find IPX-486 --source dmm,r18dev

# Use proxy (Requires Japan IP)
javinizer find IPX-486 --proxy socks5://127.0.0.1:10808

# Output NFO
javinizer find IPX-486 --nfo

# Output JSON
javinizer find IPX-486 --json
```

### 2. File Sorting

```bash
# Sort 1 file (in-place)
javinizer sort "D:/Videos/IPX-486.mp4"

# Sort to destination
javinizer sort "D:/Videos/IPX-486.mp4" --dest "D:/Movies"

# Sort entire directory
javinizer sort-dir "D:/Videos" --dest "D:/Movies" --recursive

# Preview (dry-run)
javinizer sort "video.mp4" --dry-run

# Copy instead of move
javinizer sort "video.mp4" --copy
```

### 3. Update Metadata

```bash
# Update sorted folder
javinizer update "D:/Movies/SDDE-761"

# Update entire directory
javinizer update-dir "D:/Movies" --recursive

# Only update NFO (skip images)
javinizer update "D:/Movies/SDDE-761" --nfo-only
```

### 4. Thumbnail Database Management

```bash
# List actresses
javinizer thumbs list

# Filter by name
javinizer thumbs list --filter "Yua"

# Update images from database
javinizer thumbs update
```

### 5. Configuration

```bash
# Show config
javinizer config show

# Set default proxy
javinizer config set-proxy socks5://127.0.0.1:10808

# Disable proxy
javinizer config set-proxy --disable

# Change sort format
javinizer config set-sort-format --folder "<ID> - <TITLE>"
javinizer config set-sort-format --file "<ID>"
```

---

## Configuration File (jvSettings.json)

Settings are stored in `javinizer-py/jvSettings.json`.

### Main Sections

```json
{
  "scraper_dmm": true,
  "scraper_r18dev": true,
  "scraper_javlibrary": true,

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

### Translation Config

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

> ⚠️ **NOTE**: Cloudflare cookies are tied to IP! You must use the SAME proxy when capturing cookies and when scraping.

### Step 2: Use

```bash
javinizer find SDDE-761 --source javlibrary
```

---

## Data Sources (Scrapers)

| Source | Proxy Required | Notes |
|-------|---------------|---------|
| `r18dev` | Yes (Japan IP) | JSON API, fast, **recommended** |
| `dmm_new` | Yes | Uses Playwright, high quality |
| `dmm` | Yes | Old site, fallback |
| `javlibrary` | Yes + Cookies | Requires Cloudflare bypass |

### Scraper Alias

When you specify `--source dmm`, it automatically expands to `dmm_new, dmm`:

- Tries `dmm_new` first (if Playwright is installed)
- Fallback to `dmm` if it fails

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

---

## Important Notes

1. **Japan IP Required**: All sources require a Japanese proxy.
2. **Javlibrary**: Cookies are IP-bound.
3. **Translation**: May be slow over SOCKS proxy.
4. **Aggregation**: Use `--source r18dev,dmm` to combine metadata from multiple sources.
