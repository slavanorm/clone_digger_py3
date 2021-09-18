import settings
import ast
import copy

free_variables_count = settings.free_variables_count
free_variable_cost = settings.free_variable_cost


class SourceFile:
    size_threshold = 5
    distance_threshold = 5

    def __init__(self, file_name):
        f = open(file_name, "r")

        def filter_func(s):
            for i in range(len(s) - 1, -2, -1):
                if i < 0 or not s[i].isspace():
                    break
            if i >= 0:
                return s[: i + 1]
            else:
                return s

        self._source_lines = [
            filter_func(s) for s in f.readlines()
        ]
        f.close()
        self._file_name = file_name

    def getSourceLine(self, n):
        return self._source_lines[n]

    def getFileName(self):
        return self._file_name


class StatementSequence:
    def __init__(self, sequence=[], source_file=None):
        self._sequence = []
        self._source_file = source_file
        for s in sequence:
            self.addStatement(s)

    def getCoveredLineNumbers(self):
        r = set()
        for s in self:
            r.update(s.getCoveredLineNumbers())
        return r

    def getAncestors(self):
        return self[0].getAncestors()

    def isEmpty(self):
        return self._sequence == []

    def addStatement(self, statement):
        self._sequence.append(statement)
        if not self._source_file:
            self._source_file = statement.getSourceFile()
        else:
            assert (
                self._source_file == statement.getSourceFile()
            )

    def __getitem__(self, *args):
        return self._sequence.__getitem__(*args)

    def __len__(self):
        return self._sequence.__len__()

    def getWeight(self):
        return sum(
            [
                s.getCluster().getUnifierSize()
                for s in self._sequence
            ]
        )

    def getSourceFile(self):
        return self._source_file

    def getLineNumberHashables(self):
        source_file_name = self._source_file.getFileName()
        line_numbers = self.getCoveredLineNumbers()
        return set(
            [
                (source_file_name, line_number)
                for line_number in line_numbers
            ]
        )

    def constructTree(self):
        tree = AbstractSyntaxTree("__SEQUENCE__")
        for statement in self:
            tree.addChild(statement, True)
        return tree

    def getLength(self):
        return len(self)

    def getCoveredLineNumbersCount(self):
        covered = set()
        for t in self:
            covered.update(t.getCoveredLineNumbers())
        return len(covered)


class PairSequences:
    def __init__(self, sequences):
        self._sequences = sequences

    def __getitem__(self, *args):
        return self._sequences.__getitem__(*args)

    def getWeight(self):
        assert self[0].getWeight() == self[1].getWeight()
        return self[0].getWeight()

    def calcDistance(self):

        trees = [s.constructTree() for s in self]
        unifier = Unifier(trees[0], trees[1])
        return unifier.getSize()

    def subSequence(self, first, length):
        return PairSequences(
            [
                StatementSequence(
                    self[0][first : first + length]
                ),
                StatementSequence(
                    self[1][first : first + length]
                ),
            ]
        )

    def getLength(self):
        return self[0].getLength()

    def getMaxCoveredLineNumbersCount(self):
        return min(
            [s.getCoveredLineNumbersCount() for s in self]
        )


class Substitution:
    def __init__(self, initial_value=None):
        if not initial_value:
            initial_value = {}
        self.map = initial_value

    def substitute(self, tree, without_copying=False):
        if tree in list(self.map.keys()):
            return self.map[tree]
        else:
            if isinstance(tree, FreeVariable):
                return tree
            if without_copying:
                return tree
            else:
                r = AbstractSyntaxTree(tree.name)
                for child in tree.getChilds():
                    r.addChild(
                        self.substitute(child, without_copying)
                    )
                return r

    def getSize(self):
        ret = 0
        for u, tree in self.map.items():
            ret += (
                tree.getSize(False)
                - settings.free_variable_cost
            )
        return ret


class SuffixTree:
    class StringPosition:
        def __init__(self, string, position, prevelem):
            self.string = string
            self.position = position
            self.prevelem = prevelem

    class SuffixTreeNode:
        def __init__(self):
            self.childs = {}  #
            self.string_positions = []
            self.ending_strings = []

    def __init__(self, f_code):
        self._node = self.SuffixTreeNode()
        self._f_code = f_code

    def _add(self, string, prevelem):
        pos = 0
        node = self._node
        for pos in range(len(string)):
            e = string[pos]
            code = self._f_code(e)
            node.string_positions.append(
                self.StringPosition(string, pos, prevelem)
            )
            if code not in node.childs:
                node.childs[code] = self.SuffixTreeNode()
            node = node.childs[code]
        node.ending_strings.append(
            self.StringPosition(string, pos + 1, prevelem)
        )

    def add(self, string):
        for i in range(len(string)):
            if i == 0:
                prevelem = None
            else:
                prevelem = self._f_code(string[i - 1])
            self._add(string[i:], prevelem)

    def getBestMaxSubstrings(
        self,
        threshold,
        f,
        f_elem,
        node=None,
        initial_threshold=None,
    ):
        initial_threshold = threshold or 0

        def check_left_diverse_and_add(s1, s2, p):
            if (
                (not s1.prevelem)
                or (not s2.prevelem)
                or (s1.prevelem != s2.prevelem)
            ) and s1.position > p:
                candidate = (
                    s1.string[: s1.position - p],
                    s2.string[: s2.position - p],
                )
                if (
                    f_elem(candidate[0]) >= initial_threshold
                    or f_elem(candidate[1]) >= initial_threshold
                ):
                    r.append(candidate)
                return True
            else:
                return False

        if not node:
            node = self._node
        r = []
        if threshold <= 0:
            for s1 in node.ending_strings:
                for s2 in node.string_positions:
                    if s1.string == s2.string:
                        continue
                    check_left_diverse_and_add(s1, s2, 0)
            for i in range(len(node.ending_strings)):
                for j in range(i):
                    s1 = node.ending_strings[i]
                    s2 = node.ending_strings[j]
                    check_left_diverse_and_add(s1, s2, 0)
            for i in range(len(list(node.childs.keys()))):
                for j in range(i):
                    c1 = list(node.childs.keys())[i]
                    c2 = list(node.childs.keys())[j]
                    for s1 in (
                        node.childs[c1].string_positions
                        + node.childs[c1].ending_strings
                    ):
                        for s2 in (
                            node.childs[c2].string_positions
                            + node.childs[c2].ending_strings
                        ):
                            check_left_diverse_and_add(
                                s1, s2, 1
                            )
        for (code, child) in list(node.childs.items()):
            r += self.getBestMaxSubstrings(
                threshold - f(code),
                f,
                f_elem,
                child,
                initial_threshold,
            )
        return r


class Unifier:
    # Unifier is used instead of AntiUnifier
    def __init__(self, t1, t2, ignore_parametrization=False):
        def combineSubs(node, s, t):
            # s and t are 2-tuples
            assert list(s[0].map) == list(
                s[1].map
            )
            assert list(t[0].map) == list(
                t[1].map
            )
            newt = (copy.copy(t[0]), copy.copy(t[1]))
            relabel = {}
            for si in s[0].map:
                if not ignore_parametrization:
                    foundone = False
                    for ti in t[0].map:
                        if (
                            s[0].map[si]
                            == t[0].map[ti]
                        ) and (
                            s[1].map[si]
                            == t[1].map[ti]
                        ):
                            relabel[si] = ti
                            foundone = True
                            break
                if not foundone:
                    newt[0].map[si] = s[0].map[si]
                    newt[1].map[si] = s[1].map[si]
            return (
                Substitution(relabel).substitute(node),
                newt,
            )

        def unify(node1, node2):
            if node1 == node2:
                return node1, (Substitution(), Substitution())
            elif (node1.name != node2.name) or (
                node1.getChildCount() != node2.getChildCount()
            ):
                var = FreeVariable()
                return (
                    var,
                    (
                        Substitution({var: node1}),
                        Substitution({var: node2}),
                    ),
                )
            else:
                s = (Substitution(), Substitution())
                name = node1.name
                retNode = AbstractSyntaxTree(name)
                count = node1.getChildCount()
                for i in range(count):
                    (ai, si) = unify(
                        node1.getChilds()[i],
                        node2.getChilds()[i],
                    )
                    (ai, s) = combineSubs(ai, si, s)
                    retNode.addChild(ai)
                return retNode, s

        (self._unifier, self._substitutions) = unify(t1, t2)
        self._unifier.storeSize()
        for i in (0, 1):
            for v in self._substitutions[i].map.values():
                v.storeSize()

    def getSubstitutions(self):
        return self._substitutions

    def getUnifier(self):
        return self._unifier

    def getSize(self):
        return sum(
            [s.getSize() for s in self.getSubstitutions()]
        )


class Cluster:
    count = 0

    def __init__(self, tree=None):
        if tree:
            self._n = 1
            self._unifier_tree = tree
            self._trees = [tree]
            self._max_covered_lines = len(
                tree.getCoveredLineNumbers()
            )
        else:
            self._n = 0
            self._unifier_tree = None
            self._trees = []
            self._max_covered_lines = 0
        Cluster.count += 1
        self._cluster_number = Cluster.count

    def getUnifierTree(self):
        return self._unifier_tree

    def getCount(self):
        return self._n

    def getAddCost(self, tree):
        unifier = Unifier(self.getUnifierTree(), tree)
        return (
            self.getCount()
            * unifier.getSubstitutions()[0].getSize()
            + unifier.getSubstitutions()[1].getSize()
        )

    def unify(self, tree):
        self._n += 1
        self._unifier_tree = Unifier(
            self.getUnifierTree(), tree
        ).getUnifier()
        self._trees.append(tree)

    def eraseAllTrees(self):
        self._n = 0
        self._trees = []

    def addWithoutUnification(self, tree):
        self._n += 1
        self._trees.append(tree)
        if (
            len(tree.getCoveredLineNumbers())
            > self._max_covered_lines
        ):
            self._max_covered_lines = len(
                tree.getCoveredLineNumbers()
            )

    def getMaxCoveredLines(self):
        return self._max_covered_lines

    def getUnifierSize(self):
        return self.getUnifierTree().getSize()


class AbstractSyntaxTree:
    def __init__(
        self, name=None, line_numbers=[], source_file=None
    ):
        self.childs = []
        self._line_numbers = line_numbers
        self._covered_line_numbers = None
        self._parent = None
        self._hash = None
        self._source_file = source_file
        self._is_statement = False
        self.ast_node = None
        self.name = name or "AbstractSyntaxTree"

    def getSourceFile(self):
        return self._source_file

    def setMark(self, mark):
        self._mark = mark

    def getMark(self):
        return self._mark

    def getCoveredLineNumbers(self):
        return self._covered_line_numbers

    def getParent(self):
        return self._parent

    def setParent(self, parent):
        self._parent = parent

    def getAncestors(self):
        r = []
        t = self.getParent()
        while t:
            if isinstance(t,ast.stmt):
                r.append(t)
            t = t.getParent()
        return r

    def getSourceLines(self):
        source_line_numbers = set([])
        r = []
        source_line_numbers = self.getCoveredLineNumbers()
        source_line_numbers_list = list(
            range(
                min(source_line_numbers),
                max(source_line_numbers) + 1,
            )
        )
        source_line_numbers_list.sort()
        for source_line_number in source_line_numbers_list:
            r.append(
                self.getSourceFile().getSourceLine(
                    source_line_number
                )
            )
        return r

    def getChilds(self):
        return self.childs

    def getChildCount(self):
        return len(self.childs)

    def propagateCoveredLineNumbers(self):
        self._covered_line_numbers = set(self._line_numbers)
        for child in self.getChilds():
            self._covered_line_numbers.update(
                child.propagateCoveredLineNumbers()
            )
        return self._covered_line_numbers

    def propagateHeight(self):
        if self.getChildCount() == 0:
            self._height = 0
        else:
            self._height = (
                max(
                    [
                        c.propagateHeight()
                        for c in self.getChilds()
                    ]
                )
                + 1
            )
        return self._height

    def addChild(self, child, save_parent=False):
        if not save_parent:
            child.setParent(self)
        self.childs.append(child)

    def getFullHash(self):
        return self.getDCupHash(-1)

    def getDCupHash(self, level):
        if len(self.childs) == 0:
            ret = 0  # in case of names and constants
        else:
            ret = (
                (level + 1)
                * hash(self.name)
                * len(self.childs)
            )
        # if level == -1, it will not stop until it reaches the leaves
        if level != 0:
            for i in range(len(self.childs)):
                child = self.childs[i]
                ret += (i + 1) * child.getDCupHash(level - 1)
        return hash(ret)

    def __hash__(self):
        if not self._hash:
            self._hash = hash(
                self.getDCupHash(3) + hash(self.name)
            )

        return self._hash

    def __eq__(self, tree2):
        tree1 = self
        if type(tree2) == type(None):
            return False
        if tree1.name != tree2.name:
            return False
        if tree1.getChildCount() != tree2.getChildCount():
            return False
        for i in range(tree1.getChildCount()):
            if tree1.getChilds()[i] != tree2.getChilds()[i]:
                return False
        return True

    def getStatementSequences(self):

        not_empty = (
            lambda x: (not x.isEmpty())
            and len(x.getCoveredLineNumbers())
            >= settings.size_threshold
        )

        r = []
        current = StatementSequence(
            source_file=self._source_file
        )

        if self._source_file is None:
            v = 1

        for child in self.childs:
            if isinstance(child.ast_node, ast.stmt):
                current.addStatement(child)
            elif not_empty(current):
                r += [current]
                current = StatementSequence(
                    source_file=self._source_file
                )

            # recursion here
            r += child.getStatementSequences()

        if not_empty(current):
            r += [current]

        return r

    def storeSize(self):
        observed = set()
        self._none_count = 0

        def rec_calc_size(t):
            r = 0
            if t not in observed:
                if t.getChildCount():
                    for c in t.getChilds():
                        r += rec_calc_size(c)
                else:
                    observed.add(t)
                    if t.name == "None":
                        self._none_count += 1
                    if t.__class__.__name__ == "FreeVariable":
                        r += free_variable_cost
                    else:
                        r += 1
            return r

        self._size = rec_calc_size(self)

    def getSize(self, ignore_none=True):
        ret = self._size
        if ignore_none:
            ret -= self._none_count
        return ret

    def getTokenCount(self):
        def rec_calc_size(t):
            if t.getChildCount():
                if t.getName() in [
                    "Add",
                    "Assign",
                    "Sub",
                    "Div",
                    "Mul",
                    "Mod",
                    "Function",
                    "If",
                    "Class",
                    "Raise",
                ]:
                    r = 1
                else:
                    r = 0
                for c in t.getChilds():
                    r += rec_calc_size(c)
            else:
                if (
                    t.getName()[0] != "'"
                    and t.getName() != "Pass"
                ):
                    return 0
                else:
                    return 1
            return r

        return rec_calc_size(self)

    def as_string(self):
        return "".join(
            [
                self._source_file._source_lines[e]
                for e in sorted(
                    list(self._covered_line_numbers)
                )
            ]
        )


class FreeVariable(AbstractSyntaxTree):
    def __init__(self):
        global free_variables_count
        free_variables_count += 1
        name = "VAR(%d)" % (free_variables_count)
        AbstractSyntaxTree.__init__(self, name)

