---
description: Quy trình kiểm tra toàn diện trước khi commit/PR
---
1. Chạy Workflow Lint để đảm bảo code sạch
// turbo
run_command("ruff check .")
// turbo
run_command("mypy .")

2. Chạy Workflow Test để đảm bảo logic đúng
// turbo
run_command("pytest")
