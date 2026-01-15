---
description: Đẩy code hiện tại lên Remote Repository (GitHub) một cách an toàn
---
1. Chạy Ruff để kiểm tra code (Linting)
// turbo
run_command("ruff check .")

2. Chạy MyPy để kiểm tra kiểu dữ liệu (Type Safety)
// turbo
run_command("mypy .")

3. Chạy Pytest để đảm bảo không lỗi logic
// turbo
run_command("pytest")

4. Kiểm tra trạng thái git (đảm bảo working tree sạch sẽ)
run_command("git status")

5. Lấy code mới nhất từ remote về (Rebase)
// turbo
run_command("git pull --rebase origin HEAD")

6. Đẩy code lên branch hiện tại
// turbo
run_command("git push origin HEAD")
