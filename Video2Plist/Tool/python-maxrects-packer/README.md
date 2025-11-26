# MaxRects Packer (Python)

A Python implementation of the max rectangle 2D bin packing algorithm, functionally identical to the TypeScript version.

## Features

- Max Rectangle algorithm for efficient 2D bin packing
- Support for multiple bins (sprite sheets/atlases)
- Smart sizing to minimize waste
- Power-of-2 sizing support
- 90-degree rotation support
- Tag-based grouping
- Save/Load functionality

## Installation

This is a plugin module that can be copied directly into your project. No PyPI installation required.

1. Copy the `maxrects_packer/` directory to your project
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Quick Start

```python
from maxrects_packer import MaxRectsPacker, PackingLogic

# Create a packer
options = {
    'smart': True,
    'pot': True,
    'square': False,
    'allowRotation': True,
    'tag': False,
    'border': 5
}
packer = MaxRectsPacker(1024, 1024, 2, options)

# Add rectangles
input_rects = [
    {'width': 600, 'height': 20, 'name': 'tree', 'foo': 'bar'},
    {'width': 600, 'height': 20, 'name': 'flower'},
    {'width': 1000, 'height': 1000, 'name': 'background', 'color': 0x000000ff},
]

packer.add_array(input_rects)

# Access results
for bin in packer.bins:
    print(f"Bin size: {bin.width}x{bin.height}")
    for rect in bin.rects:
        print(f"  Rect: {rect.width}x{rect.height} at ({rect.x}, {rect.y})")
```

## API Documentation

See [API.md](API.md) for complete API documentation.

## Requirements

- Python 3.7+
- NumPy 1.20.0+

## License

MIT

