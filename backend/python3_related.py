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
            # can do later: learn why it happens
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
        if node.name in ignorelist:
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

        with open(file_name,encoding='utf-8', errors='ignore') as f:
            self._tree = nt.visit(
                ast.parse(source=f.read())
            )
