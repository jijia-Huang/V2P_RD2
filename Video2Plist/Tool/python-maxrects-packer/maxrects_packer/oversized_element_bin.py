"""OversizedElementBin for handling rectangles that exceed bin size."""

from typing import Any, List, Optional, TypeVar

from .abstract_bin import Bin
from .rectangle import IRectangle, Rectangle
from .types import IOption

T = TypeVar('T', bound=IRectangle)


class OversizedElementBin(Bin[T]):
    """Bin for handling rectangles that exceed maxWidth/maxHeight."""
    
    def __init__(self, *args: Any):
        """Create an OversizedElementBin.
        
        Can be called with:
        - OversizedElementBin(rect: T)
        - OversizedElementBin(width: float, height: float, data: Any)
        """
        super().__init__()
        
        if len(args) == 1:
            if not isinstance(args[0], (dict, object)):
                raise ValueError("OversizedElementBin: Wrong parameters")
            rect = args[0]
            self.rects = [rect]
            self.width = rect.width
            self.height = rect.height
            self.data = getattr(rect, 'data', None)
            if hasattr(rect, 'oversized'):
                rect.oversized = True
        else:
            self.width = args[0]
            self.height = args[1]
            self.data = args[2] if len(args) > 2 else None
            rect = Rectangle(self.width, self.height)
            rect.oversized = True
            rect.data = self.data
            self.rects = [rect]  # type: ignore
        
        self.free_rects = []
        self.max_width = self.width
        self.max_height = self.height
        self.options: IOption = {
            'smart': False,
            'pot': False,
            'square': False
        }
    
    def add(self, *args: Any) -> Optional[T]:
        """Cannot add to oversized bin."""
        return None
    
    def reset(self, deep_reset: bool = False) -> None:
        """Nothing to reset for oversized bin."""
        pass
    
    def repack(self) -> Optional[List[T]]:
        """Cannot repack oversized bin."""
        return None
    
    def clone(self) -> 'OversizedElementBin[T]':
        """Create a clone of this bin."""
        return OversizedElementBin[T](self.rects[0])

