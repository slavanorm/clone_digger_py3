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

## TODO: de-Java pass

### Java-style getters
`getChilds()`, `getSourceFile()`, `getMark()`, `getCoveredLineNumbers()`, `getParent()`, etc — replace with direct attribute access or `@property`. ~50 lines to cut.

### Dead inheritance
`class main(SourceFile)` in `ast_wrapper.py` inherits `SourceFile` but never uses `self` as a SourceFile — it creates a separate `self._source_file = SourceFile(file_name)`. Drop the inheritance.

### Algorithm mutates report
`clone_detection_algorithm.main()` directly sets `report.mark_to_statement_hash`, `report.all_source_lines_count`, `report.covered_source_lines_count`. Should return results and let the caller wire them to the report.

### 300-line closure function
`clone_detection_algorithm.main()` has 9 nested functions sharing closure state (`statement_sequences`). Could be a flat pipeline or a class.

### Global mutable singleton
`cfg` is imported and read everywhere at call time. Nothing is testable in isolation without mutating the global.

### AbstractSyntaxTree god class
Handles tree structure, hashing, line tracking, mark/cluster assignment, statement sequence extraction, size calculation, and string rendering — 6 responsibilities in one class.
