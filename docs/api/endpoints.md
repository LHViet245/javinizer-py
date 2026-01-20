# API Documentation

## Filesystem API

Base URL: `/api/fs`

### GET /list

List contents of a directory or drive list.

- **Query Params:**
  - `path` (optional): Path to list. If omitted, returns available drives.
- **Response:** `List[FileItem]`

    ```json
    [
        {
            "name": "Movies",
            "path": "D:\\Movies",
            "type": "directory",
            "size": null,
            "has_children": true
        },
        ...
    ]
    ```

### GET /tree_fragment

HTMX-ready HTML fragment for a specific directory tree node.

- **Query Params:**
  - `path`: Path to expand.
- **Response:** HTML content (list of `div` elements).

### GET /grid_fragment

HTMX-ready HTML fragment for a folder's grid view.

- **Query Params:**
  - `path`: Path to list in grid.
- **Response:** HTML content (list of `.glass-card` elements).

### GET /inspector_fragment

HTMX-ready HTML fragment for the metadata inspector of a file.

- **Query Params:**
  - `path`: Path to the file.
- **Response:** HTML content (Inspector panel UI).

## Metadata API

### POST /api/metadata/apply

Apply manual metadata edits to a file.

- **Form Template:** `path`, `movie_id`, `title`, `release_date`.
- **Response:** HTML fragment (Status message).

## Logging API

### GET /api/logs/stream

Real-time log stream using Server-Sent Events (SSE).

- **Format:** `text/event-stream`
- **Response:** `data: [Level]: [Message]\n\n`

## Operations API

Base URL: `/api/ops`

### POST /sort

Trigger a sort operation (preview or execute).

- **Body:** `SortRequest`

    ```json
    {
        "path": "D:\\Downloads\\video.mp4",
        "dest": "D:\\Jav",
        "recursive": false,
        "dry_run": true
    }
    ```

- **Response:**

    ```json
    {
        "job_id": "uuid-string",
        "status": "pending"
    }
    ```

### POST /batch/sort

Trigger a batch sort operation for multiple paths.

- **Body:** `BatchRequest`

    ```json
    {
        "paths": ["D:\\Movies\\Video1.mp4", "D:\\Movies\\Video2.mp4"],
        "dest": "D:\\Sorted",
        "recursive": false,
        "dry_run": false
    }
    ```

- **Response:** Same as `/sort`.

### POST /batch/update

Trigger a batch metadata update for multiple paths.

- **Body:** `BatchRequest` (same format as `/batch/sort`).
- **Response:** Same as `/sort`.

### GET /job/{job_id}

Get the status of a background job.

- **Response:** `JobStatus`

    ```json
    {
        "id": "uuid-string",
        "type": "sort_preview",
        "status": "running",
        "progress": 45,
        "message": "Processing file...",
        "result": null
    }
    ```

## Settings API

Base URL: `/api/settings`

### GET /

Get current configuration.

- **Response:** JSON object of full `jvSettings.json`.

### POST /

Update configuration.

- **Body:** JSON object (partial update possible).
- **Response:**

    ```json
    {
        "status": "success",
        "settings": {...}
    }
    ```
