"""Disposable, isolated preview data for browser integration tests."""

import os
import sys
import tempfile
from pathlib import Path

import uvicorn

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

if __name__ == "__main__":
    with tempfile.TemporaryDirectory(prefix="pinginoo-browser-") as directory:
        os.environ["PINGINOO_DEMO"] = "1"
        os.environ["PINGINOO_DATA_DIR"] = directory
        uvicorn.run("webapp:app", host="0.0.0.0", port=8091, log_level="warning")
