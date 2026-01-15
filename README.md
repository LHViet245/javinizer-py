# Javinizer - Python JAV Metadata Scraper & Organizer

[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

**Javinizer** is a powerful Python CLI tool designed to automate the scraping, organizing, and management of Japanese Adult Video (JAV) files. It fetches high-quality metadata from multiple sources, downloads artwork, and organizes your collection into a structure compatible with media servers like Jellyfin, Emby, and Kodi.

[English](#english) | [Tiếng Việt](#tiếng-việt) | [中文](#中文)

---

<a name="english"></a>

## 🇬🇧 English

### Project Overview

Javinizer aims to provide a robust, cross-platform solution for JAV collectors. It focuses on:

* **Accuracy:** Aggregates data from multiple sources (DMM, R18Dev, Javlibrary, JavBus, MGStage) for complete metadata.
* **Automation:** Batch searching, sorting, and updating capabilities.
* **Organization:** Standardized folder and file naming with NFO generation.
* **Portability:** Includes features like relative path thumbnail databases.
* **Web GUI:** Optional FastAPI-based web interface for easy management.

### Installation

**Requirements:**

* Python 3.10 or higher
* Google Chrome (for some scrapers like Javlibrary)

**Quick Install (Windows):**
Run `install.bat` included in the repository.

**Manual Install:**

```bash
pip install -e .
# Optional: Install Playwright for the 'dmm_new' scraper (recommended for high quality)
pip install playwright
playwright install chromium
```

### CLI Usage

The main command is `javinizer`. Here are the available commands:

#### 1. Find Metadata (`find`)

Search for metadata by Movie ID.

```bash
javinizer find [MOVIE_ID] [FLAGS]
```

* `--source, -s`: Comma-separated sources (e.g., `r18dev,dmm`). Default: all available.
* `--proxy, -p`: Proxy URL (e.g., `socks5://127.0.0.1:1080`).
* `--nfo`: Output NFO XML content to console.
* `--json`: Output JSON data to console.
* `--no-aggregate`: Disable aggregation, use the first successful result.
* `--log-file`: Path to log file.
* `--verbose, -v`: Enable verbose (debug) logging.

#### 2. Sort Video File (`sort`)

Organize a video file into a structured folder with metadata and images.

```bash
javinizer sort [VIDEO_PATH] [FLAGS]
```

* `--dest, -d`: Destination root folder (e.g., `D:/Movies`).
* `--source, -s`: Scraper sources (comma-separated).
* `--proxy, -p`: Proxy URL.
* `--dry-run`: Preview actions without making changes.
* `--copy`: Copy file instead of moving.

#### 3. Batch Sort Directory (`sort-dir`)

Recursively scan and sort all videos in a directory.

```bash
javinizer sort-dir [INPUT_DIR] [FLAGS]
```

* `--dest, -d`: Destination folder (Required).
* `--recursive, -r`: Scan subdirectories.
* `--source, -s`: Scraper sources.
* `--proxy, -p`: Proxy URL.
* `--min-size`: Minimum file size in MB to process (default: 100).
* `--dry-run`: Preview without changes.
* `--copy`: Copy instead of move.

#### 4. Update Metadata (`update`)

Refresh metadata for an existing sorted folder.

```bash
javinizer update [FOLDER_PATH]
```

* `--source, -s`: Scraper sources.
* `--proxy, -p`: Proxy URL.
* `--dry-run`: Preview without changes.
* `--nfo-only`: Only regenerate NFO, skip image downloads.

#### 5. Batch Update Directory (`update-dir`)

Update metadata for all sorted folders in a directory.

```bash
javinizer update-dir [INPUT_DIR] [FLAGS]
```

* `--recursive, -r`: Search subdirectories recursively.
* `--source, -s`: Scraper sources.
* `--proxy, -p`: Proxy URL.
* `--dry-run`: Preview without changes.
* `--nfo-only`: Only update NFO, skip images.

#### 6. Thumbnail Database (`thumbs`)

Manage the local actress thumbnail database.

```bash
javinizer thumbs [COMMAND]
```

* `list`: List actresses in database.
  * `--filter, -f`: Filter by name.
* `update`: Bulk download/update images for actresses in the database.
  * `--force`: Re-download existing images.

#### 7. Configuration (`config`)

Manage Javinizer configuration.

```bash
javinizer config [COMMAND]
```

* `show`: Show current configuration.
* `set-proxy [URL]`: Set default proxy. Use `--disable` to turn off.
* `set-sort-format`: Set folder/file/NFO naming templates.
* `set-javlibrary-cookies`: Manually set Cloudflare cookies.
* `get-javlibrary-cookies`: Automatically capture Cloudflare cookies using a browser (requires `undetected-chromedriver`).

#### 8. Web GUI (`gui`)

Start The FastAPI-based web interface.

```bash
javinizer gui [FLAGS]
```

* `--host, -h`: Host to bind (default: 127.0.0.1).
* `--port, -p`: Port to bind (default: 8000).
* `--reload`: Enable auto-reload for development.

**Note:** Requires GUI dependencies: `pip install javinizer[gui]`

### Core Modules

* **Scrapers (`javinizer.scrapers`)**: Handles fetching data.
  * *R18Dev*: Fast, JSON-based API.
  * *DMM/DMM New*: High-quality metadata and images. `dmm_new` uses Playwright.
  * *Javlibrary*: Comprehensive database, requires Cloudflare bypass.
* **Aggregator (`javinizer.aggregator`)**: Merges data from multiple scrapers based on priority settings to ensure the most complete metadata.
* **Sorter (`javinizer.sorter`)**: Manages file operations using customizable patterns (e.g., `<ID> - <TITLE>`).
* **Thumbnail DB (`javinizer.thumbs`)**: Maintains a local database of actress images to avoid redownloading and enable portability.

### Contribution Guidelines

1. Fork the repository.
2. Create a feature branch.
3. Ensure code follows the existing style (Conflicting with `ruff` formatting is discouraged).
4. Submit a Pull Request describing your changes.

---

<a name="tiếng-việt"></a>

## 🇻🇳 Tiếng Việt

### Giới thiệu

**Javinizer** là công cụ dòng lệnh (CLI) bằng Python giúp tự động hóa việc tải thông tin, sắp xếp và quản lý file phim JAV. Nó lấy dữ liệu từ nhiều nguồn, tải cover/poster và tổ chức thư mục tương thích với Jellyfin, Emby, Kodi.

### Cài đặt

**Yêu cầu:**

* Python 3.10+
* Google Chrome (để lấy cookie cho một số nguồn)

**Cài đặt nhanh (Windows):**
Chạy file `install.bat`.

**Cài đặt thủ công:**

```bash
pip install -e .
# Tùy chọn: Cài Playwright cho nguồn 'dmm_new' (khuyên dùng)
pip install playwright
playwright install chromium
```

### Hướng dẫn sử dụng CLI

Lệnh chính là `javinizer`. Các lệnh con thường dùng:

#### 1. Tìm thông tin (`find`)

Tìm kiếm metadata theo mã phim.

```bash
javinizer find [MOVIE_ID] [CỜ]
```

* `--source, -s`: Các nguồn tìm kiếm (vd: `r18dev,dmm`). Mặc định: tất cả.
* `--proxy, -p`: URL Proxy (vd: `socks5://127.0.0.1:1080`).
* `--nfo`: Xuất nội dung NFO ra màn hình.
* `--json`: Xuất dữ liệu dạng JSON.

#### 2. Sắp xếp file (`sort`)

Sắp xếp file video vào folder chuẩn kèm hình ảnh và NFO.

```bash
javinizer sort [ĐƯỜNG_DẪN_VIDEO] [CỜ]
```

* `--dest, -d`: Thư mục đích (vd: `D:/Movies`).
* `--dry-run`: Chạy thử (không thay đổi file).
* `--copy`: Copy file thay vì di chuyển (move).

#### 3. Sắp xếp hàng loạt (`sort-dir`)

Quét và sắp xếp toàn bộ video trong thư mục.

```bash
javinizer sort-dir [THƯ_MỤC_VÀO] [CỜ]
```

* `--dest, -d`: Thư mục đích (Bắt buộc).
* `--recursive, -r`: Quét cả thư mục con.

#### 4. Cập nhật (`update`)

Cập nhật lại metadata cho thư mục phim đã có.

```bash
javinizer update [THƯ_MỤC_PHIM]
```

### Các module chính

* **Scrapers**: Module tải dữ liệu. Hỗ trợ DMM (ảnh chất lượng cao), R18Dev (nhanh), Javlibrary.
* **Aggregator**: Gộp dữ liệu từ nhiều nguồn để có thông tin đầy đủ nhất (vd: Tiêu đề từ DMM, mã từ Javlibrary).
* **Sorter**: Quản lý việc đặt tên file/folder theo mẫu cấu hình (vd: `<ID> - <TITLE>`).
* **Thumbnail DB**: Quản lý kho ảnh diễn viên cục bộ, giúp hiển thị ảnh diễn viên trong Jellyfin mà không cần tải lại nhiều lần.

### Đóng góp

1. Fork dự án.
2. Tạo nhánh tính năng mới.
3. Tuân thủ quy chuẩn code (format bằng `ruff` nếu có thể).
4. Gửi Pull Request.

---

<a name="中文"></a>

## 🇨🇳 中文

### 项目概述

**Javinizer** 是一个基于 Python 的命令行工具，用于自动抓取、整理和管理日本成人视频 (JAV) 文件。它可以从多个来源获取高质量的元数据，下载封面和海报，并将您的收藏整理成兼容 Jellyfin、Emby 和 Kodi 的结构。

### 安装说明

**系统要求：**

* Python 3.10 或更高版本
* Google Chrome (用于获取部分站点的 Cookie)

**Windows 快速安装：**
运行项目目录下的 `install.bat`。

**手动安装：**

```bash
pip install -e .
# 可选：安装 Playwright 以使用 'dmm_new' 刮削器 (推荐)
pip install playwright
playwright install chromium
```

### CLI 命令行用法

主命令为 `javinizer`。常用子命令如下：

#### 1. 搜索元数据 (`find`)

按番号搜索元数据。

```bash
javinizer find [番号] [参数]
```

* `--source, -s`: 数据源 (如 `r18dev,dmm`)。默认会搜索所有可用源。
* `--proxy, -p`: 代理地址 (如 `socks5://127.0.0.1:1080`)。
* `--nfo`: 输出 NFO XML 内容。
* `--json`: 输出 JSON 格式数据。

#### 2. 整理视频文件 (`sort`)

将视频文件整理到带元数据和图片的标准文件夹中。

```bash
javinizer sort [视频路径] [参数]
```

* `--dest, -d`: 目标根目录 (如 `D:/Movies`)。如果不指定，则并在当前目录整理。
* `--dry-run`: 试运行（仅预览，不执行操作）。
* `--copy`: 复制文件而不是移动。

#### 3. 批量整理 (`sort-dir`)

递归扫描并整理目录下的所有视频。

```bash
javinizer sort-dir [输入目录] [参数]
```

* `--dest, -d`: 目标目录 (必须)。
* `--recursive, -r`: 包含子目录。

#### 4. 更新元数据 (`update`)

刷新现有影片文件夹的元数据。

```bash
javinizer update [影片目录]
```

### 核心模块

* **Scrapers (刮削器)**: 负责获取数据。支持 R18Dev (快速 API), DMM (高质量图片), Javlibrary (数据全)。
* **Aggregator (聚合器)**: 根据优先级设置合并多个来源的数据，确保元数据最完整。
* **Sorter (整理器)**: 使用可自定义的模版 (如 `<ID> - <TITLE>`) 处理文件和文件夹命名。
* **Thumbnail DB (头像库)**: 维护本地女优头像数据库，避免重复下载，并支持便携式路径。

### 参与贡献

1. Fork 本仓库。
2. 创建一个新分支。
3. 确保代码风格一致。
4. 提交 Pull Request。

---
