from clonedigger.backend import ast_wrapper, clone_detection_algorithm
from clonedigger.report import html_report
from clonedigger.settings import Settings, logger
from pathlib import Path


def main(fps: list[Path], output: Path, func_prefixes: list[str] = None, cfg: Settings = None):
    cfg = cfg or Settings()
    logger.setLevel(cfg.logger_level)
    wrapper = ast_wrapper.ASTWrapper
    fps = [e for e in fps if e.suffix == f".{wrapper.extension}"]
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

    result = clone_detection_algorithm.main(source_files, cfg)
    report.clones = result["clones"]
    report.all_source_lines_count = result["all_source_lines_count"]
    report.covered_source_lines_count = result["covered_source_lines_count"]
    report.mark_to_statement_hash = result["mark_to_statement_hash"]

    report.sort()
    try:
        report.writeReport(output, cfg)
    except Exception:
        logger.error("caught error, removing output file")
        if output.exists():
            output.unlink()
        raise
