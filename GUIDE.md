# Javinizer Python - Hướng dẫn sử dụng

## Cài đặt

### Yêu cầu hệ thống

- **Python 3.10+**
- **Chrome browser** (cho tính năng lấy cookie Javlibrary)

### Cài đặt nhanh

```bash
cd javinizer-py
pip install -e .
```

Hoặc chạy file `install.bat` (Windows).

### Các gói Python được cài đặt

| Gói | Chức năng |
| --- | --------- |
| `httpx[socks]` | HTTP client với SOCKS proxy |
| `beautifulsoup4` | HTML parsing |
| `lxml` | XML/HTML parser |
| `pydantic` | Data validation |
| `click` | CLI framework |
| `rich` | Terminal UI đẹp |
| `Pillow` | Cắt poster từ cover |
| `curl_cffi` | **Bypass Cloudflare** (TLS impersonation) |
| `undetected-chromedriver` | Tự động lấy cookie Javlibrary |
| `setuptools` | Hỗ trợ Python 3.12+ |

### Gói tùy chọn (Optional)

```bash
# Cài Playwright cho dmm_new scraper (chất lượng cao hơn)
pip install playwright
playwright install chromium
```

---

## Tính năng chính

| Tính năng | Trạng thái | Mô tả |
|-----------|------------|-------|
| **Scrapers** | ✅ | DMM, DMM New, R18Dev, Javlibrary |
| **File Sorting** | ✅ | Sắp xếp video vào folder với metadata |
| **Update System** | ✅ | Cập nhật metadata cho folder đã sort |
| **Thumbnail DB** | ✅ | Lưu ảnh diễn viên cục bộ |
| **Translation** | ✅ | Dịch tiêu đề sang EN/VI/... |
| **Proxy Support** | ✅ | HTTP và SOCKS5 |

---

## Các lệnh chính

### 1. Tìm metadata

```bash
# Tìm cơ bản
javinizer find IPX-486

# Chỉ định nguồn (dmm tự động mở rộng thành dmm_new + dmm)
javinizer find IPX-486 --source dmm,r18dev

# Dùng proxy (cần Japan IP)
javinizer find IPX-486 --proxy socks5://127.0.0.1:10808

# Xuất NFO
javinizer find IPX-486 --nfo

# Xuất JSON
javinizer find IPX-486 --json
```

### 2. Sắp xếp video (Sort)

```bash
# Sort 1 file (in-place)
javinizer sort "D:/Videos/IPX-486.mp4"

# Sort với destination
javinizer sort "D:/Videos/IPX-486.mp4" --dest "D:/Movies"

# Sort cả thư mục
javinizer sort-dir "D:/Videos" --dest "D:/Movies" --recursive

# Preview (không thay đổi gì)
javinizer sort "video.mp4" --dry-run

# Copy thay vì move
javinizer sort "video.mp4" --copy
```

### 3. Cập nhật metadata (Update)

```bash
# Update folder đã sort
javinizer update "D:/Movies/SDDE-761"

# Update cả thư mục
javinizer update-dir "D:/Movies" --recursive

# Chỉ update NFO (bỏ qua ảnh)
javinizer update "D:/Movies/SDDE-761" --nfo-only
```

### 4. Quản lý Thumbnail Database

```bash
# Xem danh sách diễn viên
javinizer thumbs list

# Lọc theo tên
javinizer thumbs list --filter "Yua"

# Tải lại ảnh từ database
javinizer thumbs update
```

### 5. Cấu hình

```bash
# Xem cấu hình
javinizer config show

# Đặt proxy mặc định
javinizer config set-proxy socks5://127.0.0.1:10808

# Tắt proxy
javinizer config set-proxy --disable

# Đổi format folder/file
javinizer config set-sort-format --folder "<ID> - <TITLE>"
javinizer config set-sort-format --file "<ID>"

# Debug error logging
javinizer find IPX-486 --verbose
javinizer find IPX-486 --log-file javinizer.log
```

---

## Cấu hình (jvSettings.json)

File cấu hình được lưu tại `javinizer-py/jvSettings.json`.

### Các section chính

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

## Dịch thuật (Translation)

Javinizer hỗ trợ dịch tiêu đề và mô tả từ tiếng Nhật sang ngôn ngữ khác.

### Các dịch vụ được hỗ trợ

| Provider | Miễn phí | Chất lượng | Ghi chú |
|----------|----------|------------|---------|
| `google` | ✅ Có | Tốt | Mặc định, không cần API key |
| `deepl` | Free tier | Rất tốt | Cần API key từ deepl.com |

### Cấu hình Translation

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

### Các ngôn ngữ đích

| Mã | Ngôn ngữ |
|----|----------|
| `en` | Tiếng Anh |
| `vi` | Tiếng Việt |
| `zh` | Tiếng Trung |
| `ko` | Tiếng Hàn |

---

## Javlibrary - Bypass Cloudflare

Javlibrary được bảo vệ bởi Cloudflare. Để sử dụng:

### Bước 1: Lấy cookie

```bash
# Nếu KHÔNG dùng proxy:
javinizer config get-javlibrary-cookies

# Nếu CÓ dùng proxy (QUAN TRỌNG):
javinizer config get-javlibrary-cookies --proxy socks5://127.0.0.1:10808
```

> ⚠️ **LƯU Ý**: Cookie Cloudflare gắn với IP! Phải dùng cùng proxy khi lấy cookie và khi scrape.

### Bước 2: Sử dụng

```bash
javinizer find SDDE-761 --source javlibrary
```

---

## Nguồn dữ liệu (Scrapers)

| Nguồn | Yêu cầu proxy | Ghi chú |
|-------|---------------|---------|
| `r18dev` | Có (Japan IP) | API JSON, nhanh, **khuyên dùng** |
| `dmm_new` | Có | Dùng Playwright, chất lượng cao |
| `dmm` | Có | Site cũ, fallback |
| `javlibrary` | Có + Cookies | Cần bypass Cloudflare |

### Scraper Alias

Khi chỉ định `--source dmm`, hệ thống tự động mở rộng thành `dmm_new, dmm`:

- Thử `dmm_new` trước (nếu có Playwright)
- Fallback sang `dmm` nếu thất bại

---

## Thumbnail Database

Javinizer tự động lưu ảnh diễn viên vào folder `thumbs/` khi sort video.

### Cấu trúc

```
javinizer-py/
├── jvSettings.json
├── actresses.csv      # Database diễn viên
└── thumbs/            # Ảnh diễn viên
    ├── 皆/
    │   └── 皆月ひかる/
    │       └── folder.jpg
    └── 南/
        └── 南日菜乃/
            └── folder.jpg
```

### Cấu hình

```json
"thumbs": {
  "enabled": true,
  "storage_path": "thumbs",
  "csv_file": "actresses.csv",
  "auto_download": true,
  "download_on_sort": true
}
```

---

## Format Templates

| Placeholder | Giá trị | Ví dụ |
|-------------|---------|-------|
| `<ID>` | Movie ID | IPX-486 |
| `<TITLE>` | Tiêu đề | Beautiful Girl... |
| `<STUDIO>` | Studio | Idea Pocket |
| `<YEAR>` | Năm | 2020 |
| `<ACTORS>` | Diễn viên | Sakura Momo |
| `<LABEL>` | Nhãn | - |

**Ví dụ format:**

```text
<ID>                          → IPX-486
<ID> - <TITLE>                → IPX-486 - Beautiful Girl...
<TITLE> (<YEAR>) [<ID>]       → Beautiful Girl... (2020) [IPX-486]
```

---

## Cấu trúc output (Jellyfin)

```text
D:/Movies/
  SDDE-761/
    SDDE-761.mp4
    SDDE-761.nfo
    cover.jpg       ← Poster (cropped)
    backdrop.jpg    ← Full cover
```

---

## Lưu ý quan trọng

1. **Cần Japan IP**: Tất cả các nguồn đều cần proxy Japan
2. **Javlibrary**: Cookie gắn với IP - dùng cùng proxy khi lấy cookie và khi scrape
3. **Translation**: Có thể chậm khi dùng qua SOCKS proxy
4. **Aggregation**: Dùng `--source r18dev,dmm` để gộp metadata từ nhiều nguồn
