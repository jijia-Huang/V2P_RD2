"""MaxRects Packer - A Python implementation of max rectangle 2D bin packing algorithm."""

from .packer import MaxRectsPacker
from .rectangle import IRectangle, Rectangle
from .types import EDGE_MAX_VALUE, EDGE_MIN_VALUE, IOption, PackingLogic

__all__ = [
    'MaxRectsPacker',
    'Rectangle',
    'IRectangle',
    'PackingLogic',
    'IOption',
    'EDGE_MAX_VALUE',
    'EDGE_MIN_VALUE',
]

# Re-export for backward compatibility
PACKING_LOGIC = PackingLogic

