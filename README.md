<<<<<<< HEAD
# Spring Task Board

This is a small Kanban task board for spring cleaning ideas and personal tasks. Flask handles the backend, SQLite stores the data, Jinja renders the pages, and a little JavaScript makes the board interactive.

## Installation
=======
﻿# Пролетна дъска

Приложението е едно Kanban табло с 10 идеи за пролетно почистване, цветни илюстрации и лични задачи. Flask + SQLite + Jinja2 сами се грижат за логиката.

## Инсталация
>>>>>>> b87e5fea71cf0c2459026bbed66920225ab85046

1. `cd taskboard`
2. `python -m pip install -r requirements.txt`

<<<<<<< HEAD
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
=======
## Стартиране

1. Работете от директорията `taskboard`.
2. `python app.py`
3. Посетете `http://localhost:5000` – Kanban колоните са на една линия, а таблото позволява хоризонтален скрол, така че картите да не се застъпват на тесни екрани.

Данните се запазват в `db.sqlite`. За отделни среди задайте `TASKBOARD_DB="/път/до/файл.sqlite"`.

## Характеристики

- 10 предложения за деклантеринг в решетка, с три реални цветни снимки и място да добавите свои задачи.
- Kanban таблото има четири колони (To Do, In Progress, In Review, Done) на една линия, всяка със собствен вертикален скрол, избор на статус (падащо меню) и drag & drop, така че задачи се преместват между колоните с пренос.
- Вход/регистрация създават профили и гарантират, че виждате само своите задачи; текущият потребител се показва в хедъра.
- Силно компактни задачи (ограничена височина) с inline редакция и AJAX `PATCH /api/tasks/<id>` за змяна на статус или заглавие.
- Отделният формуляр за редакция дава фин контрол над заглавието и статуса, а `main.js` премества картите между колоните без презареждане.

## Тестване

```
pytest
```

Тестовете (`tests/test_models.py`) ползват временна база, посочена чрез `TASKBOARD_DB`.
>>>>>>> b87e5fea71cf0c2459026bbed66920225ab85046
