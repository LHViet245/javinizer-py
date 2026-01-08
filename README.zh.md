# Javinizer Python

Javinizer 的 Python 移植版 - 用于抓取和整理日本成人视频 (JAV) 元数据的工具。

## 功能特性

- **4个刮削器 (Scrapers)**: DMM, DMM New (Playwright), R18.dev, Javlibrary
- **文件整理 (File Sorting)**: 将视频整理到文件夹中，生成兼容 Jellyfin 的元数据
- **缩略图数据库 (Thumbnail DB)**: 本地保存女优图片
- **翻译 (Translation)**: 将标题翻译成 英文/中文/... (Google/DeepL)
- **代理支持 (Proxy)**: 支持 HTTP 和 SOCKS5
- **NFO 生成**: 兼容 Kodi/Jellyfin/Emby

## 安装

```bash
# Windows
install.bat

# 手动安装
pip install -e .
pip install playwright  # 可选，用于 dmm_new
playwright install chromium
```

## 快速开始

```bash
# 搜索元数据
javinizer find IPX-486

# 整理视频
javinizer sort "D:/Videos/IPX-486.mp4" --dest "D:/Movies"

# 更新已整理的文件夹
javinizer update "D:/Movies/SDDE-761"

# 查看女优列表
javinizer thumbs list
```

## 文档

详情请参阅 [GUIDE.zh.md](GUIDE.zh.md)。

## 系统要求

- Python 3.10+
- 日本 IP (代理) 用于刮削
- Chrome 浏览器 (用于获取 Javlibrary cookie)

## 许可证 (License)

MIT
