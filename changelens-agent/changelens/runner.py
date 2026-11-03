"""Safe subprocess execution with normalized outcomes."""

from __future__ import annotations

import shlex
import subprocess
import tempfile
import time
from pathlib import Path
from typing import List

from .models import ToolResult, ToolStatus


MAX_CAPTURE_CHARS = 20000


def run_command(
    name: str,
    args: List[str],
    cwd: Path,
    timeout_seconds: int = 120,
    env: dict[str, str] | None = None,
) -> ToolResult:
    """Run an argv command without a shell and preserve its outcome."""
    command = shlex.join(args)
    started = time.monotonic()
    try:
        # Temporary files keep a noisy tool from growing Python's memory usage
        # without bound while retaining a useful prefix for the report.
        with tempfile.TemporaryFile() as stdout_file, tempfile.TemporaryFile() as stderr_file:
            process = subprocess.Popen(args, cwd=str(cwd), stdout=stdout_file, stderr=stderr_file,
                                       text=False, close_fds=True, env=env)
            timed_out = False
            try:
                process.wait(timeout=timeout_seconds)
            except subprocess.TimeoutExpired:
                timed_out = True
                process.kill()
                process.wait()
            stdout, stdout_truncated = _read_limited(stdout_file)
            stderr, stderr_truncated = _read_limited(stderr_file)
        duration_ms = int((time.monotonic() - started) * 1000)
        if timed_out:
            return ToolResult(name, command, ToolStatus.TIMED_OUT, None, duration_ms, stdout, stderr,
                              True, stdout_truncated, stderr_truncated)
        status = ToolStatus.PASSED if process.returncode == 0 else ToolStatus.FAILED
        return ToolResult(name, command, status, process.returncode, duration_ms, stdout, stderr,
                          False, stdout_truncated, stderr_truncated)
    except FileNotFoundError as exc:
        return ToolResult(name, command, ToolStatus.UNAVAILABLE, None,
                          int((time.monotonic() - started) * 1000), "", str(exc))
    except OSError as exc:
        return ToolResult(name, command, ToolStatus.UNAVAILABLE, None,
                          int((time.monotonic() - started) * 1000), "", str(exc))


def _read_limited(stream) -> tuple[str, bool]:
    stream.seek(0)
    data = stream.read(MAX_CAPTURE_CHARS * 4 + 1)
    truncated = len(data) > MAX_CAPTURE_CHARS * 4
    return data[:MAX_CAPTURE_CHARS * 4].decode(errors="replace")[:MAX_CAPTURE_CHARS], truncated
