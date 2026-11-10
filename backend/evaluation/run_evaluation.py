"""Compatibility entry point for the CV/JD ranking evaluation."""

import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_DIR / "scripts"))

from evaluate_matching import main


if __name__ == "__main__":
    raise SystemExit(main())
