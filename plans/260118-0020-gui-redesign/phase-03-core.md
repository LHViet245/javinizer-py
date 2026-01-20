# Phase 03: Core Logic & API

Status: ⬜ Pending

## Objective

Expose Javinizer's core capabilities (Scrape, Sort, Config) as APIs and implement a background task queue.

## Requirements

### Functional

- [ ] API for `jvSettings.json` (Get/Update).
- [ ] API for `find` (Scrape metadata).
- [ ] API for `sort` (Preview and Execute).
- [ ] Job Manager to handle long-running tasks.

## Implementation Steps

1. [ ] Create `settings_api.py`: Endpoints to read/write settings.
2. [ ] Create `job_manager.py`: Singleton to track background tasks.
3. [ ] Create `operations_api.py`:
    - `POST /api/preview`: Returns sort preview (Dry run).
    - `POST /api/execute`: Starts sort job.
    - `GET /api/scrape`: Returns metadata for a given query.

## Files to Create

- `javinizer/web/api/settings.py`
- `javinizer/web/api/operations.py`
- `javinizer/web/services/job_manager.py`

## Test Criteria

- [ ] Can fetch and update settings via API.
- [ ] Can Trigger a sort preview and get JSON response.
