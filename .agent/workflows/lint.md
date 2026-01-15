---
description: Kiểm tra chất lượng code (Lint & Type Check)
---
1. Chạy Ruff để kiểm tra và format code style
// turbo
run_command("ruff check . --fix")
// turbo
run_command("ruff format .")

2. Chạy MyPy để kiểm tra kiểu dữ liệu (Strict mode)
// turbo
run_command("mypy .")
