import ast
from . import classes


class NT(ast.NodeTransformer):
    def __init__(
        self,
        *args,
        source_file,
        ignored_statements=None,
        **kwargs
    ):
        self._source_file = source_file
        self.ignored_statements = ignored_statements
        super().__init__(*args, **kwargs)

    def prepare_node(self, node):
        if isinstance(node, classes.AbstractSyntaxTree):
            # todo: learn why it happens
            return node
        if not node:
            return classes.AbstractSyntaxTree(
                "None", source_file=self._source_file
            )

        # set lines
        name = node.__class__.__name__
        lines = []
        if isinstance(node, ast.AST):
            if name in self.ignored_statements:
                return classes.AbstractSyntaxTree(
                    "None", source_file=self._source_file
                )
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
                lines = [node.lineno - 1]

        node_prepared = classes.AbstractSyntaxTree(
            name=name,
            line_numbers=lines,
            source_file=self._source_file,
        )
        node_prepared.ast_node = node

        return node_prepared

    def generic_visit(self, node):
        def write_node_relations(node, child):
            assert isinstance(node, classes.AbstractSyntaxTree)
            assert isinstance(child, classes.AbstractSyntaxTree)
            child.setParent(node)
            node.addChild(child)

        ignorelist = ["None"]  # cant be Module

        node = self.prepare_node(
            node
        )
        if node._name in ignorelist:
            return classes.AbstractSyntaxTree(
                "None", source_file=self._source_file
            )

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


class main(classes.SourceFile):
    extension = "py"
    distance_threshold = 5
    size_threshold = 5
    ignored_statements = ["Import", "From", "ImportFrom"]

    def __init__(self, file_name, func_prefixes=()):
        self._source_file = classes.SourceFile(file_name)
        self._func_prefixes = func_prefixes

        nt = NT(
            source_file=self._source_file,
            ignored_statements=self.ignored_statements,
        )

        with open(file_name) as f:
            self._tree = nt.visit(
                ast.parse(source=f.read())
            )

    """
    @staticmethod
    def flatten(list_input):
        l = []
        for elt in list_input:
            t = type(elt)
            if t is tuple or t is list_input:
                for elt2 in flatten(elt):
                    l.append(elt2)
            else:
                l.append(elt)
        return l

    def rec_build_tree(self, node, is_statement=False):
        def add_children(
            children: list, names=None, is_statement=False
        ):

            if names is not None:
                assert len(children) == len(names)
            else:
                names = [
                    None,
                ] * len(children)

            if not isinstance(children, (list, tuple)):
                children = [children]
            if not isinstance(names, (list, tuple)):
                names = [names]

            for child, name in zip(children, names):
                if isinstance(child, ast.AST):
                    tree = rec_build_tree(child, is_statement)
                    if (
                        tree.getName()
                        in self.ignored_statements
                    ):
                        continue
                elif not isinstance(child, (list, tuple)):
                    tree = AbstractSyntaxTree(repr(child))
                    leaf = PythonNodeLeaf(child)
                    tree.ast_node = leaf
                    if (names is not None) and name:
                        setattr(
                            node_represented.ast_node,
                            name,
                            leaf,
                        )
                else:
                    raise NotImplemented

                tree.setParent(node_represented)
                node_represented.addChild(tree)

        if isinstance(node, ast.AST):

            name = node.__class__.__name__
            node_represented = prepare_node(
                node, self._source_file
            )

            is_statement = name == "Stmt"

            if name in self.ignored_statements:
                pass
            # region parse ast based on name
            elif name == "AssAttr":
                add_children(
                    [node.expr, node.attrname],
                    [None, "attrname"],
                )
            elif name == "AssName":
                add_children(node.name, "name")
            elif name == "AugAssign":
                add_children([node.node, node.expr])
                add_children(node.op, "op")
            elif name == "Class":
                add_children(node.name, "name")
                add_children(flatten(node.bases))
                add_children(node.code)
            elif name == "Compare":
                add_children(node.expr)
                for i in range(len(node.ops)):
                    (op, expr) = node.ops[i]
                    node.ops[i] = (
                        PythonNodeLeaf(op),
                        expr,
                    )
                    add_children(op, "op")
                    add_children(expr)
            elif name in ["Const"]:
                add_children(repr(node.value), "value")
            elif name == "FunctionDef":
                # add_children(node.decorators)
                # not used because they are already abstracted
                add_children(node.name, "name")
                add_children(node.args.args, "args")
                if node.args.defaults == ():
                    node.defaults = []
                add_children(node.args.defaults)
                add_children(node.body)
            elif name == "Getattr":
                add_children(node.expr)
                add_children(node.attrname, "attrname")
            elif name == "Global":
                add_children(node.names, "names")
            elif name == "Keyword":
                add_children(node.name, "name")
                add_children(node.expr)
            elif name == "Lambda":
                add_children(node.args.args, "args")
                if node.defaults == ():
                    node.defaults = []
                add_children(node.defaults)
                add_children(node.code)
            elif name == "Name":
                add_children(node.name, "name")
            else:
                print(name)
                add_children(node.body)

            # endregion
            return node_represented

        return AbstractSyntaxTree(repr(node))
    """
