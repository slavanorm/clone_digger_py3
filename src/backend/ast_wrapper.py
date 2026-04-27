from __future__ import annotations
import ast
from pathlib import Path
class SourceFile:

    def __init__(self, file_name: Path):
        f = open(file_name, "r", encoding="utf-8", errors="ignore")

        def filter_func(s):
            for i in range(len(s) - 1, -2, -1):
                if i < 0 or not s[i].isspace():
                    break
            if i >= 0:
                return s[: i + 1]
            else:
                return s

        self.source_lines = [filter_func(s) for s in f.readlines()]
        f.close()
        self.file_name = file_name


class StatementSequence:
    def __init__(
        self, sequence: list[AbstractSyntaxTree] = None, source_file: SourceFile = None
    ):
        self._sequence = []
        self.source_file = source_file
        for s in sequence or []:
            self.addStatement(s)

    def getCoveredLineNumbers(self):
        r = set()
        for s in self:
            r.update(s.getCoveredLineNumbers())
        return r

    def getAncestors(self):
        return self[0].getAncestors()

    def addStatement(self, statement: AbstractSyntaxTree):
        self._sequence.append(statement)
        if not self.source_file:
            self.source_file = statement.source_file
        else:
            assert self.source_file == statement.source_file

    def __getitem__(self, *args):
        return self._sequence.__getitem__(*args)

    def __len__(self):
        return self._sequence.__len__()

    def getWeight(self):
        return sum([s.mark.pattern.getSize() for s in self._sequence])

    def getLineNumberHashables(self):
        line_numbers = self.getCoveredLineNumbers()
        return set([(self.source_file.file_name, e) for e in line_numbers])

    def constructTree(self):
        tree = AbstractSyntaxTree("__SEQUENCE__")
        for statement in self:
            tree.addChild(statement, True)
        return tree

    def getCoveredLineNumbersCount(self):
        covered = set()
        for t in self:
            covered.update(t.getCoveredLineNumbers())
        return len(covered)


class TreeMixin:
    def addChild(self, child, save_parent: bool = False):
        if not save_parent:
            child.parent = self
        self.childs.append(child)

    def propagateHeight(self):
        if len(self.childs) == 0:
            self._height = 0
        else:
            self._height = max([c.propagateHeight() for c in self.childs]) + 1
        return self._height


class HashMixin:
    def getFullHash(self):
        return self.getDCupHash(-1)

    def getDCupHash(self, level: int):
        if len(self.childs) == 0:
            ret = 0  # in case of names and constants
        else:
            ret = (level + 1) * hash(self.name) * len(self.childs)
        # if level == -1, it will not stop until it reaches the leaves
        if level != 0:
            for i in range(len(self.childs)):
                child = self.childs[i]
                ret += (i + 1) * child.getDCupHash(level - 1)
        return hash(ret)

    def __hash__(self):
        if not self._hash:
            self._hash = hash(self.getDCupHash(3) + hash(self.name))
        return self._hash

    def __eq__(self, tree2):
        tree1 = self
        if type(tree2) == type(None):
            return False
        if tree1.name != tree2.name:
            return False
        if len(tree1.childs) != len(tree2.childs):
            return False
        for i in range(len(tree1.childs)):
            if tree1.childs[i] != tree2.childs[i]:
                return False
        return True


class LineMixin:
    def getCoveredLineNumbers(self):
        return self._covered_line_numbers

    def getAncestors(self):
        r = []
        t = self.parent
        while t:
            if isinstance(t, ast.stmt):
                r.append(t)
            t = t.parent
        return r

    def getSourceLines(self):
        source_line_numbers = self.getCoveredLineNumbers()
        source_line_numbers_list = list(
            range(
                min(source_line_numbers),
                max(source_line_numbers) + 1,
            )
        )
        source_line_numbers_list.sort()
        return [self.source_file.source_lines[e] for e in source_line_numbers_list]

    def propagateCoveredLineNumbers(self):
        self._covered_line_numbers = set(self._line_numbers)
        for child in self.childs:
            self._covered_line_numbers.update(child.propagateCoveredLineNumbers())
        return self._covered_line_numbers

    def as_string(self):
        return "\n".join(
            [
                self.source_file.source_lines[e]
                for e in sorted(list(self._covered_line_numbers))
            ]
        )


class SizeMixin:
    def storeSize(self, free_variable_cost: float):
        observed = set()
        self._none_count = 0

        def rec_calc_size(t):
            r = 0
            if t not in observed:
                if len(t.childs):
                    for c in t.childs:
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

    def getSize(self, ignore_none: bool = True):
        ret = self._size
        if ignore_none:
            ret -= self._none_count
        return ret

    def getTokenCount(self):
        def rec_calc_size(t):
            if len(t.childs):
                if t.name in [
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
                for c in t.childs:
                    r += rec_calc_size(c)
            else:
                if t.name[0] != "'" and t.name != "Pass":
                    return 0
                else:
                    return 1
            return r

        return rec_calc_size(self)


class AbstractSyntaxTree(TreeMixin, HashMixin, LineMixin, SizeMixin):
    def __init__(
        self,
        name: str = None,
        line_numbers: list[int] = None,
        source_file: SourceFile = None,
    ):
        self.childs = []
        self._line_numbers = line_numbers or []
        self._covered_line_numbers = None
        self.parent = None
        self._hash = None
        self.source_file = source_file
        self._is_statement = False
        self.ast_node = None
        self.name = name or "AbstractSyntaxTree"
        self.mark = None


class FreeVariable(AbstractSyntaxTree):
    count = 0

    def __init__(self):
        FreeVariable.count += 1
        name = "VAR(%d)" % FreeVariable.count
        AbstractSyntaxTree.__init__(self, name)


class NT(ast.NodeTransformer):
    def __init__(self, *args, source_file, ignored_statements=None, **kwargs):
        self._source_file = source_file
        self.ignored_statements = ignored_statements
        super().__init__(*args, **kwargs)

    def prepare_node(self, node: ast.AST):
        if isinstance(node, AbstractSyntaxTree):
            # can do later: learn why it happens
            return node
        if not node:
            return AbstractSyntaxTree("None", source_file=self._source_file)

        # set lines
        name = node.__class__.__name__
        line_numbers = []
        if isinstance(node, ast.AST):
            if name in self.ignored_statements:
                return AbstractSyntaxTree("None", source_file=self._source_file)
            """
            if name in ["FunctionDef", "Class"]:
                # can have ignorelist
                pass
            if name == "FunctionDef":
                for prefix in self._func_prefixes:
                    if node.name.startswith(prefix):
                        # skip function that matches pattern
                        return AbstractSyntaxTree(
                            "none"
                        )
            """
            if "lineno" in node._attributes:
                start = node.lineno - 1
                end = getattr(node, "end_lineno", node.lineno) - 1
                line_numbers = list(range(start, end + 1))

        node_prepared = AbstractSyntaxTree(
            name=name,
            line_numbers=line_numbers,
            source_file=self._source_file,
        )
        node_prepared.ast_node = node

        return node_prepared

    def generic_visit(self, node: ast.AST):
        def write_node_relations(node, child):
            assert isinstance(node, AbstractSyntaxTree)
            assert isinstance(child, AbstractSyntaxTree)
            child.parent = node
            node.addChild(child)

        ignorelist = ["None"]  # cant be Module

        node = self.prepare_node(node)
        if node.name in ignorelist:
            return AbstractSyntaxTree("None", source_file=self._source_file)

        for field, child in ast.iter_fields(node.ast_node):
            if isinstance(child, list):
                new_child = []
                for e in child:
                    if isinstance(e, ast.AST):
                        e = self.generic_visit(e)
                    if e is not None:
                        if not isinstance(e, list):
                            e = self.prepare_node(e)
                        new_child.append(e)
                        write_node_relations(node, e)
                    if isinstance(e, list):
                        new_child.extend(e)

                child[:] = new_child
            else:
                if isinstance(child, ast.AST):
                    child = self.generic_visit(child)
                    if child is None:
                        delattr(node.ast_node, field)
                    else:
                        setattr(node.ast_node, field, child)
                child = self.prepare_node(child)
                write_node_relations(node, child)
        return node


def get_statement_sequences(tree: AbstractSyntaxTree, size_threshold: int):
    not_empty = lambda x: x and len(x.getCoveredLineNumbers()) >= size_threshold

    r = []
    current = StatementSequence(source_file=tree.source_file)

    for child in tree.childs:
        if isinstance(child.ast_node, ast.stmt):
            current.addStatement(child)
        elif not_empty(current):
            r += [current]
            current = StatementSequence(source_file=tree.source_file)

        # recursion here
        r += get_statement_sequences(child, size_threshold=size_threshold)

    if not_empty(current):
        r += [current]

    return r


class ASTWrapper:
    extension = "py"
    ignored_statements = ["Import", "From", "ImportFrom"]

    def __init__(self, file_name: Path, func_prefixes: tuple = ()):
        self._source_file = SourceFile(file_name)
        self._func_prefixes = func_prefixes

        nt = NT(
            source_file=self._source_file,
            ignored_statements=self.ignored_statements,
        )

        with open(file_name, encoding="utf-8", errors="ignore") as f:
            self._tree = nt.visit(ast.parse(source=f.read()))
