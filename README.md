# Javinizer Python

[English](README.en.md) | [Tiếng Việt](README.md) | [中文](README.zh.md)

Python port của Javinizer - công cụ scrape và quản lý metadata cho Japanese Adult Video (JAV).

## Tính năng

- **4 Scrapers**: DMM, DMM New (Playwright), R18.dev, Javlibrary
- **File Sorting**: Sắp xếp video vào folder với metadata Jellyfin-compatible
- **Thumbnail Database**: Lưu ảnh diễn viên cục bộ
- **Translation**: Dịch tiêu đề sang EN/VI/... (Google/DeepL)
- **Proxy Support**: HTTP và SOCKS5
- **NFO Generation**: Kodi/Jellyfin/Emby compatible

## Cài đặt

```bash
# Windows
install.bat

# Manual
pip install -e .
pip install playwright  # Optional for dmm_new
playwright install chromium
```

## Sử dụng nhanh

```bash
# Tìm metadata
javinizer find IPX-486

# Sắp xếp video
javinizer sort "D:/Videos/IPX-486.mp4" --dest "D:/Movies"

# Cập nhật folder đã sort
javinizer update "D:/Movies/SDDE-761"

# Xem danh sách diễn viên
javinizer thumbs list
```

## Documentation

Xem [GUIDE.md](GUIDE.md) để biết chi tiết đầy đủ.

## Yêu cầu

- Python 3.10+
- Japan IP (proxy) cho các nguồn scrape
- Chrome browser (cho Javlibrary cookie)

## License

MIT
