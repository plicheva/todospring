# Spring Task Board

This is a small Kanban task board for spring cleaning ideas and personal tasks. Flask handles the backend, SQLite stores the data, Jinja renders the pages, and a little JavaScript makes the board interactive.

## Installation

1. `cd taskboard`
2. `python -m pip install -r requirements.txt`

If you are using the local dependency folder that already exists in this workspace, start commands should include `.vendor` on `PYTHONPATH`.

## Start

Work from the `taskboard` directory:

```powershell
$env:PYTHONPATH = (Get-Location).Path + ';' + (Join-Path (Get-Location) '.vendor')
python -B -m flask --app app run --host 127.0.0.1 --port 5000
```

Then open `http://127.0.0.1:5000`.

To stop the foreground server, press `Ctrl+C`. If the server was started in the background, find and stop it with:

```powershell
Get-CimInstance Win32_Process | Where-Object { $_.Name -match 'python' -and $_.CommandLine -like '*flask*--app*app*run*' } | Select-Object ProcessId,CommandLine
Stop-Process -Id <PID>
```

Data is stored in `db.sqlite`. To use another database file, set `TASKBOARD_DB` to an absolute path.

## Features

- Four Kanban columns: To Do, In Progress, In Review, and Done.
- Per-user accounts, so each user sees only their own tasks.
- Add, edit, delete, and move tasks between columns.
- Inline title editing and AJAX updates through `PATCH /api/tasks/<id>`.
- Pointer-based card movement with a normal form fallback for status changes.
- Local runtime logs in `logs/taskboard.log`.
- Authenticated log dashboard at `/logs` with request counts, latency, status codes, log levels, app actions, and recent entries.
- Daily status banner in the shared page header.

## Testing

```powershell
$env:PYTHONPATH = (Get-Location).Path + ';' + (Join-Path (Get-Location) '.vendor')
.vendor\bin\pytest.exe -q
```

The tests in `tests/test_models.py` use a temporary SQLite database through `TASKBOARD_DB`.
