"""Rectangle geometry class for maxrects-packer."""

from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class IRectangle(Protocol):
    """Interface for rectangle objects.
    
    Any object with width, height, x, y properties can be used as a rectangle.
    """
    width: float
    height: float
    x: float
    y: float
    
    def __getitem__(self, key: str) -> Any: ...
    def __setitem__(self, key: str, value: Any) -> None: ...


class Rectangle:
    """Rectangle class with geometry operations and dirty state tracking."""
    
    def __init__(
        self,
        width: float = 0,
        height: float = 0,
        x: float = 0,
        y: float = 0,
        rot: bool = False,
        allow_rotation: bool | None = None
    ):
        """Create a rectangle instance.
        
        Args:
            width: Width of the rectangle (default is 0)
            height: Height of the rectangle (default is 0)
            x: X position of the rectangle (default is 0)
            y: Y position of the rectangle (default is 0)
            rot: Rotation flag (default is False)
            allow_rotation: Allow rotation flag (default is None)
        """
        self._width = width
        self._height = height
        self._x = x
        self._y = y
        self._data: Any = {}
        self._rot = rot
        self._allow_rotation = allow_rotation
        self.oversized: bool = False
        self._dirty: int = 0
    
    @property
    def width(self) -> float:
        """Get the width of the rectangle."""
        return self._width
    
    @width.setter
    def width(self, value: float) -> None:
        """Set the width of the rectangle."""
        if value != self._width:
            self._width = value
            self._dirty += 1
    
    @property
    def height(self) -> float:
        """Get the height of the rectangle."""
        return self._height
    
    @height.setter
    def height(self, value: float) -> None:
        """Set the height of the rectangle."""
        if value != self._height:
            self._height = value
            self._dirty += 1
    
    @property
    def x(self) -> float:
        """Get the x position of the rectangle."""
        return self._x
    
    @x.setter
    def x(self, value: float) -> None:
        """Set the x position of the rectangle."""
        if value != self._x:
            self._x = value
            self._dirty += 1
    
    @property
    def y(self) -> float:
        """Get the y position of the rectangle."""
        return self._y
    
    @y.setter
    def y(self, value: float) -> None:
        """Set the y position of the rectangle."""
        if value != self._y:
            self._y = value
            self._dirty += 1
    
    @property
    def rot(self) -> bool:
        """Get the rotation flag."""
        return self._rot
    
    @rot.setter
    def rot(self, value: bool) -> None:
        """Set the rotation flag.
        
        Note: After rot is set, width/height of this rectangle is swapped.
        """
        if self._allow_rotation is False:
            return
        
        if self._rot != value:
            tmp = self.width
            self.width = self.height
            self.height = tmp
            self._rot = value
            self._dirty += 1
    
    @property
    def allow_rotation(self) -> bool | None:
        """Get the allow rotation flag."""
        return self._allow_rotation
    
    @allow_rotation.setter
    def allow_rotation(self, value: bool | None) -> None:
        """Set the allow rotation flag."""
        if self._allow_rotation != value:
            self._allow_rotation = value
            self._dirty += 1
    
    @property
    def data(self) -> Any:
        """Get the data associated with this rectangle."""
        return self._data
    
    @data.setter
    def data(self, value: Any) -> None:
        """Set the data associated with this rectangle."""
        if value is None or value == self._data:
            return
        self._data = value
        # Extract allowRotation settings
        if isinstance(value, dict) and "allowRotation" in value:
            self._allow_rotation = value["allowRotation"]
        self._dirty += 1
    
    @property
    def dirty(self) -> bool:
        """Check if the rectangle is dirty (has been modified)."""
        return self._dirty > 0
    
    def set_dirty(self, value: bool = True) -> None:
        """Set the dirty flag."""
        self._dirty = self._dirty + 1 if value else 0
    
    def area(self) -> float:
        """Get the area (width * height) of the rectangle.
        
        Returns:
            The area of the rectangle.
        """
        return self.width * self.height
    
    def collide(self, rect: IRectangle) -> bool:
        """Test if the given rectangle collides with this rectangle.
        
        Args:
            rect: Rectangle to test collision with.
            
        Returns:
            True if rectangles collide.
        """
        return (
            rect.x < self.x + self.width and
            rect.x + getattr(rect, 'width', 0) > self.x and
            rect.y < self.y + self.height and
            rect.y + getattr(rect, 'height', 0) > self.y
        )
    
    def contain(self, rect: IRectangle) -> bool:
        """Test if this rectangle contains the given rectangle.
        
        Args:
            rect: Rectangle to test containment.
            
        Returns:
            True if this rectangle contains the given rectangle.
        """
        return (
            rect.x >= self.x and
            rect.y >= self.y and
            rect.x + getattr(rect, 'width', 0) <= self.x + self.width and
            rect.y + getattr(rect, 'height', 0) <= self.y + self.height
        )
    
    @staticmethod
    def collide_static(first: IRectangle, second: IRectangle) -> bool:
        """Test if two given rectangles collide each other.
        
        Args:
            first: First rectangle.
            second: Second rectangle.
            
        Returns:
            True if rectangles collide.
        """
        if hasattr(first, 'collide'):
            return first.collide(second)  # type: ignore
        # Fallback calculation
        return (
            second.x < first.x + getattr(first, 'width', 0) and
            second.x + getattr(second, 'width', 0) > first.x and
            second.y < first.y + getattr(first, 'height', 0) and
            second.y + getattr(second, 'height', 0) > first.y
        )
    
    @staticmethod
    def contain_static(first: IRectangle, second: IRectangle) -> bool:
        """Test if the first rectangle contains the second one.
        
        Args:
            first: First rectangle.
            second: Second rectangle.
            
        Returns:
            True if first rectangle contains the second.
        """
        if hasattr(first, 'contain'):
            return first.contain(second)  # type: ignore
        # Fallback calculation
        return (
            second.x >= first.x and
            second.y >= first.y and
            second.x + getattr(second, 'width', 0) <= first.x + getattr(first, 'width', 0) and
            second.y + getattr(second, 'height', 0) <= first.y + getattr(first, 'height', 0)
        )

