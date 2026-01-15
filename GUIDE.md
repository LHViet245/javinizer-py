# Javinizer Python - Hướng dẫn sử dụng

## Cài đặt

### Yêu cầu hệ thống

- **Python 3.10+**
- **Google Chrome** (để lấy cookie cho Javlibrary)

### Cài đặt nhanh

```bash
cd javinizer-py
pip install -e .
```

Hoặc chạy file **`install.bat`** (Windows) và chọn:

- **[1] Standard Install**: Cài đặt thông thường.
- **[2] Clean Install**: Cài đặt sạch (xoá venv cũ, cache, log) - khuyên dùng khi gặp lỗi lạ.

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
| :--- | :---: | :--- |
| **Scrapers** | ✅ | DMM, DMM New, R18Dev, Javlibrary, MGStage |
| **File Sorting** | ✅ | Sắp xếp video vào folder với metadata |
| **Update System** | ✅ | Cập nhật metadata cho folder đã sort |
| **Thumbnail DB** | ✅ | Lưu ảnh diễn viên cục bộ |
| **Translation** | ✅ | Dịch tiêu đề sang EN/VI/... |
| **Proxy Support** | ✅ | HTTP và SOCKS5 |

---

## Các lệnh chính

### 1. Tìm metadata (`find`)

Tìm kiếm thông tin phim theo mã (ID).

```bash
# Tìm cơ bản
javinizer find IPX-486

# Chỉ định nguồn (dmm tự động mở rộng thành dmm_new + dmm)
javinizer find IPX-486 --source dmm,r18dev

# Dùng proxy (cần Japan IP)
javinizer find IPX-486 --proxy socks5://127.0.0.1:10808

# Xuất NFO/JSON
javinizer find IPX-486 --nfo
javinizer find IPX-486 --json

# Debug log
javinizer find IPX-486 --verbose --log-file debug.log
```

- `--source, -s`: Nguồn tìm kiếm (mặc định: tất cả).
- `--proxy, -p`: Proxy URL.
- `--no-aggregate`: Tắt tính năng gộp kết quả, chỉ lấy từ nguồn đầu tiên tìm thấy.

### 2. Sắp xếp video (`sort`)

Sắp xếp file video vào cấu trúc thư mục chuẩn.

```bash
# Sort 1 file (in-place - tạo folder ngay tại chỗ)
javinizer sort "D:/Videos/IPX-486.mp4"

# Sort với destination (di chuyển sang ổ khác)
javinizer sort "D:/Videos/IPX-486.mp4" --dest "D:/Movies"

# Preview (không thay đổi gì)
javinizer sort "video.mp4" --dry-run
```

- `--dest, -d`: Thư mục đích.
- `--source, -s`: Nguồn scrape.
- `--proxy, -p`: Proxy URL.
- `--copy`: Copy file thay vì Move.
- `--dry-run`: Chạy thử.

### 3. Sắp xếp hàng loạt (`sort-dir`)

Quét và sắp xếp toàn bộ video trong một thư mục.

```bash
# Sort cả thư mục
javinizer sort-dir "D:/Videos" --dest "D:/Movies" --recursive
```

- `--dest, -d`: Thư mục đích (Bắt buộc).
- `--recursive, -r`: Quét thư mục con.
- `--min-size`: Dung lượng file tối thiểu (MB) để xử lý (mặc định: 100).
- `--source, -s`: Nguồn scrape.
- `--proxy, -p`: Proxy URL.

### 4. Cập nhật metadata (`update`)

Cập nhật lại metadata cho thư mục phim đã được sort trước đó.

```bash
# Update folder đã sort
javinizer update "D:/Movies/SDDE-761"

# Chỉ update NFO (bỏ qua ảnh)
javinizer update "D:/Movies/SDDE-761" --nfo-only
```

- `--source, -s`: Nguồn scrape.
- `--proxy, -p`: Proxy URL.
- `--nfo-only`: Chỉ tạo lại NFO, không tải lại ảnh.
- `--dry-run`: Chạy thử.

### 5. Cập nhật hàng loạt (`update-dir`)

Cập nhật cho tất cả các folder phim trong một thư mục lớn.

```bash
javinizer update-dir "D:/Movies" --recursive
```

- `--recursive, -r`: Quét thư mục con.
- `--nfo-only`: Chỉ tạo lại NFO.

### 6. Quản lý Thumbnail Database (`thumbs`)

```bash
# Xem danh sách diễn viên
javinizer thumbs list

# Lọc theo tên
javinizer thumbs list --filter "Yua"

# Tải lại ảnh từ database
javinizer thumbs update
```

### 7. Cấu hình (`config`)

```bash
# Xem cấu hình
javinizer config show

# Đặt proxy mặc định
javinizer config set-proxy socks5://127.0.0.1:10808

# Tắt proxy
javinizer config set-proxy --disable

# Lấy cookie Javlibrary (Browser)
javinizer config get-javlibrary-cookies
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
  "target_language": "vi",
  "deepl_api_key": null,
  "translate_title": true,
  "translate_description": true
}
```

### Các ngôn ngữ đích

| Mã | Ngôn ngữ |
| :---: | :--- |
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

> 💡 **Mẹo**: Nếu bạn chạy lệnh scrape và bị chặn, tool sẽ **tự động** gợi ý chính xác lệnh cần chạy.

> ⚠️ **LƯU Ý**: Cookie Cloudflare gắn với IP! Phải dùng cùng proxy khi lấy cookie và khi scrape.

### Bước 2: Sử dụng

```bash
javinizer find SDDE-761 --source javlibrary
```

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

> 🛡️ **Tính năng Portable**: Đường dẫn ảnh được lưu dưới dạng **tương đối** (Relative Path). Bạn có thể copy thư mục `thumbs` sang máy khác hoặc ổ đĩa khác thoải mái.

---

## Format Templates

| Placeholder | Giá trị | Ví dụ |
| :--- | :--- | :--- |
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
