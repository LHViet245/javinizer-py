# Phase 01: Implementation

Status: ⬜ Pending

## Objective

Enable multi-level folder generation by exposing `output_folder` setting in `jvSettings.json` and mapping it to the sorter logic.

## Requirements

### Functional

- [ ] Add `output_folder` list to `SortSettings` model.
- [ ] Update `sort` command to pass `output_folder` to `SortConfig`.
- [ ] Ensure `output_folder` supports template matching (already in `sorter.py`).

## Implementation Steps

1. [ ] Modify `javinizer/models.py`: Add `output_folder: list[str]` to `SortSettings`.
2. [ ] Modify `javinizer/commands/sort.py`: Pass `output_folder` to `SortConfig` constructor.

## Files to Modify

- `javinizer/models.py` - Add field
- `javinizer/commands/sort.py` - Update mapping

## Test Criteria

- [ ] `javinizer sort` works with default settings (no regression).
- [ ] `javinizer sort` works with `output_folder=["<ACTORS>", "<YEAR>"]`.
