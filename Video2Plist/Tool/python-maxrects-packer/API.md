# MaxRects Packer API Documentation

Complete API documentation for the Python maxrects-packer plugin.

## Table of Contents

- [MaxRectsPacker](#maxrectspacker)
- [Rectangle](#rectangle)
- [Types and Constants](#types-and-constants)
- [Usage Examples](#usage-examples)

## MaxRectsPacker

Main class for bin packing operations.

### Constructor

```python
MaxRectsPacker(
    width: float = 4096,
    height: float = 4096,
    padding: float = 0,
    options: Optional[IOption] = None
)
```

**Parameters:**
- `width` (float): Width of the output atlas (default: 4096)
- `height` (float): Height of the output atlas (default: 4096)
- `padding` (float): Padding between rectangles (default: 0)
- `options` (IOption, optional): Packing options

**Example:**
```python
packer = MaxRectsPacker(1024, 1024, 2, {
    'smart': True,
    'allowRotation': True
})
```

### Methods

#### `add(rect: T) -> T`
#### `add(width: float, height: float, data: Any = None) -> T`

Add a rectangle to the packer.

**Parameters:**
- `rect`: Rectangle object with `width` and `height` properties
- OR `width`, `height`, `data`: Width, height, and optional data

**Returns:** The added rectangle

**Example:**
```python
# Method 1: Add rectangle object
rect = {'width': 100, 'height': 200, 'name': 'sprite1'}
packer.add(rect)

# Method 2: Add with width, height, data
packer.add(100, 200, {'name': 'sprite1'})
```

#### `add_array(rects: List[T]) -> None`

Add multiple rectangles at once. Automatically sorts them for optimal packing.

**Parameters:**
- `rects`: List of rectangle objects

**Example:**
```python
rects = [
    {'width': 100, 'height': 200},
    {'width': 150, 'height': 150},
    {'width': 200, 'height': 100},
]
packer.add_array(rects)
```

#### `reset() -> None`

Reset the packer to initial state, keeping settings.

#### `repack(quick: bool = True) -> None`

Repack all elements in bins.

**Parameters:**
- `quick`: If True, only repack dirty bins. If False, repack all.

#### `next() -> int`

Stop adding to current bins and start a new bin group.

**Returns:** Current bin index

#### `save() -> List[Dict[str, Any]]`

Save current bin state to a serializable format.

**Returns:** List of bin dictionaries (JSON-serializable)

#### `load(bins: List[Dict[str, Any]]) -> None`

Load previously saved bin state.

**Parameters:**
- `bins`: List of bin dictionaries from `save()`

### Properties

- `bins: List[Bin[T]]` - List of all bins
- `current_bin_index: int` - Current functioning bin index
- `dirty: bool` - Whether any bins are dirty
- `rects: List[T]` - All rectangles in all bins

## Rectangle

Rectangle class for geometry operations.

### Constructor

```python
Rectangle(
    width: float = 0,
    height: float = 0,
    x: float = 0,
    y: float = 0,
    rot: bool = False,
    allow_rotation: bool | None = None
)
```

### Properties

- `width: float` - Rectangle width
- `height: float` - Rectangle height
- `x: float` - X position
- `y: float` - Y position
- `rot: bool` - Rotation flag
- `allow_rotation: bool | None` - Allow rotation flag
- `data: Any` - Associated data
- `dirty: bool` - Whether rectangle has been modified
- `oversized: bool` - Whether rectangle exceeds bin size

### Methods

#### `area() -> float`

Get the area of the rectangle.

#### `collide(rect: IRectangle) -> bool`

Test if this rectangle collides with another.

#### `contain(rect: IRectangle) -> bool`

Test if this rectangle contains another.

#### `set_dirty(value: bool = True) -> None`

Set the dirty flag.

## Types and Constants

### PackingLogic

Enum for packing logic options:

- `PackingLogic.MAX_AREA = 0` - Select free space with smallest area loss
- `PackingLogic.MAX_EDGE = 1` - Select free space with smallest width/height loss (default)
- `PackingLogic.FILL_WIDTH = 2` - Fill complete width before next row

### IOption

Dictionary type for packer options:

```python
{
    'smart': bool,           # Smart sizing (default: True)
    'pot': bool,             # Power-of-2 sizing (default: True)
    'square': bool,          # Square size (default: False)
    'allowRotation': bool,   # Allow 90° rotation (default: False)
    'tag': bool,             # Enable tag grouping (default: False)
    'exclusiveTag': bool,    # Exclusive tag bins (default: True)
    'border': int,           # Atlas edge spacing (default: 0)
    'logic': PackingLogic    # Packing logic (default: MAX_EDGE)
}
```

### Constants

- `EDGE_MAX_VALUE = 4096` - Default maximum edge size
- `EDGE_MIN_VALUE = 128` - Default minimum edge size

## Usage Examples

### Basic Packing

```python
from maxrects_packer import MaxRectsPacker

packer = MaxRectsPacker(1024, 1024)
packer.add(100, 100, {'name': 'sprite1'})
packer.add(200, 200, {'name': 'sprite2'})

for bin in packer.bins:
    print(f"Bin: {bin.width}x{bin.height}")
    for rect in bin.rects:
        print(f"  {rect.width}x{rect.height} at ({rect.x}, {rect.y})")
```

### With Rotation

```python
packer = MaxRectsPacker(500, 400, 1, {
    'smart': False,
    'allowRotation': True
})

packer.add(398, 98)
packer.add(398, 98)
packer.add(398, 98)
rect = packer.add(398, 98)
print(f"Rotated: {rect.rot}")  # May be True
```

### Tag-based Grouping

```python
packer = MaxRectsPacker(1024, 1024, 0, {
    'tag': True,
    'exclusiveTag': True
})

packer.add(512, 512, {'tag': 'group1'})
packer.add(512, 512, {'tag': 'group1'})
packer.add(512, 512, {'tag': 'group2'})

# Rectangles with same tag go to same bin
```

### Save/Load

```python
# Pack some rectangles
packer = MaxRectsPacker(1024, 1024)
packer.add_array([...])

# Save state
bins = packer.save()
import json
with open('bins.json', 'w') as f:
    json.dump(bins, f)

# Later, load state
with open('bins.json', 'r') as f:
    bins = json.load(f)
packer.load(bins)
packer.add_array([...])  # Continue packing
```

## Comparison with TypeScript API

The Python API is designed to match the TypeScript version:

| TypeScript | Python |
|------------|--------|
| `new MaxRectsPacker(...)` | `MaxRectsPacker(...)` |
| `packer.add(...)` | `packer.add(...)` |
| `packer.addArray(...)` | `packer.add_array(...)` |
| `packer.repack(...)` | `packer.repack(...)` |
| `PACKING_LOGIC.MAX_EDGE` | `PackingLogic.MAX_EDGE` |
| `rect.rot` | `rect.rot` |
| `bin.rects` | `bin.rects` |

