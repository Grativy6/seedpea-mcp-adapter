"""Test package; make the in-tree foundation importable before installation."""
import sys
from pathlib import Path

_foundation = str(Path(__file__).parents[1] / "packages" / "foundation")
if _foundation not in sys.path:
    sys.path.insert(0, _foundation)
