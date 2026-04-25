# Clone Digger Refresh

## Part 1: Light Refresh

- [x] 1A. Remove `import pdb` and `pdb.set_trace()`
- [x] 1A. `logging.DEBUG(...)` → `logger.debug(...)`
- [x] 1A. `except:` → `except Exception:`
- [x] 1B. `logger.warn()` → `logger.warning()`
- [x] 1C. Remove dead imports from html_report.py
- [x] 1D. Fix logger list args → f-strings
- [x] 1E. Wrap `open()` in `with` statements
- [x] 1F. Remove `if __name__ == '__main__':` block
- [x] 1F. Fix type annotation → `list[Path]`, coerce
- [x] 1F. Update test imports

## Part 2: Deep Changes

- [x] 2A. Pydantic BaseModel settings
- [x] 2B. Replace `from classes import *` with explicit imports
- [x] 2C. Add type annotations to all public methods
- [x] 2D. Replace os.path with pathlib in main.py
- [ ] 2E. Rename `class main` in python3_related.py (pending user decision)
- [x] 2F. Set up pytest + test
- [x] 2G. Fix mutable default args
