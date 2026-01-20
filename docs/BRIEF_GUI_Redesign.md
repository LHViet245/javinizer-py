# 💡 BRIEF: Javinizer Web Station (GUI Redesign)

**Ngày tạo:** 18/01/2026
**Mục tiêu:** Mang toàn bộ sức mạnh của CLI lên giao diện Web trực quan (Hybrid File Explorer style).

---

## 1. VẤN ĐỀ CẦN GIẢI QUYẾT

- CLI mạnh nhưng khó dùng với người không rành dòng lệnh.
- Không xem trước được kết quả (ảnh bìa, thông tin) trước khi Sort/Update.
- Quản lý file (rename, move) trên CLI rủi ro nếu gõ sai lệnh.

## 2. GIẢI PHÁP ĐỀ XUẤT

- Xây dựng **Modern Web App** (FastAPI + TailwindCSS) chạy local.
- Giao diện **Hybrid**: Kết hợp Tree View (File Explorer) và Media Grid (Plex-like).
- Tích hợp **Real-time Terminal Log** để user thấy tool đang làm gì.

## 3. TÍNH NĂNG CHÍNH (Feature Set)

### 🚀 Management Dashboard (Màn hình chính)

- [ ] **Folder Tree Navigation**: Duyệt file hệ thống bên trái.
- [ ] **Media Grid/List View**: Xem danh sách file bên phải (Thumbnail, Tên, ID, Size).
- [ ] **Quick Filters**: Lọc nhanh theo: status (đã có info/chưa có), độ phân giải, studio.

### 🛠 Center Operations (Thao tác)

- [ ] **Preview Sort Mode**: Xem trước kết quả Dry-run (bảng: Nguồn -> Đích).
- [ ] **Execute Sort**: Nút chạy thật sau khi review.
- [ ] **Edit Metadata**: Sửa tay ID, Title nếu scrape sai.
- [ ] **Manual Search**: Tìm lại info với ID khác.

### ⚙️ System & Config

- [ ] **Real-time Log Terminal**: Cửa sổ pop-up hiện log realtime khi chạy task.
- [ ] **Settings UI**: Form chỉnh sửa `jvSettings.json` trực quan.
- [ ] **Actress DB**: Quản lý kho ảnh thumbnail diễn viên.

## 4. YÊU CẦU KỸ THUẬT (Technical Constraints)

- **Backend**: FastAPI (Python) - Tận dụng code CLI có sẵn.
- **Frontend**: Jinja2 Templates + TailwindCSS (styling) + HTMX (tương tác không reload).
- **Log Streaming**: WebSocket hoặc SSE (Server-Sent Events).
- **No Node.js**: Chỉ dùng Python ecosystem để dễ cài đặt (pip install).

## 5. ƯỚC TÍNH SƠ BỘ

- **Độ phức tạp**: Trung bình (Logic có sẵn, chỉ làm thêm UI).
- **Rủi ro**:
  - Xử lý các task chạy lâu (Long-running tasks) trên Web cần Queue (BackgroundTasks).
  - Đồng bộ trạng thái giữa File System thực tế và UI.

## 6. KẾ HOẠCH TRIỂN KHAI

Sẽ chạy `/plan` để chia thành các giai đoạn:

1. **Core**: Setup FastAPI + File Browser cơ bản.
2. **Tasks**: Hệ thống Background Jobs + Log Streaming.
3. **Features**: Port từng lệnh CLI (`sort`, `update`, `find`) lên Web UI.
