---
description: Chạy bộ kiểm thử tự động (Unit Tests)
---
1. Chạy tất cả các test case bằng pytest
// turbo
run_command("pytest")

2. Nếu user yêu cầu coverage, chạy với cờ coverage
// turbo
run_command("pytest --cov=javinizer tests/")
