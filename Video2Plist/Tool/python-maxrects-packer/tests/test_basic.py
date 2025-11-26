"""Basic tests for maxrects-packer."""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from maxrects_packer import MaxRectsPacker, Rectangle, PackingLogic


def test_basic_packing():
    """Test basic packing functionality."""
    packer = MaxRectsPacker(1024, 1024, 0, {
        'smart': True,
        'pot': False,
        'square': False,
        'allowRotation': False,
        'tag': False,
        'exclusiveTag': True
    })
    
    # Add some rectangles
    packer.add(1000, 1000, {'num': 1})
    packer.add(1000, 1000, {'num': 2})
    
    assert len(packer.bins) == 2
    assert packer.bins[0].rects[0].data['num'] == 1
    assert packer.bins[1].rects[0].data['num'] == 2


def test_add_array():
    """Test adding array of rectangles."""
    packer = MaxRectsPacker(1024, 1024, 0)
    
    input_rects = [
        {'width': 600, 'height': 20, 'data': {'num': 1}},
        {'width': 600, 'height': 20, 'data': {'num': 2}},
        {'width': 1000, 'height': 1000, 'data': {'num': 3}},
        {'width': 1000, 'height': 1000, 'data': {'num': 4}},
    ]
    
    packer.add_array(input_rects)
    
    # Should create 2 bins (big rects first)
    assert len(packer.bins) == 2


if __name__ == '__main__':
    test_basic_packing()
    test_add_array()
    print("All basic tests passed!")

