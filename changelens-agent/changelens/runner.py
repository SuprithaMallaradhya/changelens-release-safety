"""Safe subprocess execution with normalized outcomes."""

from __future__ import annotations

import shlex
import subprocess
import time
from pathlib import Path
from typing import List, Optional

from .models import ToolResult, ToolStatus


def run_command(
    name: str,
    args: List[str],
    cwd: Path,
    timeout_seconds: int = 120,
) -> ToolResult:
    """Run an argv command without a shell and preserve its outcome."""
    command = shlex.join(args)
    started = time.monotonic()
    try:
        completed = subprocess.run(
            args,
            cwd=str(cwd),
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
            check=False,
        )
        duration_ms = int((time.monotonic() - started) * 1000)
        status = ToolStatus.PASSED if completed.returncode == 0 else ToolStatus.FAILED
        return ToolResult(name, command, status, completed.returncode, duration_ms,
                          completed.stdout, completed.stderr)
    except FileNotFoundError as exc:
        return ToolResult(name, command, ToolStatus.UNAVAILABLE, None,
                          int((time.monotonic() - started) * 1000), "", str(exc))
    except subprocess.TimeoutExpired as exc:
        stdout = _as_text(exc.stdout)
        stderr = _as_text(exc.stderr)
        return ToolResult(name, command, ToolStatus.TIMED_OUT, None,
                          int((time.monotonic() - started) * 1000), stdout, stderr,
                          timed_out=True)


def _as_text(value: Optional[object]) -> str:
    if value is None:
        return ""
    return value.decode() if isinstance(value, bytes) else str(value)
