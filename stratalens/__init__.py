"""StrataLens descriptive stratified-comparison audit."""

from .analysis import analyze_rows
from .io import load_rows

__all__ = ["analyze_rows", "load_rows"]
__version__ = "0.1.0"
