import arguments
import copy

# from previous file abstract_syntax_tree
class ParseError:
    def __init__(self, descr):
        self._descr = descr

    def __str__(self):
        return self._descr


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
        #       if n >= len(self._source_lines):
        #           return ''
        # TODO
        # error here
        return self._source_lines[n]

    def _setTree(self, tree):
        self._tree = tree

    def getTree(self):
        return self._tree

    def getFileName(self):
        return self._file_name


class AbstractSyntaxTree:
    def __init__(
        self, name=None, line_numbers=[], source_file=None
    ):
        self._childs = []
        self._line_numbers = line_numbers
        self._covered_line_numbers = None
        self._parent = None
        self._hash = None
        self._source_file = source_file
        self._is_statement = False
        if name:
            self.setName(name)

    def getSourceFile(self):
        return self._source_file

    def setMark(self, mark):
        self._mark = mark

    def getMark(self):
        return self._mark

    def markAsStatement(self, val=True):
        self._is_statement = val

    def isStatement(self):
        return self._is_statement

    def setName(self, name):
        self._name = name

    def getLineNumbers(self):
        return self._line_numbers

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
            if t.isStatement():
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

    def getName(self):
        return self._name

    def getChilds(self):
        return self._childs

    def getChildCount(self):
        return len(self._childs)

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

    def getHeight(self):
        return self._height

    def addChild(self, child, save_parent=False):
        if not save_parent:
            child.setParent(self)
        self._childs.append(child)

    def setChildCount(self, count):
        assert not self._childs
        self._childs = count * [None]

    def setNextUndefinedChild(self, c):
        for i in range(len(self.getChilds())):
            if self.getChilds()[i] == None:
                self._childs[i] = c
        assert ()

    def __str__(self):
        return (
            " ( "
            + self.getName()
            + " ".join(
                [str(child) for child in self.getChilds()]
            )
            + " ) "
        )

    def getFullHash(self):
        return self.getDCupHash(-1)

    def getDCupHash(self, level):
        if len(self._childs) == 0:
            ret = 0  # in case of names and constants
        else:
            ret = (
                (level + 1)
                * hash(self._name)
                * len(self._childs)
            )
        # if level == -1, it will not stop until it reaches the leaves
        if level != 0:
            for i in range(len(self._childs)):
                child = self._childs[i]
                ret += (i + 1) * child.getDCupHash(level - 1)
        return hash(ret)

    def __hash__(self):
        # TODO check correctness
        if not self._hash:
            self._hash = hash(
                self.getDCupHash(3) + hash(self.getName())
            )
        return self._hash

    #       return  hash(self.getDCupHash(3) + hash(self.getName()))

    def __eq__(self, tree2):
        tree1 = self
        if type(tree2) == type(None):
            return False
        if tree1.getName() != tree2.getName():
            return False
        if tree1.getChildCount() != tree2.getChildCount():
            return False
        for i in range(tree1.getChildCount()):
            if tree1.getChilds()[i] != tree2.getChilds()[i]:
                return False
        return True

    def getAllStatementSequences(self):
        r = []
        current = StatementSequence()
        for child in self.getChilds():
            if child.isStatement():
                current.addStatement(child)
            else:
                if (not current.isEmpty()) and len(
                    current.getCoveredLineNumbers()
                ) >= arguments.size_threshold:
                    r.append(current)
                    current = StatementSequence()
            r.extend(child.getAllStatementSequences())
        if (not current.isEmpty()) and len(
            current.getCoveredLineNumbers()
        ) >= arguments.size_threshold:
            r.append(current)
        return r

    def storeSize(self):
        observed = set()
        self._none_count = 0

        def rec_calc_size(t):
            r = 0
            if not t in observed:
                if t.getChildCount():
                    for c in t.getChilds():
                        r += rec_calc_size(c)
                else:
                    observed.add(t)
                    if t.getName() == "None":
                        self._none_count += 1
                    if t.__class__.__name__ == "FreeVariable":
                        r += arguments.free_variable_cost
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


class StatementSequence:
    def __init__(self, sequence=[]):
        self._sequence = []
        self._source_file = None
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
        if self._source_file:
            self._source_file = statement.getSourceFile()
        else:
            assert (
                self._source_file == statement.getSourceFile()
            )

    def __getitem__(self, *args):
        return self._sequence.__getitem__(*args)

    def __len__(self):
        return self._sequence.__len__()

    def __str__(self):
        return ",".join([str(s) for s in self])

    def getWeight(self):
        return sum(
            [
                s.getCluster().getUnifierSize()
                for s in self._sequence
            ]
        )

    def getSourceFile(self):
        return self._source_file

    def getSourceLines(self):
        source_line_numbers = set([])
        r = []
        for statement in self:
            r.extend(statement.getSourceLines())
        return r

    def getLineNumbers(self):
        r = []
        for statement in self:
            r.extend(statement.getLineNumbers())
        return r

    def getLineNumberHashables(self):
        source_file_name = self.getSourceFile().getFileName()
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

    def __str__(self):
        return ";\t".join([str(s) for s in self])

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


# from previous file anti_unification
class FreeVariable(AbstractSyntaxTree):
    free_variables_count = 1

    def __init__(self):
        global free_variables_count
        FreeVariable.free_variables_count += 1
        name = "VAR(%d)" % (FreeVariable.free_variables_count,)
        #       self._childs = []
        AbstractSyntaxTree.__init__(self, name)


class Substitution:
    def __init__(self, initial_value=None):
        if not initial_value:
            initial_value = {}
        self._map = initial_value

    def substitute(self, tree, without_copying=False):
        if tree in list(self._map.keys()):
            return self._map[tree]
        else:
            if isinstance(tree, FreeVariable):
                return tree
            if without_copying:
                return tree
            else:
                r = AbstractSyntaxTree(tree.getName())
                for child in tree.getChilds():
                    r.addChild(
                        self.substitute(child, without_copying)
                    )
                return r

    def getMap(self):
        return self._map

    def getSize(self):
        ret = 0
        for (u, tree) in list(self.getMap().items()):
            ret += (
                tree.getSize(False)
                - arguments.free_variable_cost
            )
        return ret


class Unifier:
    def __init__(self, t1, t2, ignore_parametrization=False):
        def combineSubs(node, s, t):
            # s and t are 2-tuples
            assert list(s[0].getMap().keys()) == list(
                s[1].getMap().keys()
            )
            assert list(t[0].getMap().keys()) == list(
                t[1].getMap().keys()
            )
            newt = (copy.copy(t[0]), copy.copy(t[1]))
            relabel = {}
            for si in list(s[0].getMap().keys()):
                if not ignore_parametrization:
                    foundone = False
                    for ti in list(t[0].getMap().keys()):
                        if (
                            s[0].getMap()[si]
                            == t[0].getMap()[ti]
                        ) and (
                            s[1].getMap()[si]
                            == t[1].getMap()[ti]
                        ):
                            relabel[si] = ti
                            foundone = True
                            break
                if ignore_parametrization or not foundone:
                    newt[0].getMap()[si] = s[0].getMap()[si]
                    newt[1].getMap()[si] = s[1].getMap()[si]
            return (
                Substitution(relabel).substitute(node),
                newt,
            )

        def unify(node1, node2):
            if node1 == node2:
                return node1, (Substitution(), Substitution())
            elif (node1.getName() != node2.getName()) or (
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
                name = node1.getName()
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
            for key in self._substitutions[i].getMap():
                self._substitutions[i].getMap()[key].storeSize()

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
