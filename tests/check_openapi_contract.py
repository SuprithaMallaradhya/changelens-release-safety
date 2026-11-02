#!/usr/bin/env python3
"""Check the live Order API has the required paths and response fields."""

import argparse
import json
import sys
import urllib.request
from pathlib import Path


def load_json(url: str):
    with urllib.request.urlopen(url, timeout=5) as response:
        return json.load(response)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", default="http://localhost:8080")
    args = parser.parse_args()
    contract = json.loads((Path(__file__).parent / "contracts/order-response.json").read_text())
    document = load_json(args.base_url.rstrip("/") + "/v3/api-docs")
    required_paths = {"/orders", "/orders/{id}", "/orders/{id}/reserve"}
    missing_paths = sorted(required_paths - set(document.get("paths", {})))
    schema = document.get("components", {}).get("schemas", {}).get("Response", {})
    missing_fields = sorted(set(contract["required"]) - set(schema.get("properties", {})))
    if missing_paths or missing_fields:
        print(json.dumps({"missing_paths": missing_paths, "missing_fields": missing_fields}, indent=2))
        return 1
    print("API contract passed: required paths and response fields are present")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"API contract check failed: {exc}", file=sys.stderr)
        raise SystemExit(2)
