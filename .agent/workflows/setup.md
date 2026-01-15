---
description: Cài đặt môi trường và dependencies cho dự án
---
1. Kiểm tra version python hiện tại (yêu cầu >= 3.10)
run_command("python --version")
2. Tạo virtual environment nếu chưa có
// turbo
run_command("python -m venv .venv")
3. Cài đặt project ở chế độ editable với full dev dependencies
// turbo
run_command("pip install -e .[dev,browser,gui]")
4. Kiểm tra cài đặt thành công bằng cách hiển thị version
run_command("javinizer --version")
