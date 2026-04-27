import sys
from pathlib import Path
from argparse import ArgumentParser
from clonedigger.settings import Settings
from clonedigger.main import main


def cli():


    cmdline = ArgumentParser(
        usage="""To run Clone Digger type:
        clonedigger [OPTION]... [SOURCE FILE OR DIRECTORY]...

        The typical usage is:
        clonedigger source_file_1 source_file_2 ...
          or
        clonedigger path_to_source_tree
        Don't forget to remove automatically generated sources, tests and third
        party libraries from the source tree.

        Notice:
        The semantics of threshold options is discussed in the paper "Duplicate
        code detection using anti-unification", which can be downloaded from the
        site http://clonedigger.sourceforge.net . All arguments are optional.
        Supported options are:
        """
    )
    kwargs = [
        dict(
            args="file_list",
            help="files to parse",
            nargs="+",
        ),
        dict(
            args="--no-recursion",
            dest="no_recursion",
            action="store_true",
            help="do not traverse directions recursively",
        ),
        dict(
            args=["-o", "--output"],
            dest="output",
            help='the name of the output file ("output.html" by default)',
        ),
        dict(
            args="--clustering-threshold",
            type=int,
            dest="clustering_threshold",
            help="read the paper for semantics",
        ),
        dict(
            args="--distance-threshold",
            type=int,
            dest="distance_threshold",
            help="the maximum amount of differences between pair of sequences in clone pair (5 by default). Larger value leads to larger amount of false positives",
        ),
        dict(
            args="--hashing-depth",
            type=int,
            dest="hashing_depth",
            help="default value if 1, read the paper for semantics. Computation can be speeded up by increasing this value (but some clones can be missed)",
        ),
        dict(
            args="--size-threshold",
            type=int,
            dest="size_threshold",
            help="the minimum clone size. The clone size for its turn is equal to the count of lines of code in its the largest fragment",
        ),
        dict(
            args="--clusterize-using-dcup",
            action="store_true",
            dest="clusterize_using_dcup",
            help="mark each statement with its D-cup value instead of the most similar pattern. This option together with --hashing-depth=0 make it possible to catch all considered clones (but it is slow and applicable only to small programs)",
        ),
        dict(
            args="--dont-print-time",
            action="store_false",
            dest="print_time",
            help="do not print time",
        ),
        dict(
            args=["-f", "--force"],
            action="store_true",
            dest="force",
            help="",
        ),
        dict(
            args="--force-diff",
            action="store_true",
            dest="use_diff",
            help="force highlighting of differences based on the diff algorithm",
        ),
        dict(
            args="--fast",
            action="store_true",
            dest="clusterize_using_hash",
            help="find only clones, which differ in variable and function names and constants",
        ),
        dict(
            args="--ignore-dir",
            action="append",
            dest="ignore_dirs",
            help="exclude directories from parsing",
            type=list,
        ),
        dict(
            args="--report-unifiers",
            action="store_true",
            dest="report_unifiers",
            help="",
        ),
        dict(
            args="--func-prefixes",
            action="store",
            dest="f_prefixes",
            help="skip functions/methods with these prefixes (provide a CSV string as argument)",
        ),
        dict(
            args="--file-list",
            dest="file_list",
            help="a file that contains a list of file names that must be processed by Clone Digger",
        ),
    ]
    for kw in kwargs:
        if "args" in kw:
            args = kw.pop("args")
            if isinstance(args, str):
                args = [args]
        cmdline.add_argument(*args, **kw)

    cmdline.set_defaults(**Settings().model_dump())
    options = cmdline.parse_args()

    cfg = Settings(**{
        k: getattr(options, k) for k, v in Settings() if getattr(options, k, None) is not None
    })

    # resolve func prefixes
    func_prefixes = []
    if options.f_prefixes:
        func_prefixes = [e.strip() for e in options.f_prefixes.split(",")]

    # resolve output
    output = Path(options.output or "output.html")

    # collect file paths
    options.ignore_dirs = options.ignore_dirs or []
    if isinstance(options.file_list, str):
        options.file_list = [options.file_list]

    fps = []
    for fp in options.file_list:
        fp = Path(fp)
        if fp.is_dir():
            if cfg.no_recursion:
                fps += list(fp.iterdir())
            else:
                fps += [
                    e
                    for e in fp.rglob("*")
                    if e.is_file() and e.parent.name not in options.ignore_dirs
                ]
        else:
            fps.append(fp)
    main(fps=fps, output=output, func_prefixes=func_prefixes, cfg=cfg)


cli()
