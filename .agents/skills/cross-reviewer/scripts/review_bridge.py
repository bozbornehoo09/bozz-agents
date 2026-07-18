#!/usr/bin/env python3
"""Run the canonical bridge helper bundled with cross-review-requester."""

from pathlib import Path
import runpy


HELPER = Path(__file__).resolve().parents[2] / "cross-review-requester" / "scripts" / "review_bridge.py"
runpy.run_path(str(HELPER), run_name="__main__")
