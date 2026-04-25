# Clone Digger Refresh

## Part 1: Light Refresh

- [ ] 1A. Remove `import pdb` and `pdb.set_trace()` from clone_detection_algorithm.py
- [ ] 1A. `logging.DEBUG(...)` → `logger.debug(...)` in clone_detection_algorithm.py
- [ ] 1A. `except:` → `except Exception:` in main.py
- [ ] 1B. `logger.warn()` → `logger.warning()` in clone_detection_algorithm.py (3 occurrences)
- [ ] 1C. Remove dead imports from html_report.py (logging, difflib, re, os.path)
- [ ] 1D. Fix `logger.info([...])` list args → f-strings in clone_detection_algorithm.py + main.py
- [ ] 1E. Wrap `open()` in `with` statements in html_report.py
- [ ] 1F. Remove `if __name__ == '__main__':` block from main.py
- [ ] 1F. Fix type annotation `os.path` → `str` in main.py
- [ ] 1F. Update test imports to `from clonedigger.main import main`
- [ ] Verify: `clonedigger tests/test_me.py` produces output.html

## Part 2: Deep Changes

- [ ] 2A. Replace settings.py module globals with a `@dataclass`
- [ ] 2B. Replace `from classes import *` with explicit imports
- [ ] 2C. Add type annotations to all public methods
- [ ] 2D. Replace os.path with pathlib in main.py
- [ ] 2E. Rename `class main` in python3_related.py to PascalCase
- [ ] 2F. Set up pytest, convert tests to proper pytest functions
- [ ] 2G. Fix mutable default args (`sequence=[]`, `line_numbers=[]`)
- [ ] Verify: `python -m pytest tests/`
