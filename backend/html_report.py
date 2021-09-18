import logging
import time
import difflib
import re
import os.path
from jinja2 import Template

import settings
from backend import classes


class Report:
    def __init__(self):
        self.error_info = []
        self.clones = []
        self.timers = []
        self.file_names = []
        self.mark_to_statement_hash = None

    def sort(self):
        # sortByCloneSize
        self.clones.sort(
            key=lambda x: -x.getMaxCoveredLineNumbersCount()
        )

    def startTimer(self, descr):
        self.timers.append([descr, time.time(), time.ctime()])

    def stopTimer(self, descr=""):
        self.timers[-1][1] = time.time() - self.timers[-1][1]

class HTMLReport(Report):

    def writeReport(self, file_name):
        clone_descriptions =[]
        for idx, clone in enumerate(self.clones):
            rows = []
            for i in range(len(clone[0])):
                statements = [clone[j][i] for j in [0, 1]]
                u = classes.Unifier(*statements)
                rows += [[u.getSize() > 0,*[e.as_string() for e in statements]]]
            clone_descriptions += [dict(
                idx=idx,
                distance=clone.calcDistance(),
                cloned_length=max(len(set(e.getCoveredLineNumbers())) for e in clone),
                filenames=[e._source_file._file_name for e in clone],
                linenos=[min(e[0].getCoveredLineNumbers()) + 1 for e in clone],
                rows=rows)]

        lines_dup = self.covered_source_lines_count
        lines_ttl = self.all_source_lines_count
        lines_perc = round(lines_dup * 100.0 / lines_ttl, 2) or 100

        result = dict(
            files=self.file_names,
            params=settings.__dict__,
            count_clones=len(self.clones),
            lines_dup=lines_dup,
            lines_ttl=lines_ttl,
            lines_perc=lines_perc,
            errors_info=self.error_info,
            timings="",
            marks_report="",
            table=clone_descriptions
        )

        if settings.print_time:
            timings = ""
            timings += "<B>Time elapsed</B><BR>"
            timings += "<BR>\n".join(
                [
                    "%s : %.2f seconds" % (i[0], i[1])
                    for i in self.timers
                ]
            )
            timings += "<BR>\n Total time: %.2f" % (
                self.getTotalTime()
            )
            timings += "<BR>\n Started at: " + self.timers[0][2]
            timings += "<BR>\n Finished at: " + self.timers[-1][2]
            result["timings"] = timings
        if self.mark_to_statement_hash:
            marks_report = "<P>Top 20 statement marks:"
            marks = list(self.mark_to_statement_hash)
            marks.sort(
                key=lambda x: -len(self.mark_to_statement_hash[x])
            )
            counter = 0
            for mark in marks[:20]:
                counter += 1
                marks_report += (
                    "<BR>"
                    + str(len(self.mark_to_statement_hash[mark]))
                    + ":"
                    + str(mark.getUnifierTree())
                    + "<a href=\"javascript:unhide('stmt%d');\">show/hide representatives</a> "
                    % counter
                )
                marks_report += (
                    '<div id="stmt%d" class="hidden"> <BR>' % counter
                )
                for statement in self.mark_to_statement_hash[mark]:
                    marks_report += str(statement) + "<BR>"
                marks_report += "</div>"
                marks_report += "</P>"
            result["marks_report"] = marks_report

        HTML_base = open("backend/template.html").read()
        HTML_base = Template(HTML_base)
        HTML_code = HTML_base.render(**result)
        f = open(file_name, "w")
        f.write(HTML_code)
        f.close()
