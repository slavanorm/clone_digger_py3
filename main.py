from backend import python3_related, html_report,clone_detection_algorithm
import global_settings

import sys
import os
from argparse import ArgumentParser

sys.path.insert(0, "")

def main(override: [os.path, bool] = False):
    def parse_file(file_name, func_prefixes):
        # try:
        print("Parsing ", file_name, "...")
        sys.stdout.flush()
        source_file = supplier(file_name, func_prefixes)
        source_file._tree.propagateCoveredLineNumbers()
        source_file._tree.propagateHeight()
        source_files.append(source_file)
        report.addFileName(file_name)
        print("done")
        """
        except:
            s = (
                'Error: can\'t parse "%s" \n: ' % (file_name,)
                + traceback.format_exc()
            )
            report.addErrorInformation(s)
            print(s)
        """

    supplier = python3_related.main
    report = html_report.HTMLReport()
    source_files = []
    # region parse options

    cmdline = ArgumentParser(
        usage="""To run Clone Digger type:
        python clonedigger.py [OPTION]... [SOURCE FILE OR DIRECTORY]...
        
        The typical usage is:
        python clonedigger.py source_file_1 source_file_2 ...
          or
        python clonedigger.py path_to_source_tree
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

    cmdline.set_defaults(
        ingore_dirs=[],
        f_prefixes=None,
        **global_settings.__dict__
    )
    options = cmdline.parse_args()
    if override:
        if isinstance(override, str):
            options = cmdline.parse_args(
                ["--file-list", override]
            )
        else:
            options = cmdline.parse_args(
                ["--file-list", "main.py"]
            )

    options.ignore_dirs = options.ignore_dirs or []
    if isinstance(options.file_list, str):
        options.file_list = [options.file_list]

    if options.f_prefixes:
        func_prefixes = tuple(
            [x.strip() for x in options.f_prefixes.split(",")]
        )
    else:
        func_prefixes = ()

    if options.output is None:
        options.output = "output.html"

    for k, v in vars(options).items():
        if not k.startswith("_"):
            global_settings.__dict__[k] = v
    if options.distance_threshold is None:
        global_settings.distance_threshold = (
            supplier.distance_threshold
        )
    if options.size_threshold is None:
        global_settings.size_threshold = supplier.size_threshold

    # endregion

    report.startTimer("Construction of AST")
    # region collect filenames
    filenames = []
    for file_name in options.file_list:
        if os.path.isdir(file_name):
            if global_settings.no_recursion:
                filenames += [
                    os.path.join(file_name, f)
                    for f in os.listdir(file_name)
                ]
            else:
                filenames += [
                    os.path.join(dirpath, f)
                    for dirpath, dirnames, filenames0 in os.walk(
                        file_name
                    )
                    if dirnames not in options.ignore_dirs
                    for f in filenames0

                ]
    # endregion

    for f in filenames:
        if os.path.splitext(f)[1][1:] == supplier.extension:
            parse_file(f, func_prefixes)
    report.stopTimer()

    report._clones = clone_detection_algorithm.main(source_files, report)

    report.sortByCloneSize()
    try:
        report.writeReport(options.output)
    except:
        print("caught error, removing output file")
        if os.path.exists(options.output):
            os.remove(options.output)
        raise


if __name__ == "__main__":
    # parse path, save a output.html
    main()
