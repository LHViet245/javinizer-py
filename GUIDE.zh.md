# Javinizer Python - 用户指南

## 安装

### 系统要求

- **Python 3.10+**
- **Chrome 浏览器** (用于获取 Javlibrary cookie)

### 快速安装

```bash
cd javinizer-py
pip install -e .
```

或者运行 `install.bat` (Windows).

### 已安装的 Python 包

| 包名 | 功能 |
| --- | --------- |
| `httpx[socks]` | 支持 SOCKS 代理的 HTTP 客户端 |
| `beautifulsoup4` | HTML 解析 |
| `lxml` | XML/HTML 解析器 |
| `pydantic` | 数据验证 |
| `click` | CLI 框架 |
| `rich` | 美观的终端界面 |
| `Pillow` | 图像处理 (裁切海报) |
| `curl_cffi` | **绕过 Cloudflare** (TLS 模拟) |
| `undetected-chromedriver` | 自动获取 Javlibrary cookie |
| `setuptools` | 支持 Python 3.12+ |

### 可选包 (Optional)

```bash
# 安装 Playwright 以支持 dmm_new (更高质量的元数据)
pip install playwright
playwright install chromium
```

---

## 主要功能

| 功能 | 状态 | 描述 |
|-----------|------------|-------|
| **刮削器 (Scrapers)** | ✅ | DMM, DMM New, R18Dev, Javlibrary |
| **文件整理 (Sorting)** | ✅ | 将视频整理到含有元数据的文件夹中 |
| **更新系统 (Update)** | ✅ | 更新已整理文件夹的元数据 |
| **缩略图数据库** | ✅ | 本地女优图片数据库 |
| **翻译 (Translation)** | ✅ | 将标题翻译为 EN/VI/ZH... |
| **代理支持 (Proxy)** | ✅ | HTTP 和 SOCKS5 |

---

## 主要命令

### 1. 查找元数据

```bash
# 基本搜索
javinizer find IPX-486

# 指定来源 (dmm 会自动扩展为 dmm_new + dmm)
javinizer find IPX-486 --source dmm,r18dev

# 使用代理 (需要日本 IP)
javinizer find IPX-486 --proxy socks5://127.0.0.1:10808

# 输出 NFO
javinizer find IPX-486 --nfo

# 输出 JSON
javinizer find IPX-486 --json
```

### 2. 视频整理 (File Sorting)

```bash
# 整理单个文件 (原地整理)
javinizer sort "D:/Videos/IPX-486.mp4"

# 整理到目标目录
javinizer sort "D:/Videos/IPX-486.mp4" --dest "D:/Movies"

# 整理整个目录
javinizer sort-dir "D:/Videos" --dest "D:/Movies" --recursive

# 预览 (不进行实际更改)
javinizer sort "video.mp4" --dry-run

# 复制而不是移动
javinizer sort "video.mp4" --copy
```

### 3. 更新元数据 (Update)

```bash
# 更新已整理的文件夹
javinizer update "D:/Movies/SDDE-761"

# 更新整个目录
javinizer update-dir "D:/Movies" --recursive

# 仅更新 NFO (跳过图片)
javinizer update "D:/Movies/SDDE-761" --nfo-only
```

### 4. 缩略图数据库管理

```bash
# 列出女优
javinizer thumbs list

# 按名称过滤
javinizer thumbs list --filter "Yua"

# 从数据库更新图片
javinizer thumbs update
```

### 5. 配置

```bash
# 显示配置
javinizer config show

# 设置默认代理
javinizer config set-proxy socks5://127.0.0.1:10808

# 禁用代理
javinizer config set-proxy --disable

# 更改整理格式
javinizer config set-sort-format --folder "<ID> - <TITLE>"
javinizer config set-sort-format --file "<ID>"

# 调试/错误日志
javinizer find IPX-486 --verbose
javinizer find IPX-486 --log-file javinizer.log
```

---

## 配置文件 (jvSettings.json)

配置保存在 `javinizer-py/jvSettings.json`.

### 主要部分

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

## 翻译 (Translation)

Javinizer 支持将日语标题和简介翻译成其他语言。

### 支持的服务商

| 服务商 | 免费 | 质量 | 备注 |
|----------|----------|------------|---------|
| `google` | ✅ 是 | 好 | 默认，不需要 API Key |
| `deepl` | 免费额度 | 很好 | 需要 deepl.com 的 API Key |

### 翻译配置

```json
"translation": {
  "enabled": true,
  "provider": "google",
  "target_language": "zh",
  "deepl_api_key": null,
  "translate_title": true,
  "translate_description": true
}
```

### 目标语言

| 代码 | 语言 |
|----|----------|
| `en` | 英语 |
| `vi` | 越南语 |
| `zh` |即使中文 |
| `ko` | 韩语 |

---

## Javlibrary - 绕过 Cloudflare

Javlibrary 受 Cloudflare 保护。使用方法：

### 第1步：获取 Cookie

```bash
# 如果 不使用 代理:
javinizer config get-javlibrary-cookies

# 如果 使用 代理 (重要):
javinizer config get-javlibrary-cookies --proxy socks5://127.0.0.1:10808
```

> ⚠️ **注意**: Cloudflare cookie 与 IP 绑定！获取 cookie 和刮削时必须使用相同的代理。

### 第2步：使用

```bash
javinizer find SDDE-761 --source javlibrary
```

---

## 数据源 (Scrapers)

| 来源 | 需要代理 | 备注 |
|-------|---------------|---------|
| `r18dev` | 是 (日本 IP) | JSON API, 速度快, **推荐** |
| `dmm_new` | 是 | 使用 Playwright, 高质量 |
| `dmm` | 是 | 旧版网站, 后备方案 |
| `javlibrary` | 是 + Cookies | 需要绕过 Cloudflare |

### 刮削器别名 (Alias)

当你指定 `--source dmm` 时，它会自动扩展为 `dmm_new, dmm`：
-首 试 `dmm_new` (如果安装了 Playwright)

- 失败则回退到 `dmm`

---

## 缩略图数据库

整理视频时，Javinizer 会自动把女优图片保存到 `thumbs/` 文件夹。

### 结构

```
javinizer-py/
├── jvSettings.json
├── actresses.csv      # 女优数据库
└── thumbs/            # 女优图片
    ├── 皆/
    │   └── 皆月ひかる/
    │       └── folder.jpg
    └── 南/
        └── 南日菜乃/
            └── folder.jpg
```

---

## 格式模板

| 占位符 | 值 | 示例 |
|-------------|---------|-------|
| `<ID>` | 番号 | IPX-486 |
| `<TITLE>` | 标题 | Beautiful Girl... |
| `<STUDIO>` | 片商 | Idea Pocket |
| `<YEAR>` | 年份 | 2020 |
| `<ACTORS>` | 演员 | Sakura Momo |
| `<LABEL>` | 厂牌 | - |

**格式示例:**

```text
<ID>                          → IPX-486
<ID> - <TITLE>                → IPX-486 - Beautiful Girl...
<TITLE> (<YEAR>) [<ID>]       → Beautiful Girl... (2020) [IPX-486]
```

---

## 输出结构 (Jellyfin)

```text
D:/Movies/
  SDDE-761/
    SDDE-761.mp4
    SDDE-761.nfo
    cover.jpg       ← 海报 (裁剪后)
    backdrop.jpg    ← 完整封面
```

---

## 重要提示

1. **需要日本 IP**: 所有来源都需要日本代理。
2. **Javlibrary**: Cookies 与 IP 绑定。
3. **翻译**: 通过 SOCKS 代理时可能会很慢。
4. **聚合**: 使用 `--source r18dev,dmm` 来合并多个来源的元数据。
