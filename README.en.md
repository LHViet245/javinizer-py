# Javinizer Python

Python port of Javinizer - a tool to scrape and organize metadata for Japanese Adult Videos (JAV).

## Features

- **4 Scrapers**: DMM, DMM New (Playwright), R18.dev, Javlibrary
- **File Sorting**: Sort videos into folders with Jellyfin-compatible metadata
- **Thumbnail Database**: Save actress images locally
- **Translation**: Translate titles to EN/VI/... (Google/DeepL)
- **Proxy Support**: HTTP and SOCKS5
- **NFO Generation**: Kodi/Jellyfin/Emby compatible

## Installation

```bash
# Windows
install.bat

# Manual
pip install -e .
pip install playwright  # Optional for dmm_new
playwright install chromium
```

## Quick Usage

```bash
# Find metadata
javinizer find IPX-486

# Sort video
javinizer sort "D:/Videos/IPX-486.mp4" --dest "D:/Movies"

# Update sorted folder
javinizer update "D:/Movies/SDDE-761"

# View actress list
javinizer thumbs list
```

## Documentation

See [GUIDE.en.md](GUIDE.en.md) for full details.

## Requirements

- Python 3.10+
- Japan IP (proxy) for scrapers
- Chrome browser (for Javlibrary cookies)

## License

MIT
