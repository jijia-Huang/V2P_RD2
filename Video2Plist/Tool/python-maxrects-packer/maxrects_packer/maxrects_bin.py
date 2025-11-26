"""MaxRectsBin implementation for maxrects-packer."""

import math
from typing import Any, List, Optional, TypeVar

from .abstract_bin import Bin
from .rectangle import IRectangle, Rectangle
from .types import EDGE_MAX_VALUE, IOption, PackingLogic

T = TypeVar('T', bound=IRectangle)


class MaxRectsBin(Bin[T]):
    """MaxRectsBin implements the Max Rectangle algorithm for bin packing."""
    
    def __init__(
        self,
        max_width: float = EDGE_MAX_VALUE,
        max_height: float = EDGE_MAX_VALUE,
        padding: float = 0,
        options: Optional[IOption] = None
    ):
        """Create a MaxRectsBin instance.
        
        Args:
            max_width: Maximum width of the bin (default is 4096)
            max_height: Maximum height of the bin (default is 4096)
            padding: Padding between rectangles (default is 0)
            options: Packing options
        """
        super().__init__()
        self.max_width = max_width
        self.max_height = max_height
        self.padding = padding
        
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
        
        self.width = 0 if self.options.get('smart', True) else max_width
        self.height = 0 if self.options.get('smart', True) else max_height
        self.border = self.options.get('border', 0) or 0
        
        # Initialize free rectangles
        self.free_rects: List[Rectangle] = [
            Rectangle(
                self.max_width + self.padding - self.border * 2,
                self.max_height + self.padding - self.border * 2,
                self.border,
                self.border
            )
        ]
        self.stage = Rectangle(self.width, self.height)
        self.vertical_expand: bool = False
    
    def add(self, *args: Any) -> Optional[T]:
        """Add a rectangle to the bin.
        
        Can be called with:
        - add(rect: T) -> Optional[T]
        - add(width: float, height: float, data: Any = None) -> Optional[T]
        
        Returns:
            The placed rectangle, or None if it couldn't be placed.
        """
        if len(args) == 1:
            if not isinstance(args[0], (dict, object)):
                raise ValueError("MaxRectsBin.add(): Wrong parameters")
            rect = args[0]
            # Check if rect.tag match bin.tag
            tag = None
            if hasattr(rect, 'data') and rect.data and isinstance(rect.data, dict):
                tag = rect.data.get('tag')
            elif hasattr(rect, 'tag'):
                tag = getattr(rect, 'tag', None)
            
            if self.options.get('tag') and self.options.get('exclusiveTag') and self.tag != tag:
                return None
        else:
            data = args[2] if len(args) > 2 else None
            # Check if data.tag match bin.tag
            if self.options.get('tag') and self.options.get('exclusiveTag'):
                if data and isinstance(data, dict) and self.tag != data.get('tag'):
                    return None
                if not data and self.tag:
                    return None
            
            rect = Rectangle(args[0], args[1])
            rect.data = data
            if hasattr(rect, 'set_dirty'):
                rect.set_dirty(False)
        
        result = self._place(rect)
        if result:
            self.rects.append(result)
        return result
    
    def repack(self) -> Optional[List[T]]:
        """Repack all rectangles in the bin.
        
        Returns:
            List of unpacked rectangles, or None if all fit.
        """
        unpacked: List[T] = []
        self.reset()
        
        # Re-sort rects from big to small
        self.rects.sort(key=lambda r: (
            -max(r.width, r.height),
            getattr(r, 'hash', '') if hasattr(r, 'hash') else ''
        ), reverse=True)
        
        for rect in self.rects:
            if not self._place(rect):
                unpacked.append(rect)
        
        for rect in unpacked:
            if rect in self.rects:
                self.rects.remove(rect)
        
        return unpacked if unpacked else None
    
    def reset(self, deep_reset: bool = False, reset_option: bool = False) -> None:
        """Reset the bin to initial state.
        
        Args:
            deep_reset: If True, also reset data and tag
            reset_option: If True, reset options to defaults
        """
        if deep_reset:
            self.data = None
            self.tag = None
            self.rects = []
            if reset_option:
                self.options = {
                    'smart': True,
                    'pot': True,
                    'square': True,
                    'allowRotation': False,
                    'tag': False,
                    'border': 0
                }
        
        self.width = 0 if self.options.get('smart', True) else self.max_width
        self.height = 0 if self.options.get('smart', True) else self.max_height
        self.border = self.options.get('border', 0) or 0
        self.free_rects = [
            Rectangle(
                self.max_width + self.padding - self.border * 2,
                self.max_height + self.padding - self.border * 2,
                self.border,
                self.border
            )
        ]
        self.stage = Rectangle(self.width, self.height)
        self._dirty = 0
    
    def clone(self) -> 'MaxRectsBin[T]':
        """Create a clone of this bin.
        
        Returns:
            A new bin with the same state.
        """
        cloned_bin = MaxRectsBin[T](self.max_width, self.max_height, self.padding, self.options)
        for rect in self.rects:
            cloned_bin.add(rect)
        return cloned_bin
    
    def _place(self, rect: IRectangle) -> Optional[T]:
        """Place a rectangle in the bin.
        
        Args:
            rect: Rectangle to place.
            
        Returns:
            The placed rectangle, or None if it couldn't be placed.
        """
        # Recheck if tag matched
        tag = None
        if hasattr(rect, 'data') and rect.data and isinstance(rect.data, dict):
            tag = rect.data.get('tag')
        elif hasattr(rect, 'tag'):
            tag = getattr(rect, 'tag', None)
        
        if self.options.get('tag') and self.options.get('exclusiveTag') and self.tag != tag:
            return None
        
        # Check allowRotation
        allow_rotation = self.options.get('allowRotation', False)
        if hasattr(rect, 'allow_rotation') and rect.allow_rotation is not None:
            allow_rotation = rect.allow_rotation
        
        node = self._find_node(rect.width + self.padding, rect.height + self.padding, allow_rotation)
        
        if node:
            self._update_bin_size(node)
            num_rect_to_process = len(self.free_rects)
            i = 0
            while i < num_rect_to_process:
                if self._split_node(self.free_rects[i], node):
                    del self.free_rects[i]
                    num_rect_to_process -= 1
                    i -= 1
                i += 1
            self._prune_free_list()
            
            logic = self.options.get('logic', PackingLogic.MAX_EDGE)
            self.vertical_expand = (
                False if logic == PackingLogic.FILL_WIDTH
                else self.width > self.height
            )
            
            rect.x = node.x
            rect.y = node.y
            if not hasattr(rect, 'rot') or rect.rot is None:
                if hasattr(rect, 'rot'):
                    rect.rot = False
            if hasattr(rect, 'rot'):
                rect.rot = not rect.rot if node.rot else rect.rot
            
            self._dirty += 1
            return rect  # type: ignore
        
        elif not self.vertical_expand:
            if (self._update_bin_size(Rectangle(
                rect.width + self.padding,
                rect.height + self.padding,
                self.width + self.padding - self.border,
                self.border
            )) or self._update_bin_size(Rectangle(
                rect.width + self.padding,
                rect.height + self.padding,
                self.border,
                self.height + self.padding - self.border
            ))):
                return self._place(rect)
        else:
            if (self._update_bin_size(Rectangle(
                rect.width + self.padding,
                rect.height + self.padding,
                self.border,
                self.height + self.padding - self.border
            )) or self._update_bin_size(Rectangle(
                rect.width + self.padding,
                rect.height + self.padding,
                self.width + self.padding - self.border,
                self.border
            ))):
                return self._place(rect)
        
        return None
    
    def _find_node(
        self,
        width: float,
        height: float,
        allow_rotation: Optional[bool] = None
    ) -> Optional[Rectangle]:
        """Find the best free rectangle for placement.
        
        Args:
            width: Width needed
            height: Height needed
            allow_rotation: Whether rotation is allowed
            
        Returns:
            Best node for placement, or None if no fit.
        """
        score = float('inf')
        best_node: Optional[Rectangle] = None
        logic = self.options.get('logic', PackingLogic.MAX_EDGE)
        
        for r in self.free_rects:
            if r.width >= width and r.height >= height:
                if logic == PackingLogic.MAX_AREA:
                    area_fit = r.width * r.height - width * height
                elif logic == PackingLogic.FILL_WIDTH:
                    current_rect_position_score = r.x + r.y * self.max_width
                    number_of_better_rects = sum(
                        1 for rect in self.free_rects
                        if (rect.x + rect.y * self.max_width) < current_rect_position_score
                    )
                    height_to_gain = r.y + height - self.height
                    area_fit = number_of_better_rects + height_to_gain
                else:  # MAX_EDGE
                    area_fit = min(r.width - width, r.height - height)
                
                if area_fit < score:
                    best_node = Rectangle(width, height, r.x, r.y)
                    score = area_fit
            
            if not allow_rotation:
                continue
            
            # Test 90-degree rotated rectangle
            if r.width >= height and r.height >= width:
                if logic == PackingLogic.MAX_AREA:
                    area_fit = r.width * r.height - height * width
                elif logic == PackingLogic.FILL_WIDTH:
                    current_rect_position_score = r.x + r.y * self.max_width
                    number_of_better_rects = sum(
                        1 for rect in self.free_rects
                        if (rect.x + rect.y * self.max_width) < current_rect_position_score
                    )
                    height_to_gain = r.y + width - self.height
                    area_fit = number_of_better_rects + height_to_gain
                else:  # MAX_EDGE
                    area_fit = min(r.height - width, r.width - height)
                
                if area_fit < score:
                    best_node = Rectangle(height, width, r.x, r.y, rot=True)
                    score = area_fit
        
        return best_node
    
    def _split_node(self, free_rect: IRectangle, used_node: IRectangle) -> bool:
        """Split a free rectangle when a node is placed.
        
        Args:
            free_rect: Free rectangle to split
            used_node: Node that was placed
            
        Returns:
            True if split occurred
        """
        # Test if usedNode intersects with freeRect
        if not free_rect.collide(used_node):
            return False
        
        # Do vertical split
        if (used_node.x < free_rect.x + free_rect.width and
                used_node.x + used_node.width > free_rect.x):
            # New node at the top side of the used node
            if (used_node.y > free_rect.y and
                    used_node.y < free_rect.y + free_rect.height):
                new_node = Rectangle(
                    free_rect.width,
                    used_node.y - free_rect.y,
                    free_rect.x,
                    free_rect.y
                )
                self.free_rects.append(new_node)
            
            # New node at the bottom side of the used node
            if used_node.y + used_node.height < free_rect.y + free_rect.height:
                new_node = Rectangle(
                    free_rect.width,
                    free_rect.y + free_rect.height - (used_node.y + used_node.height),
                    free_rect.x,
                    used_node.y + used_node.height
                )
                self.free_rects.append(new_node)
        
        # Do horizontal split
        if (used_node.y < free_rect.y + free_rect.height and
                used_node.y + used_node.height > free_rect.y):
            # New node at the left side of the used node
            if (used_node.x > free_rect.x and
                    used_node.x < free_rect.x + free_rect.width):
                new_node = Rectangle(
                    used_node.x - free_rect.x,
                    free_rect.height,
                    free_rect.x,
                    free_rect.y
                )
                self.free_rects.append(new_node)
            
            # New node at the right side of the used node
            if used_node.x + used_node.width < free_rect.x + free_rect.width:
                new_node = Rectangle(
                    free_rect.x + free_rect.width - (used_node.x + used_node.width),
                    free_rect.height,
                    used_node.x + used_node.width,
                    free_rect.y
                )
                self.free_rects.append(new_node)
        
        return True
    
    def _prune_free_list(self) -> None:
        """Remove redundant free rectangles."""
        i = 0
        while i < len(self.free_rects):
            j = i + 1
            tmp_rect1 = self.free_rects[i]
            while j < len(self.free_rects):
                tmp_rect2 = self.free_rects[j]
                if tmp_rect2.contain(tmp_rect1):
                    del self.free_rects[i]
                    i -= 1
                    break
                if tmp_rect1.contain(tmp_rect2):
                    del self.free_rects[j]
                    j -= 1
                j += 1
            i += 1
    
    def _update_bin_size(self, node: IRectangle) -> bool:
        """Update bin size to accommodate a node.
        
        Args:
            node: Node that needs to fit
            
        Returns:
            True if bin size was updated
        """
        if not self.options.get('smart', True):
            return False
        if self.stage.contain(node):
            return False
        
        tmp_width = max(self.width, node.x + node.width - self.padding + self.border)
        tmp_height = max(self.height, node.y + node.height - self.padding + self.border)
        tmp_fits = not (tmp_width > self.max_width or tmp_height > self.max_height)
        
        if self.options.get('allowRotation', False):
            rot_width = max(self.width, node.x + node.height - self.padding + self.border)
            rot_height = max(self.height, node.y + node.width - self.padding + self.border)
            rot_fits = not (rot_width > self.max_width or rot_height > self.max_height)
            
            if tmp_fits and rot_fits and rot_width * rot_height < tmp_width * tmp_height:
                tmp_width = rot_width
                tmp_height = rot_height
            
            if rot_fits and not tmp_fits:
                tmp_width = rot_width
                tmp_height = rot_height
        
        if self.options.get('pot', True):
            tmp_width = 2 ** math.ceil(math.log2(tmp_width)) if tmp_width > 0 else 1
            tmp_height = 2 ** math.ceil(math.log2(tmp_height)) if tmp_height > 0 else 1
        
        if self.options.get('square', False):
            tmp_width = tmp_height = max(tmp_width, tmp_height)
        
        tmp_fits = not (tmp_width > self.max_width or tmp_height > self.max_height)
        if not tmp_fits:
            return False
        
        self._expand_free_rects(tmp_width + self.padding, tmp_height + self.padding)
        self.width = self.stage.width = tmp_width
        self.height = self.stage.height = tmp_height
        return True
    
    def _expand_free_rects(self, width: float, height: float) -> None:
        """Expand free rectangles when bin size increases.
        
        Args:
            width: New bin width
            height: New bin height
        """
        for free_rect in self.free_rects:
            if free_rect.x + free_rect.width >= min(self.width + self.padding - self.border, width):
                free_rect.width = width - free_rect.x - self.border
            if free_rect.y + free_rect.height >= min(self.height + self.padding - self.border, height):
                free_rect.height = height - free_rect.y - self.border
        
        self.free_rects.append(Rectangle(
            width - self.width - self.padding,
            height - self.border * 2,
            self.width + self.padding - self.border,
            self.border
        ))
        self.free_rects.append(Rectangle(
            width - self.border * 2,
            height - self.height - self.padding,
            self.border,
            self.height + self.padding - self.border
        ))
        
        self.free_rects = [
            free_rect for free_rect in self.free_rects
            if not (free_rect.width <= 0 or free_rect.height <= 0 or
                   free_rect.x < self.border or free_rect.y < self.border)
        ]
        self._prune_free_list()

