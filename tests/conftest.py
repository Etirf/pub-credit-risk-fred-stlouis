# tests/conftest.py
"""
Ensure project root is importable when running pytest directly.

I avoid using `pip install -e .` (editable mode) because it writes a .pth file
pointing to the project root inside site-packages, which can make imports
ambiguous if multiple editable projects are active.

This file ensures that the project root is importable when running pytest
without requiring an editable install.
"""

import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))
