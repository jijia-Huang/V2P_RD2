"""Type definitions and constants for maxrects-packer."""

from enum import IntEnum
from typing import Optional, TypedDict

# Constants
EDGE_MAX_VALUE: int = 4096
EDGE_MIN_VALUE: int = 128


class PackingLogic(IntEnum):
    """Packing logic options for selecting free spaces."""
    MAX_AREA = 0
    MAX_EDGE = 1
    FILL_WIDTH = 2


class IOption(TypedDict, total=False):
    """Options for MaxRect Packer.
    
    Attributes:
        smart: Smart sizing packer (default is True)
        pot: Use power of 2 sizing (default is True)
        square: Use square size (default is False)
        allowRotation: Allow rotation packing (default is False)
        tag: Allow auto grouping based on rect.tag (default is False)
        exclusiveTag: Tagged rects will have dependent bin, if set to False,
            packer will try to put tag rects into the same bin (default is True)
        border: Atlas edge spacing (default is 0)
        logic: MAX_AREA or MAX_EDGE based sorting logic (default is MAX_EDGE)
    """
    smart: bool
    pot: bool
    square: bool
    allowRotation: bool
    tag: bool
    exclusiveTag: bool
    border: int
    logic: PackingLogic

