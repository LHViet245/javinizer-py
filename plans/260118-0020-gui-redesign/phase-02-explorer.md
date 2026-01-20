# Phase 02: File Explorer (Left Panel)

Status: ⬜ Pending

## Objective

Implement the left sidebar file tree to browse the filesystem and select files/folders.

## Requirements

### Functional

- [ ] API endpoint to list directories and contents.
- [ ] UI component (Recursive Tree) to display folders.
- [ ] Expand/Collapse folder functionality.
- [ ] filtering/hidden file logic (ignore system files).

## Implementation Steps

1. [ ] Create API `GET /api/filesystem/list?path=...` in `javinizer/web/api/filesystem.py`.
2. [ ] Create Jinja2 component `file_tree.html` (recursive).
3. [ ] Use HTMX to lazy-load folder contents on click.
4. [ ] Add Alpine.js for client-side selection state.

## Files to Create/Modify

- `javinizer/web/api/filesystem.py`
- `javinizer/web/templates/components/file_tree.html`
- `javinizer/web/server.py` (Mount API router)

## Test Criteria

- [ ] Clicking a folder expands it without full page reload.
- [ ] Can navigate to nested subdirectories.
- [ ] Clicking a file highlights it and updates the specific selection state.
