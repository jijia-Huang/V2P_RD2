"""MaxRectsPacker main class for maxrects-packer."""

from typing import Any, Dict, List, Optional, TypeVar

from .abstract_bin import Bin, IBin
from .maxrects_bin import MaxRectsBin
from .oversized_element_bin import OversizedElementBin
from .rectangle import IRectangle, Rectangle
from .types import EDGE_MAX_VALUE, IOption, PackingLogic

T = TypeVar('T', bound=IRectangle)


class MaxRectsPacker:
    """MaxRectsPacker implements the Max Rectangle bin packing algorithm."""
    
    def __init__(
        self,
        width: float = EDGE_MAX_VALUE,
        height: float = EDGE_MAX_VALUE,
        padding: float = 0,
        options: Optional[IOption] = None
    ):
        """Create a MaxRectsPacker instance.
        
        Args:
            width: Width of the output atlas (default is 4096)
            height: Height of the output atlas (default is 4096)
            padding: Padding between glyphs/images (default is 0)
            options: Optional packing options
        """
        self.width = width
        self.height = height
        self.padding = padding
        self.bins: List[Bin[T]] = []
        self._current_bin_index: int = 0
        
        # Set default options
        self.options: IOption = {
            'smart': True,
            'pot': True,
            'square': False,
            'allowRotation': False,
            'tag': False,
            'exclusiveTag': True,
            'border': 0,
            'logic': PackingLogic.MAX_EDGE
        }
        if options:
            self.options.update(options)
    
    def add(self, *args: Any) -> T:
        """Add a rectangle to the packer.
        
        Can be called with:
        - add(rect: T) -> T
        - add(width: float, height: float, data: Any = None) -> T
        
        Returns:
            The added rectangle.
        """
        if len(args) == 1:
            if not isinstance(args[0], (dict, object)):
                raise ValueError("MaxRectsPacker.add(): Wrong parameters")
            rect = args[0]
            
            # Check if oversized
            fits = ((rect.width <= self.width and rect.height <= self.height) or
                   (self.options.get('allowRotation', False) and
                    rect.width <= self.height and rect.height <= self.width))
            
            if not fits:
                self.bins.append(OversizedElementBin[T](rect))
            else:
                added = None
                for bin in self.bins[self._current_bin_index:]:
                    result = bin.add(rect)
                    if result is not None:
                        added = bin
                        break
                
                if not added:
                    bin = MaxRectsBin[T](self.width, self.height, self.padding, self.options)
                    tag = None
                    if hasattr(rect, 'data') and rect.data and isinstance(rect.data, dict):
                        tag = rect.data.get('tag')
                    elif hasattr(rect, 'tag'):
                        tag = getattr(rect, 'tag', None)
                    if self.options.get('tag') and tag:
                        bin.tag = tag
                    bin.add(rect)
                    self.bins.append(bin)
            return rect  # type: ignore
        else:
            rect = Rectangle(args[0], args[1])
            if len(args) > 2:
                rect.data = args[2]
            
            # Check if oversized
            fits = ((rect.width <= self.width and rect.height <= self.height) or
                   (self.options.get('allowRotation', False) and
                    rect.width <= self.height and rect.height <= self.width))
            
            if not fits:
                self.bins.append(OversizedElementBin[T](rect))  # type: ignore
            else:
                added = None
                for bin in self.bins[self._current_bin_index:]:
                    result = bin.add(rect)  # type: ignore
                    if result is not None:
                        added = bin
                        break
                
                if not added:
                    bin = MaxRectsBin[T](self.width, self.height, self.padding, self.options)
                    if self.options.get('tag') and rect.data and isinstance(rect.data, dict):
                        bin.tag = rect.data.get('tag')
                    bin.add(rect)  # type: ignore
                    self.bins.append(bin)
            return rect  # type: ignore
    
    def add_array(self, rects: List[T]) -> None:
        """Add an array of rectangles to the packer.
        
        Args:
            rects: Array of rectangles to pack.
            
        Note:
            Objects with `hash` property will have more stable packing result.
        """
        normalized_rects: List[T] = []
        for rect in rects:
            if isinstance(rect, dict):
                width = float(rect.get('width', 0))
                height = float(rect.get('height', 0))
                data = rect.get('data')
                normalized = Rectangle(width, height)
                if data is not None:
                    normalized.data = data
                for key in ['x', 'y', 'rot', 'tag', 'hash']:
                    if key in rect:
                        setattr(normalized, key, rect[key])
                if 'allowRotation' in rect:
                    normalized.allow_rotation = rect['allowRotation']
                normalized_rects.append(normalized)  # type: ignore
            else:
                normalized_rects.append(rect)

        if not self.options.get('tag') or self.options.get('exclusiveTag'):
            # Old approach
            sorted_rects = self._sort(normalized_rects, self.options.get('logic', PackingLogic.MAX_EDGE))
            for rect in sorted_rects:
                self.add(rect)
        else:
            # Sort rects by tags first
            if len(normalized_rects) == 0:
                return
            
            def get_tag(r: Any) -> Any:
                if hasattr(r, 'data') and r.data and isinstance(r.data, dict):
                    return r.data.get('tag')
                elif hasattr(r, 'tag'):
                    return getattr(r, 'tag', None)
                return None
            
            rects_sorted = sorted(normalized_rects, key=lambda r: (
                0 if get_tag(r) is None else 1,
                get_tag(r) or ''
            ), reverse=True)
            
            current_tag = None
            current_idx = 0
            
            target_bin = None
            for bin in self.bins[self._current_bin_index:]:
                test_bin = bin.clone()
                for i in range(current_idx, len(rects_sorted)):
                    rect = rects_sorted[i]
                    tag = get_tag(rect)
                    
                    if i == current_idx:
                        current_tag = tag
                    
                    if tag != current_tag:
                        current_tag = tag
                        sorted_subset = self._sort(
                            rects_sorted[current_idx:i],
                            self.options.get('logic', PackingLogic.MAX_EDGE)
                        )
                        for r in sorted_subset:
                            bin.add(r)
                        current_idx = i
                        self.add_array(rects_sorted[i:])
                        target_bin = bin
                        break
                    
                    if tag is None:
                        sorted_subset = self._sort(
                            rects_sorted[i:],
                            self.options.get('logic', PackingLogic.MAX_EDGE)
                        )
                        for r in sorted_subset:
                            self.add(r)
                        current_idx = len(rects_sorted)
                        target_bin = bin
                        break
                    
                    if test_bin.add(rect) is None:
                        sorted_subset = self._sort(
                            rects_sorted[current_idx:i],
                            self.options.get('logic', PackingLogic.MAX_EDGE)
                        )
                        for r in sorted_subset:
                            bin.add(r)
                        current_idx = i
                        break
                else:
                    sorted_subset = self._sort(
                        rects_sorted[current_idx:],
                        self.options.get('logic', PackingLogic.MAX_EDGE)
                    )
                    for r in sorted_subset:
                        bin.add(r)
                    target_bin = bin
                    break
            
            if not target_bin:
                rect = rects_sorted[current_idx]
                bin = MaxRectsBin[T](self.width, self.height, self.padding, self.options)
                tag = get_tag(rect)
                if self.options.get('tag') and self.options.get('exclusiveTag') and tag:
                    bin.tag = tag
                self.bins.append(bin)
                bin.add(rect)
                current_idx += 1
                self.add_array(rects_sorted[current_idx:])
    
    def reset(self) -> None:
        """Reset entire packer to initial states, keep settings."""
        self.bins = []
        self._current_bin_index = 0
    
    def repack(self, quick: bool = True) -> None:
        """Repack all elements inside bins.
        
        Args:
            quick: If True, only repack dirty bins. If False, repack all.
        """
        if quick:
            unpack: List[T] = []
            for bin in self.bins:
                if bin.dirty:
                    up = bin.repack()
                    if up:
                        unpack.extend(up)
            if unpack:
                self.add_array(unpack)
            return
        
        if not self.dirty:
            return
        
        all_rects = self.rects
        self.reset()
        self.add_array(all_rects)
    
    def next(self) -> int:
        """Stop adding new element to the current bin and return a new bin.
        
        Note: After calling next(), all elements will no longer be added to previous bins.
        
        Returns:
            The current bin index.
        """
        self._current_bin_index = len(self.bins)
        return self._current_bin_index
    
    def load(self, bins: List[Dict[str, Any]]) -> None:
        """Load bins to the packer, overwrite exist bins.
        
        Args:
            bins: List of bin dictionaries to load.
        """
        for index, bin_data in enumerate(bins):
            if bin_data.get('maxWidth', 0) > self.width or bin_data.get('maxHeight', 0) > self.height:
                self.bins.append(OversizedElementBin(
                    bin_data.get('width', 0),
                    bin_data.get('height', 0),
                    {}
                ))
            else:
                new_bin = MaxRectsBin[T](
                    self.width,
                    self.height,
                    self.padding,
                    bin_data.get('options', {})
                )
                new_bin.free_rects = []
                for r in bin_data.get('freeRects', []):
                    new_bin.free_rects.append(Rectangle(
                        r.get('width', 0),
                        r.get('height', 0),
                        r.get('x', 0),
                        r.get('y', 0)
                    ))
                new_bin.width = bin_data.get('width', 0)
                new_bin.height = bin_data.get('height', 0)
                if bin_data.get('tag'):
                    new_bin.tag = bin_data.get('tag')
                if index < len(self.bins):
                    self.bins[index] = new_bin
                else:
                    self.bins.append(new_bin)
    
    def save(self) -> List[Dict[str, Any]]:
        """Output current bins to save.
        
        Returns:
            List of bin dictionaries that can be JSON serialized.
        """
        save_bins: List[Dict[str, Any]] = []
        for bin in self.bins:
            save_bin: Dict[str, Any] = {
                'width': bin.width,
                'height': bin.height,
                'maxWidth': bin.max_width,
                'maxHeight': bin.max_height,
                'freeRects': [],
                'rects': [],
                'options': bin.options
            }
            if bin.tag:
                save_bin['tag'] = bin.tag
            for r in bin.free_rects:
                save_bin['freeRects'].append({
                    'x': r.x,
                    'y': r.y,
                    'width': r.width,
                    'height': r.height
                })
            save_bins.append(save_bin)
        return save_bins
    
    def _get_dimension(self, rect: Any, name: str) -> float:
        """Safely get a numeric dimension from rectangle-like objects."""
        if hasattr(rect, name):
            value = getattr(rect, name)
            if isinstance(value, (int, float)):
                return float(value)
        if isinstance(rect, dict):
            value = rect.get(name, 0)
            if isinstance(value, (int, float)):
                return float(value)
        return float(getattr(rect, name, 0) if hasattr(rect, name) else 0)

    def _sort(self, rects: List[T], logic: PackingLogic = PackingLogic.MAX_EDGE) -> List[T]:
        """Sort rectangles based on longest edge or surface area.
        
        Args:
            rects: Array of rectangles to sort.
            logic: Sorting logic (default is MAX_EDGE).
            
        Returns:
            Sorted list of rectangles.
        """
        def sort_key(r: T) -> tuple[float, Any]:
            width = self._get_dimension(r, 'width')
            height = self._get_dimension(r, 'height')
            if logic == PackingLogic.MAX_EDGE:
                primary = max(width, height)
            else:  # MAX_AREA
                primary = width * height
            secondary = getattr(r, 'hash', '') if hasattr(r, 'hash') else ''
            if isinstance(r, dict):
                secondary = r.get('hash', secondary)
            return (primary, secondary)
        
        return sorted(rects, key=sort_key, reverse=True)
    
    @property
    def current_bin_index(self) -> int:
        """Return current functioning bin index.
        
        Prior to this index, bins won't accept any new elements.
        """
        return self._current_bin_index
    
    @property
    def dirty(self) -> bool:
        """Returns dirty status of all child bins."""
        return any(bin.dirty for bin in self.bins)
    
    @property
    def rects(self) -> List[T]:
        """Return all rectangles in this packer."""
        all_rects: List[T] = []
        for bin in self.bins:
            all_rects.extend(bin.rects)
        return all_rects

