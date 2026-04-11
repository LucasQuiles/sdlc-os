#!/usr/bin/env bash
# ABOUTME: Run unit tests for the duplicate detection skill
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/.."
python3 -m pytest tests/ -v 2>&1
