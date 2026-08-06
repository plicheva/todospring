import re
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple


LOG_LINE_PATTERN = re.compile(
    r"^(?P<timestamp>\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d{3}) "
    r"(?P<level>[A-Z]+) \[(?P<logger>[^\]]+)\] (?P<message>.*)$"
)
REQUEST_PATTERN = re.compile(
    r"^(?P<method>[A-Z]+) (?P<path>\S+) -> (?P<status>\d{3}) "
    r"in (?P<duration>\d+(?:\.\d+)?) ms from (?P<remote_addr>\S+) "
    r"user_id=(?P<user_id>\S+)"
    r"(?: request_id=(?P<request_id>\S+))?"
    r"(?: endpoint=(?P<endpoint>\S+))?"
    r"(?: user_agent=(?P<user_agent>.*))?$"
)
ANSI_PATTERN = re.compile(r"\x1b\[[0-9;]*m")

ACTION_PREFIXES = {
    "Task created": "Task created",
    "Task updated": "Task updated",
    "Task deleted": "Task deleted",
    "Task API updated": "Task updated via API",
    "User registered": "User registered",
    "User logged in": "User logged in",
    "User logged out": "User logged out",
    "Login failed": "Login failed",
    "Registration failed": "Registration failed",
}


def _log_files(log_dir: Path) -> List[Path]:
    if not log_dir.exists():
        return []
    return sorted(
        (path for path in log_dir.glob("taskboard.log*") if path.is_file()),
        key=lambda path: (path.stat().st_mtime, path.name),
    )


def _read_lines(files: Iterable[Path], limit: int) -> List[Tuple[str, str]]:
    rows: List[Tuple[str, str]] = []
    for path in files:
        try:
            with path.open("r", encoding="utf-8", errors="replace") as handle:
                rows.extend((path.name, line.rstrip()) for line in handle if line.strip())
        except OSError:
            continue
    return rows[-limit:]


def _parse_timestamp(value: str) -> Optional[datetime]:
    try:
        return datetime.strptime(value, "%Y-%m-%d %H:%M:%S,%f")
    except ValueError:
        return None


def _classify_action(message: str) -> Optional[str]:
    for prefix, label in ACTION_PREFIXES.items():
        if message.startswith(prefix):
            return label
    return None


def _status_family(status: int) -> str:
    return f"{status // 100}xx"


def _pct(value: int, total: int) -> float:
    return round((value / total) * 100, 1) if total else 0


def _bar_pct(value: int, maximum: int) -> int:
    if not maximum:
        return 0
    return max(6, round((value / maximum) * 100))


def _parse_entry(source: str, raw_line: str) -> Dict:
    clean_line = ANSI_PATTERN.sub("", raw_line)
    match = LOG_LINE_PATTERN.match(clean_line)
    if not match:
        return {
            "source": source,
            "raw": clean_line,
            "timestamp": "",
            "time": None,
            "time_label": "-",
            "level": "UNKNOWN",
            "logger": "-",
            "message": clean_line,
            "request": None,
            "action": None,
        }

    timestamp = match.group("timestamp")
    message = match.group("message")
    parsed_time = _parse_timestamp(timestamp)
    request_match = REQUEST_PATTERN.match(message)
    request_data = None
    if request_match:
        status = int(request_match.group("status"))
        request_data = {
            "method": request_match.group("method"),
            "path": request_match.group("path"),
            "status": status,
            "duration": float(request_match.group("duration")),
            "remote_addr": request_match.group("remote_addr"),
            "user_id": request_match.group("user_id"),
            "request_id": request_match.group("request_id") or "-",
            "endpoint": request_match.group("endpoint") or "-",
            "user_agent": request_match.group("user_agent") or "-",
            "family": _status_family(status),
        }

    return {
        "source": source,
        "raw": clean_line,
        "timestamp": timestamp,
        "time": parsed_time,
        "time_label": parsed_time.strftime("%Y-%m-%d %H:%M:%S") if parsed_time else timestamp,
        "level": match.group("level"),
        "logger": match.group("logger"),
        "message": message,
        "request": request_data,
        "action": _classify_action(message),
    }


def _load_entries(log_dir: Path, line_limit: int) -> Tuple[List[Path], List[Dict]]:
    files = _log_files(log_dir)
    entries = [_parse_entry(source, line) for source, line in _read_lines(files, line_limit)]
    return files, entries


def _normal_filters(filters: Optional[Dict[str, str]]) -> Dict[str, str]:
    filters = filters or {}
    return {
        "level": filters.get("level", "").upper().strip(),
        "q": filters.get("q", "").strip().lower(),
    }


def _matches_filters(entry: Dict, filters: Dict[str, str]) -> bool:
    level = filters.get("level", "")
    query = filters.get("q", "")
    if level and entry["level"] != level:
        return False
    if not query:
        return True

    request_data = entry.get("request") or {}
    haystack = " ".join(
        str(value)
        for value in (
            entry.get("source", ""),
            entry.get("level", ""),
            entry.get("logger", ""),
            entry.get("message", ""),
            request_data.get("method", ""),
            request_data.get("path", ""),
            request_data.get("status", ""),
            request_data.get("request_id", ""),
            request_data.get("endpoint", ""),
        )
    ).lower()
    return query in haystack


def build_daily_status(log_dir: Path, line_limit: int = 1200) -> Dict:
    today = datetime.now().date()
    files, entries = _load_entries(log_dir, line_limit)
    today_entries = [
        entry for entry in entries if entry["time"] and entry["time"].date() == today
    ]
    today_requests = [entry for entry in today_entries if entry["request"]]
    health_entries = [entry for entry in today_entries if entry["logger"] == "app"]
    level_counts = Counter(entry["level"] for entry in health_entries)
    durations = [entry["request"]["duration"] for entry in today_requests]
    avg_latency = round(sum(durations) / len(durations), 1) if durations else 0
    error_count = level_counts.get("ERROR", 0) + level_counts.get("CRITICAL", 0)
    warning_count = level_counts.get("WARNING", 0)

    if error_count:
        tone = "bad"
        message = f"Today needs attention: {error_count} errors found"
    elif avg_latency >= 1000:
        tone = "warn"
        message = f"Today load is slow: {avg_latency} ms average response time"
    elif warning_count >= 10:
        tone = "warn"
        message = f"Today load is fine, but {warning_count} warnings need a look"
    elif today_requests:
        tone = "ok"
        message = "Today load is fine, no issues"
    else:
        tone = "quiet"
        message = "Today is quiet, no requests logged yet"

    return {
        "date": today.isoformat(),
        "message": message,
        "tone": tone,
        "request_count": len(today_requests),
        "avg_latency": avg_latency,
        "warning_count": warning_count,
        "error_count": error_count,
        "file_count": len(files),
    }


def build_log_dashboard(
    log_dir: Path,
    line_limit: int = 1200,
    filters: Optional[Dict[str, str]] = None,
) -> Dict:
    files, entries = _load_entries(log_dir, line_limit)
    filters = _normal_filters(filters)
    filtered_entries = [
        entry for entry in entries if _matches_filters(entry, filters)
    ]
    requests = [entry for entry in filtered_entries if entry["request"]]
    actions = [entry for entry in filtered_entries if entry["action"]]
    problem_entries = [
        entry
        for entry in filtered_entries
        if entry["level"] in {"WARNING", "ERROR", "CRITICAL"}
        or (entry["request"] and entry["request"]["status"] >= 400)
    ]

    level_counts = Counter(entry["level"] for entry in filtered_entries)
    status_counts = Counter(entry["request"]["status"] for entry in requests)
    path_counts = Counter(entry["request"]["path"] for entry in requests)
    action_counts = Counter(entry["action"] for entry in actions)
    durations = [entry["request"]["duration"] for entry in requests]

    slowest_request = max(
        requests,
        key=lambda entry: entry["request"]["duration"],
        default=None,
    )
    latest_entry = filtered_entries[-1] if filtered_entries else None

    timeline_counter = Counter(
        entry["time"].strftime("%H:%M")
        for entry in requests
        if entry["time"] is not None
    )
    timeline_labels = list(timeline_counter.keys())[-14:]
    max_timeline_count = max(timeline_counter.values(), default=0)
    timeline = [
        {
            "label": label,
            "count": timeline_counter[label],
            "bar_pct": _bar_pct(timeline_counter[label], max_timeline_count),
        }
        for label in timeline_labels
    ]

    max_path_count = max(path_counts.values(), default=0)
    max_status_count = max(status_counts.values(), default=0)

    return {
        "log_dir": str(log_dir),
        "filters": filters,
        "entries": list(reversed(filtered_entries[-80:])),
        "problem_entries": list(reversed(problem_entries[-12:])),
        "timeline": timeline,
        "top_paths": [
            {"path": path, "count": count, "bar_pct": _bar_pct(count, max_path_count)}
            for path, count in path_counts.most_common(8)
        ],
        "levels": [
            {"label": level, "count": count, "pct": _pct(count, len(filtered_entries))}
            for level, count in level_counts.most_common()
        ],
        "statuses": [
            {
                "code": code,
                "family": _status_family(code),
                "count": count,
                "bar_pct": _bar_pct(count, max_status_count),
            }
            for code, count in status_counts.most_common()
        ],
        "actions_summary": [
            {"label": action, "count": count}
            for action, count in action_counts.most_common()
        ],
        "summary": {
            "total_entries": len(filtered_entries),
            "unfiltered_total_entries": len(entries),
            "request_count": len(requests),
            "warning_count": level_counts.get("WARNING", 0),
            "error_count": level_counts.get("ERROR", 0) + level_counts.get("CRITICAL", 0),
            "avg_latency": round(sum(durations) / len(durations), 1) if durations else 0,
            "slowest_request": slowest_request,
            "latest_time": latest_entry["time_label"] if latest_entry else "-",
            "file_count": len(files),
        },
    }
