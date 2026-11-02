#!/usr/bin/env python3
"""Small deterministic check for the unsafe Kubernetes fixture used in Phase 2."""

import argparse
import sys
from pathlib import Path


RULES = {
    "hostNetwork: true": "host networking exposes the pod to the node network",
    "privileged: true": "privileged containers have excessive kernel access",
    "runAsUser: 0": "the container runs as root",
}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("manifest", type=Path)
    args = parser.parse_args()
    text = args.manifest.read_text()
    findings = [reason for marker, reason in RULES.items() if marker in text]
    if findings:
        print(f"Security check found {len(findings)} finding(s) in {args.manifest}:")
        for finding in findings:
            print(f"- {finding}")
        return 1
    print(f"Security check passed: {args.manifest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
