# Phase 05: Real-time Logs

Status: ⬜ Pending

## Objective

Implement the "Terminal HUD" at the bottom to show real-time progress.

## Requirements

### Functional

- [ ] Capture Console output (stdout/log) from backend.
- [ ] Stream logs to frontend via SSE.
- [ ] UI Component to display logs (Monospace, auto-scroll).

## Implementation Steps

1. [ ] Create `LogBroadcaster` service in backend.
2. [ ] Hook `rich.console` or Python `logging` to broadcasting queue.
3. [ ] Create `GET /api/logs/stream` endpoint (SSE).
4. [ ] Create `terminal_log.html` component with EventSource connection.

## Files to Create/Modify

- `javinizer/web/services/log_broadcaster.py`
- `javinizer/web/templates/components/terminal_log.html`

## Test Criteria

- [ ] Triggering an action (e.g., scrape) shows logs immediately in the HUD.
