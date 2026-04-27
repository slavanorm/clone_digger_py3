# Clone Digger Refresh

## Done

### Part 1: Light Refresh
- Remove `import pdb` and `pdb.set_trace()`
- `logging.DEBUG(...)` → `logger.debug(...)`
- `except:` → `except Exception:`
- `logger.warn()` → `logger.warning()`
- Remove dead imports from html_report.py
- Fix logger list args → f-strings
- Wrap `open()` in `with` statements
- Remove `if __name__ == '__main__':` block
- Fix type annotation → `list[Path]`, coerce
- Update test imports

### Part 2: Deep Changes
- Pydantic BaseModel settings
- Replace `from classes import *` with explicit imports
- Add type annotations to all public methods
- Replace os.path with pathlib in main.py
- Set up pytest + test
- Fix mutable default args
- a=a variable naming pass
- Move report out of backend → `report/`
- Merge logging into settings
- Split classes.py into ast_wrapper.py and clone_detection_algorithm.py
- Move CLI handling into `__main__.py`
- Rename python3_related.py → ast_wrapper.py

### Part 3: de-Java pass
- Kill Java-style getters → direct attribute access
- `Cluster.n` → `__len__`
- `Unifier.unifier` → `Unifier.tree`
- `Cluster.unifier_tree` → `Cluster.pattern`
- Cluster method param `tree` → `statement`
- Drop dead inheritance `class main(SourceFile)`
- Algorithm returns dict instead of mutating report
- Flatten 300-line closure → 9 module-level functions with explicit params
- Frozen `Settings` + pass `cfg` as param (no global singleton)
- `class main` → `class ASTWrapper`
- Move extension filter from `__main__` to `main.py`
- Move `SourceFile.size_threshold`/`distance_threshold` to Settings

## TODO

### AbstractSyntaxTree god class
Handles tree structure, hashing, line tracking, mark/cluster assignment, statement sequence extraction, size calculation, and string rendering — 6 responsibilities in one class.
