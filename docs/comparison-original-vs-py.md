# So sánh Javinizer Original (PowerShell) vs Javinizer-py (Python)

> **Tài liệu tham khảo**: [javinizer-original-analysis.md](file:///e:/Applications/javinizer-py/docs/javinizer-original-analysis.md)  
> **Ngày so sánh**: 2026-01-14  
> **Phiên bản**: 1.0

---

## 🎯 Tóm tắt Nhanh

### ✅ Điểm Mạnh của Javinizer-py

- **Performance tốt hơn**: Python + async scraping
- **Modern tech stack**: Pydantic, httpx, async/await
- **Clean codebase**: Type hints, clear structure
- **Translation support**: Google Translate tích hợp
- **Thumbnail DB**: Portable, relative paths

### ⚠️ Điểm Yếu / Thiếu Sót

- **Ít scrapers hơn**: 4 vs 8 scrapers
- **Không có GUI**: Chưa có dashboard
- **Thiếu Docker**: Chưa có container image
- **CSV settings hạn chế**: Chỉ có actresses.csv
- **Advanced sorting**: Chưa hỗ trợ multi-level folders

---

## 1. So sánh Scrapers

### 1.1 Số lượng Scrapers

| Scraper | Javinizer Original | Javinizer-py | Ghi chú |
|---------|-------------------|---------------|---------|
| **Javlibrary** | ✅ | ✅ | Database lớn nhất |
| **R18.dev** | ✅ (R18Dev) | ✅ | Fast JSON API |
| **DMM (Fanza)** | ✅ | ✅ (2 versions) | dmm + dmm_new |
| **MGStage** | ✅ | ✅ | Publisher specific |
| **JavBus** | ✅ | ❌ **ĐÃ LOẠI BỎ** | Blocked (Region/Age check) |
| **Jav321** | ✅ | ❌ **THIẾU** | CN/JP support |
| **AVEntertainment** | ✅ | ❌ **THIẾU** | JP database |
| **DLGetchu** | ✅ | ❌ **THIẾU** | Digital content |

**Kết luận**: Javinizer-py thiếu/loại bỏ **4 scrapers** (JavBus, Jav321, AVEntertainment, DLGetchu).

### 1.2 Chất lượng Scrapers

#### Javinizer-py có

- ✅ **DMM New**: Sử dụng Playwright, chất lượng cao
- ✅ **Async support**: Native async/await cho parallel scraping
- ✅ **Better error handling**: Retry logic, timeout management
- ✅ **Cloudflare bypass**: curl_cffi cho Javlibrary

#### Javinizer-py thiếu/loại bỏ

- ❌ **JavBus**: Đã loại bỏ do chặn IP/Region và chặn bot quá gắt.
- ❌ **Jav321**: Hỗ trợ Chinese metadata
- ❌ **DLGetchu**: Cho digital content

---

## 2. So sánh Aggregation System

| Tính năng | Javinizer Original | Javinizer-py | Đánh giá |
|-----------|-------------------|---------------|----------|
| **Priority-based** | ✅ | ✅ | Tương đương |
| **Field-level priority** | ✅ | ✅ | jvSettings.json có priority config |
| **Merge actresses** | ✅ | ✅ | Union từ tất cả sources |
| **Merge genres** | ✅ | ✅ | Union từ tất cả sources |
| **Scraper aliases** | ❓ | ✅ | "dmm" → dmm_new + dmm |

**Kết luận**: **TƯƠNG ĐƯƠNG**. Javinizer-py có aggregator tốt với scraper aliases.

---

## 3. So sánh File Detection & Matching

| Tính năng | Javinizer Original | Javinizer-py | Đánh giá |
|-----------|-------------------|---------------|----------|
| **Built-in matcher** | ✅ | ✅ | Regex-based ID extraction |
| **Custom regex** | ✅ | ❓ **UNCLEAR** | Cần kiểm tra |
| **Direct URL** | ✅ | ✅ | Scrape bằng tham số `--url` |
| **Recursive scan** | ✅ | ✅ | --recursive flag |
| **Min file size** | ✅ | ✅ | Default 100MB |
| **File extensions** | ✅ | ✅ | .mp4, .avi, .mkv, .wmv |

**Kết luận**: Javinizer-py thiếu **Direct URL scraping** và **custom regex** chưa rõ.

---

## 4. So sánh Sorting System

### 4.1 Basic Sorting

| Tính năng | Javinizer Original | Javinizer-py | Đánh giá |
|-----------|-------------------|---------------|----------|
| **Template-based naming** | ✅ | ✅ | `<ID>`, `<TITLE>`, `<YEAR>`, etc. |
| **Folder format** | ✅ | ✅ | Customizable |
| **File format** | ✅ | ✅ | Customizable |
| **NFO format** | ✅ | ✅ | Customizable |
| **Sanitize filenames** | ✅ | ✅ | Remove invalid chars |
| **Title truncation** | ❓ | ✅ | Smart truncation với max_length |

**Kết luận**: **TƯƠNG ĐƯƠNG**

### 4.2 Advanced Sorting

| Tính năng | Javinizer Original | Javinizer-py | Đánh giá |
|-----------|-------------------|---------------|----------|
| **Multi-level folders** | ✅ | ❌ **THIẾU** | `<ACTORS>/<YEAR>/<ID>` |
| **Output folder array** | ✅ | ❌ **THIẾU** | `["<ACTORS>", "<YEAR>"]` |
| **Group by actress** | ✅ | ⚠️ **HẠN CHẾ** | Có cấu hình nhưng chưa implement |
| **Custom placeholders** | ✅ | ⚠️ **HẠN CHẾ** | Chỉ có placeholders cơ bản |

**Ví dụ Javinizer Original có mà Javinizer-py thiếu**:

```
├─Nishimiya Yume              ← Folder theo diễn viên
│  └─2020                     ← Subfolder theo năm
│      └─IDBD-979 [...]       ← Folder phim
│          │   fanart.jpg
│          │   IDBD-979.mp4
│          ├─.actors           ← Actor thumbs folder
│          └─extrafanart       ← Multiple fanart
```

Javinizer-py hiện tại chỉ hỗ trợ:

```
├─IDBD-979                    ← Direct folder
│   cover.jpg
│   backdrop.jpg
│   IDBD-979.mp4
│   IDBD-979.nfo
```

**Kết luận**: Javinizer-py **THIẾU advanced sorting** (multi-level folders).

---

## 5. So sánh Multi-language Support

| Tính năng | Javinizer Original | Javinizer-py | Đánh giá |
|-----------|-------------------|---------------|----------|
| **Native languages** | EN, JP, CN | EN, JP | Thiếu CN |
| **Machine translation** | ✅ Google Translate | ✅ Google Translate | Tương đương |
| **Translatable fields** | Title, Description, Genre | Title, Description | Thiếu Genre |
| **Target languages** | EN, JP, CN | EN, VI, ZH, KO | **PY TỐT HƠN** |
| **Translation provider** | Google only | Google + DeepL | **PY TỐT HƠN** |

**Kết luận**: Javinizer-py có **translation tốt hơn** (DeepL, nhiều ngôn ngữ).

---

## 6. So sánh Configuration System

### 6.1 Settings File

| Tính năng | Javinizer Original | Javinizer-py | Đánh giá |
|-----------|-------------------|---------------|----------|
| **JSON config** | ✅ jvSettings.json | ✅ jvSettings.json | Tương đương |
| **Priority config** | ✅ | ✅ | Per-field priority |
| **Proxy config** | ✅ | ✅ | HTTP + SOCKS5 |
| **Scraper toggle** | ✅ | ✅ | Enable/disable scrapers |
| **Throttle settings** | ✅ | ⚠️ **HẠN CHẾ** | Có sleep_between_requests |
| **Timeout config** | ✅ | ✅ | Configurable |

### 6.2 CSV Settings

| File CSV | Javinizer Original | Javinizer-py | Đánh giá |
|----------|-------------------|---------------|----------|
| **actresses.csv** | ✅ | ✅ | Tương đương |
| **genres.csv** | ✅ | ✅ | Đã hỗ trợ |
| **studios.csv** | ✅ | ✅ | Đã hỗ trợ |

**Kết luận**: Javinizer-py đã hỗ trợ đầy đủ **genres.csv** và **studios.csv**.

---

## 7. So sánh Media Assets

| Asset | Javinizer Original | Javinizer-py | Đánh giá |
|-------|-------------------|---------------|----------|
| **Poster** | ✅ folder.jpg | ✅ cover.jpg | Tương đương |
| **Fanart** | ✅ fanart.jpg | ✅ backdrop.jpg | Tương đương |
| **Extra Fanart** | ✅ extrafanart/*.jpg | ❌ **THIẾU** | Multiple fanart |
| **Actor Thumbs** | ✅ .actors/*.jpg | ✅ thumbs/* | **PY TỐT HƠN** |
| **Trailer** | ✅ `<ID>`-trailer.mp4 | ❌ **THIẾU** | Download trailer |
| **Auto-crop poster** | ✅ Python/Pillow | ✅ Pillow | Tương đương |

**Kết luận**: Javinizer-py thiếu **extrafanart** và **trailer download**.

---

## 8. So sánh CLI/GUI

### 8.1 CLI Commands

| Command | Javinizer Original | Javinizer-py | Đánh giá |
|---------|-------------------|---------------|----------|
| **Find metadata** | ✅ `-Find` | ✅ `find` | Tương đương |
| **Sort single file** | ✅ `-Path` | ✅ `sort` | Tương đương |
| **Sort directory** | ✅ `-Path + -Recurse` | ✅ `sort-dir` | **PY TỐT HƠN** (dedicated command) |
| **Update metadata** | ❓ | ✅ `update` | **PY TỐT HƠN** |
| **Batch update** | ❓ | ✅ `update-dir` | **PY TỐT HƠN** |
| **Thumbs management** | ❓ | ✅ `thumbs` | **PY TỐT HƠN** |
| **Config management** | ✅ `-OpenSettings` | ✅ `config` | **PY TỐT HƠN** |
| **Direct URL scrape** | ✅ `-Url` | ✅ `find --url` | Tương đương |

### 8.2 GUI

| Tính năng | Javinizer Original | Javinizer-py | Đánh giá |
|-----------|-------------------|---------------|----------|
| **Web Dashboard** | ✅ PowerShell Universal | ❌ **THIẾU** | Không có GUI |
| **GUI Port config** | ✅ `-Port` | ❌ | N/A |
| **GUI Features** | Full-featured | ❌ | N/A |

**Kết luận**: Javinizer Original có **GUI dashboard**, Javinizer-py **THIẾU hoàn toàn**.

---

## 9. So sánh Deployment

| Deployment | Javinizer Original | Javinizer-py | Đánh giá |
|------------|-------------------|---------------|----------|
| **Package manager** | PowerShell Gallery | pip (local) | **ORIGINAL TỐT HƠN** |
| **Docker image** | ✅ Docker Hub | ❌ **THIẾU** | Không có image |
| **Docker Compose** | ✅ | ❌ **THIẾU** | Không có |
| **Cross-platform** | ✅ PS7 | ✅ Native Python | **PY TỐT HƠN** |
| **Installation** | `Install-Module` | `pip install -e .` | **ORIGINAL TỐT HƠN** |

**Kết luận**: Javinizer-py thiếu **Docker** và **package distribution**.

---

## 10. So sánh Tính năng Đặc biệt

### 10.1 Thumbnail Database

| Tính năng | Javinizer Original | Javinizer-py | Đánh giá |
|-----------|-------------------|---------------|----------|
| **Local thumbnail DB** | ❓ | ✅ | **PY độc quyền** |
| **Portable paths** | ❓ | ✅ | Relative paths |
| **Auto-download** | ❓ | ✅ | Auto tải ảnh diễn viên |
| **CSV management** | ✅ actresses.csv | ✅ actresses.csv | Tương đương |

**Kết luận**: Javinizer-py có **thumbnail DB tốt hơn**.

### 10.2 Health Check

| Tính năng | Javinizer Original | Javinizer-py | Đánh giá |
|-----------|-------------------|---------------|----------|
| **Scraper health check** | ❓ | ✅ `health.py` | **PY độc quyền** |
| **Verify scrapers** | ❓ | ✅ | Test scrapers |

---

## 11. Bảng So sánh Tổng quan

| Aspect | Javinizer Original | Javinizer-py | Winner |
|--------|-------------------|---------------|--------|
| **Scrapers** | 8 scrapers | 4 scrapers | ⭐ Original |
| **Aggregation** | ✅ | ✅ | 🟰 Tương đương |
| **File Detection** | ✅ Direct URL | ❌ No URL | ⭐ Original |
| **Basic Sorting** | ✅ | ✅ | 🟰 Tương đương |
| **Advanced Sorting** | ✅ Multi-level | ❌ Single-level | ⭐ Original |
| **Translation** | Google only | Google + DeepL | ⭐ Py |
| **CSV Settings** | 3 files | 1 file | ⭐ Original |
| **Media Assets** | Trailer + Extrafanart | No trailer | ⭐ Original |
| **CLI** | Basic | Advanced commands | ⭐ Py |
| **GUI** | ✅ Dashboard | ❌ None | ⭐ Original |
| **Deployment** | Docker + Gallery | Local only | ⭐ Original |
| **Thumbnail DB** | Basic | Advanced + Portable | ⭐ Py |
| **Performance** | Slow (PS) | Fast (async) | ⭐ Py |
| **Modern Stack** | PS7 + Python | Pure Python | ⭐ Py |

---

## 12. Thiếu Sót và Điểm Yếu của Javinizer-py

### 🔴 Critical (Ảnh hưởng lớn)

1. **Thiếu 4 scrapers**
   - JavBus, Jav321, AVEntertainment, DLGetchu
   - **Impact**: Giảm coverage metadata, đặc biệt cho phim niche

2. **Không có GUI**
   - Không có web dashboard
   - **Impact**: Khó sử dụng cho người không quen CLI

3. **Thiếu advanced sorting**
   - Không hỗ trợ multi-level folders (`<ACTORS>/<YEAR>/<ID>`)
   - **Impact**: Không organize được theo diễn viên/năm

4. **Không có Docker**
   - Không có Docker image, Docker Compose
   - **Impact**: Khó deploy lên server

### 🟡 Medium (Ảnh hưởng trung bình)

303: [Resolved] **Thiếu CSV settings**
304:    - Đã support `genres.csv`, `studios.csv`

1. **Thiếu media assets**
   - Không download trailer
   - Không download extrafanart
   - **Impact**: Media server không có đầy đủ assets

312: [Resolved] **Thiếu Direct URL scraping**
313:    - Đã support `--url`

1. **Chưa phát hành package**
   - Chưa lên PyPI, chưa có wheel
   - **Impact**: Khó cài đặt cho người dùng thông thường

### 🟢 Low (Ảnh hưởng nhỏ)

1. **Thiếu custom regex**
   - Unclear nếu có hỗ trợ custom regex
   - **Impact**: Không flexible cho pattern đặc biệt

2. **Throttle settings đơn giản**
    - Chỉ có `sleep_between_requests`, không có limit/window
    - **Impact**: Có thể bị rate limit

---

## 13. Điểm Mạnh của Javinizer-py

### ✅ Ưu điểm vượt trội

1. **Performance tốt hơn**
   - Python async/await vs PowerShell tuần tự
   - Parallel scraping

2. **Modern tech stack**
   - Pydantic models
   - Type hints
   - httpx, curl_cffi

3. **Better CLI**
   - Dedicated commands (`sort-dir`, `update`, `config`)
   - Rich UI với colors
   - Click framework

4. **Thumbnail DB**
   - Portable với relative paths
   - Auto-download
   - CSV management

5. **Translation tốt hơn**
   - Google + DeepL
   - Nhiều target languages (VI, KO, ZH)

6. **Health check**
   - Test scrapers
   - Verify functionality

7. **Better error handling**
   - Proper exceptions
   - Retry logic
   - Timeout management

---

## 14. Roadmap Đề xuất cho Javinizer-py

### Phase 1: Critical Features (P0)

- [ ] **Implement missing scrapers**
  - [ ] Jav321 scraper (Chinese support)
  - [ ] AVEntertainment scraper
  - [ ] MGStage scraper
  - [ ] *Self-hosted/Alternative JavBus* (Consider later if proxy situation improves)
  - [ ] AVEntertainment scraper
  - [ ] MGStage scraper

- [ ] **Advanced sorting**
  - [ ] Multi-level folder support (`<ACTORS>/<YEAR>/<ID>`)
  - [ ] `output_folder` array config
  - [ ] Group by actress implementation

- [ ] **Direct URL scraping**
  - [ ] Accept URLs in `find` command
  - [ ] Support multiple URLs for aggregation

### Phase 2: Important Features (P1)

- [ ] **GUI Dashboard**
  - [ ] FastAPI/Flask web UI
  - [ ] Dashboard cho sort operations
  - [ ] Settings management page

- [ ] **Docker support**
  - [ ] Create Docker image
  - [ ] Docker Compose file
  - [ ] Push to Docker Hub

- [ ] **CSV settings expansion**
  - [ ] genres.csv support
  - [ ] studios.csv support
  - [ ] Translation override

- [ ] **Media assets**
  - [ ] Trailer download
  - [ ] Extrafanart support
  - [ ] Multiple screenshot download

### Phase 3: Nice-to-have (P2)

- [ ] **Package distribution**
  - [ ] Publish to PyPI
  - [ ] Create wheel package
  - [ ] Installation via `pip install javinizer`

- [ ] **Custom regex**
  - [ ] User-defined regex patterns
  - [ ] Pattern testing tool

- [ ] **Advanced throttle**
  - [ ] Rate limiting với window
  - [ ] Per-scraper throttle config

---

## 15. Kết luận

### Tình trạng hiện tại

**Javinizer-py** là một **rewrite tốt** của Javinizer gốc với:

- ✅ Performance tốt hơn (async)
- ✅ Codebase sạch hơn (Python, type hints)
- ✅ CLI tốt hơn (dedicated commands)
- ✅ Thumbnail DB tốt hơn
- ✅ Hỗ trợ MGStage scraper

Tuy nhiên vẫn còn **thiếu nhiều tính năng** quan trọng:

- ❌ 4 scrapers (JavBus removed, others missing)
- ❌ Không có GUI
- ❌ Không có Docker
- ❌ Advanced sorting hạn chế
- ❌ Thiếu media assets (trailer, extrafanart)

### Đánh giá tổng thể

| Metric | Score | Comment |
|--------|-------|---------|
| **Feature Coverage** | 60% | Thiếu nhiều tính năng |
| **Code Quality** | 95% | Excellent codebase |
| **Performance** | 90% | Nhanh hơn original |
| **Usability** | 70% | CLI tốt nhưng thiếu GUI |
| **Deployment** | 40% | Khó deploy |

**Overall**: Javinizer-py là **foundation tốt** nhưng cần thêm nhiều features để **thay thế** hoàn toàn Javinizer gốc.

### Ưu tiên phát triển

1. **P0 (Critical)**: Scrapers, Advanced sorting, Direct URL
2. **P1 (Important)**: GUI, Docker, CSV settings, Media assets
3. **P2 (Nice-to-have)**: PyPI, Custom regex, Advanced throttle

---

**Phân tích bởi**: Antigravity AI  
**Ngày**: 2026-01-14  
**Phiên bản**: 1.0
