"""Safe extraction of committed pull-request candidates."""

from __future__ import annotations

import os
import shutil
import subprocess
import tarfile
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional


class DiffAnalysisError(RuntimeError):
    """Raised when a base/head diff cannot be analyzed safely."""


@dataclass(frozen=True)
class ChangedFile:
    status: str
    path: str
    old_path: Optional[str] = None


@dataclass(frozen=True)
class GitDiff:
    base_sha: str
    head_sha: str
    merge_base: str
    files: List[ChangedFile]
    insertions: int
    deletions: int

    @property
    def paths(self) -> List[str]:
        return [item.path for item in self.files if item.status != "D"]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "base_sha": self.base_sha,
            "head_sha": self.head_sha,
            "merge_base": self.merge_base,
            "files": [
                {"status": item.status, "path": item.path, "old_path": item.old_path}
                for item in self.files
            ],
            "file_count": len(self.files),
            "insertions": self.insertions,
            "deletions": self.deletions,
        }


def _git(root: Path, args: List[str], timeout: int = 30) -> str:
    try:
        result = subprocess.run(["git", *args], cwd=root, capture_output=True, text=True,
                                check=False, timeout=timeout)
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise DiffAnalysisError(f"git command unavailable or timed out: git {' '.join(args)}") from exc
    if result.returncode != 0:
        message = result.stderr.strip() or result.stdout.strip() or "unknown git error"
        raise DiffAnalysisError(f"git {' '.join(args)} failed: {message}")
    return result.stdout


def resolve_ref(root: Path, ref: str) -> str:
    if not ref or ref.startswith("-"):
        raise DiffAnalysisError("git ref must be non-empty and cannot start with '-'")
    return _git(root, ["rev-parse", "--verify", f"{ref}^{{commit}}"]).strip()


def extract_diff(root: Path, base_ref: str, head_ref: str) -> GitDiff:
    base_sha = resolve_ref(root, base_ref)
    head_sha = resolve_ref(root, head_ref)
    merge_base = _git(root, ["merge-base", base_sha, head_sha]).strip()
    raw = _git(root, ["diff", "--name-status", "-z", "--find-renames", "--find-copies",
                      "--no-ext-diff", base_sha, head_sha])
    files = _parse_name_status(raw)
    stat = _git(root, ["diff", "--numstat", "--no-ext-diff", base_sha, head_sha])
    insertions, deletions = _parse_numstat(stat)
    return GitDiff(base_sha, head_sha, merge_base, files, insertions, deletions)


def _parse_name_status(raw: str) -> List[ChangedFile]:
    values = raw.split("\0")
    files: List[ChangedFile] = []
    index = 0
    while index < len(values) and values[index]:
        status = values[index]
        index += 1
        if status.startswith(("R", "C")):
            if index >= len(values):
                raise DiffAnalysisError("malformed rename/copy diff output")
            old_path = values[index]
            index += 1
            if index >= len(values):
                raise DiffAnalysisError("malformed rename/copy diff output")
            new_path = values[index]
            index += 1
            files.append(ChangedFile(status[0], _safe_relative_path(new_path), _safe_relative_path(old_path)))
        else:
            if index >= len(values):
                raise DiffAnalysisError("malformed git diff output")
            files.append(ChangedFile(status[0], _safe_relative_path(values[index])))
            index += 1
    return files


def _safe_relative_path(value: str) -> str:
    path = Path(value)
    if not value or path.is_absolute() or ".." in path.parts:
        raise DiffAnalysisError(f"unsafe path in git diff: {value!r}")
    return path.as_posix()


def _parse_numstat(output: str) -> tuple[int, int]:
    insertions = deletions = 0
    for line in output.splitlines():
        parts = line.split("\t")
        if len(parts) < 2:
            continue
        try:
            if parts[0] != "-":
                insertions += int(parts[0])
            if parts[1] != "-":
                deletions += int(parts[1])
        except ValueError:
            continue
    return insertions, deletions


def create_candidate_workspace(root: Path, head_sha: str) -> tuple[Path, tempfile.TemporaryDirectory]:
    """Export a committed head into a temporary directory without touching the worktree."""
    temporary = tempfile.TemporaryDirectory(prefix="changelens-candidate-")
    workspace = Path(temporary.name)
    archive = workspace / "candidate.tar"
    try:
        subprocess.run(["git", "archive", "--format=tar", "--output", str(archive), head_sha],
                       cwd=root, check=True, capture_output=True, text=True, timeout=60)
        with tarfile.open(archive) as tar:
            _extract_safe(tar, workspace / "source")
        archive.unlink(missing_ok=True)
        return workspace / "source", temporary
    except Exception:
        temporary.cleanup()
        raise


def _extract_safe(archive: tarfile.TarFile, destination: Path) -> None:
    destination.mkdir(parents=True, exist_ok=True)
    destination_root = destination.resolve()
    for member in archive.getmembers():
        target = (destination / member.name).resolve()
        if os.path.commonpath([str(destination_root), str(target)]) != str(destination_root):
            raise DiffAnalysisError(f"archive path escapes candidate workspace: {member.name!r}")
        if member.issym() or member.islnk():
            raise DiffAnalysisError(f"links are not allowed in candidate archive: {member.name!r}")
    archive.extractall(destination)


def cleanup_workspace(temporary: tempfile.TemporaryDirectory) -> bool:
    try:
        temporary.cleanup()
        return True
    except OSError:
        return False
