"""Abstract base class for bin implementations."""

from abc import ABC, abstractmethod
from typing import Any, Generic, List, Optional, TypeVar

from .rectangle import IRectangle
from .types import IOption

T = TypeVar('T', bound=IRectangle)


class IBin:
    """Interface for bin objects."""
    width: float
    height: float
    max_width: float
    max_height: float
    free_rects: List[IRectangle]
    rects: List[IRectangle]
    options: IOption


class Bin(ABC, Generic[T]):
    """Abstract base class for bin implementations."""
    
    def __init__(self):
        """Initialize a bin."""
        self.width: float = 0
        self.height: float = 0
        self.max_width: float = 0
        self.max_height: float = 0
        self.free_rects: List[IRectangle] = []
        self.rects: List[T] = []
        self.options: IOption = {}
        self.data: Any = None
        self.tag: Optional[str] = None
        self._dirty: int = 0
    
    @property
    def dirty(self) -> bool:
        """Check if the bin is dirty (has been modified)."""
        return self._dirty > 0 or any(
            rect.dirty if hasattr(rect, 'dirty') else False
            for rect in self.rects
        )
    
    def set_dirty(self, value: bool = True) -> None:
        """Set the dirty flag.
        
        Args:
            value: True to mark as dirty, False to clear.
        """
        if value:
            self._dirty += 1
        else:
            self._dirty = 0
            for rect in self.rects:
                if hasattr(rect, 'set_dirty'):
                    rect.set_dirty(False)
    
    @abstractmethod
    def add(self, *args: Any) -> Optional[T]:
        """Add a rectangle to the bin.
        
        Can be called with:
        - add(rect: T) -> Optional[T]
        - add(width: float, height: float, data: Any = None) -> Optional[T]
        """
        pass
    
    @abstractmethod
    def reset(self, deep_reset: bool = False) -> None:
        """Reset the bin to initial state.
        
        Args:
            deep_reset: If True, also reset data and tag.
        """
        pass
    
    @abstractmethod
    def repack(self) -> Optional[List[T]]:
        """Repack all rectangles in the bin.
        
        Returns:
            List of unpacked rectangles, or None if all fit.
        """
        pass
    
    @abstractmethod
    def clone(self) -> 'Bin[T]':
        """Create a clone of this bin.
        
        Returns:
            A new bin with the same state.
        """
        pass

