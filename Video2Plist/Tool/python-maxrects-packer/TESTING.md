# Testing Guide

## Using Conda Environment

To test the Python maxrects-packer plugin, use Conda to manage the Python environment.

### Setup Conda Environment

```powershell
# Create a new Conda environment with Python 3.7+
conda create -n maxrects-packer python=3.9 -y

# Activate the environment
conda activate maxrects-packer

# Install dependencies
pip install -r requirements.txt

# Install pytest for testing (optional)
pip install pytest
```

### Run Basic Tests

```powershell
# Activate Conda environment first
conda activate maxrects-packer

# Run basic tests
cd python-maxrects-packer
python tests/test_basic.py
```

### Run with pytest (if installed)

```powershell
conda activate maxrects-packer
pytest tests/
```

## Test Structure

- `tests/test_basic.py` - Basic functionality tests
- Additional tests can be added following the same pattern

## Notes

- Ensure Conda is installed and available in PowerShell
- Python 3.7+ is required
- NumPy will be installed via requirements.txt

