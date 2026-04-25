from clonedigger.backend import ast_wrapper, clone_detection_algorithm
from clonedigger.report import html_report
from clonedigger.settings import cfg, logger
from pathlib import Path


def main(fps: list[Path], output: Path, func_prefixes: list[str] = None):
    wrapper = ast_wrapper.main
    report = html_report.HTMLReport()
    source_files = []
    func_prefixes = func_prefixes or []

    def parse_file(file_name, func_prefixes):
        logger.info(f"Parsing {file_name}...")
        source_file = wrapper(file_name, func_prefixes)
        source_file._tree.propagateCoveredLineNumbers()
        source_file._tree.propagateHeight()
        source_files.append(source_file)
        report.file_names += [file_name]

    report.startTimer("Construction of AST")
    for file_name in fps:
        parse_file(file_name, func_prefixes)
    report.stopTimer()

    report.clones = clone_detection_algorithm.main(source_files, report)

    report.sort()
    try:
        report.writeReport(output)
    except Exception:
        logger.error("caught error, removing output file")
        if output.exists():
            output.unlink()
        raise
