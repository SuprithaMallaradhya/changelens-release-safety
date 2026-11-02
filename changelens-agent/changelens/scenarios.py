"""Scenario manifest loading and changed-file extraction."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List


@dataclass(frozen=True)
class Scenario:
    name: str
    category: str
    changed_files: List[str]
    setup: str
    expected_outcome: str
    expected_evidence: List[str]
    validation_command: str
    directory: Path


def load_manifest(path: Path) -> Dict[str, Scenario]:
    document = json.loads(path.read_text())
    return {
        item["name"]: Scenario(
            name=item["name"],
            category=item["category"],
            changed_files=list(item["changed_files"]),
            setup=item["setup"],
            expected_outcome=item["expected_outcome"],
            expected_evidence=list(item["expected_evidence"]),
            validation_command=item["validation_command"],
            directory=path.parent / item["name"],
        )
        for item in document["scenarios"]
    }


def extract_changed_files(patch: Path) -> List[str]:
    """Extract paths from git patch headers without applying the patch."""
    files: List[str] = []
    if not patch.exists():
        return files
    for line in patch.read_text().splitlines():
        match = re.match(r"diff --git a/(.+) b/(.+)$", line)
        if match:
            files.append(match.group(2))
    return files


def scenario_changed_files(scenario: Scenario) -> List[str]:
    patch_files = extract_changed_files(scenario.directory / "change.patch")
    return patch_files or scenario.changed_files
