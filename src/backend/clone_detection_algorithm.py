from __future__ import annotations
import copy
import logging
import sys
import time
from collections.abc import Callable
from clonedigger.backend.ast_wrapper import (
    AbstractSyntaxTree,
    FreeVariable,
    StatementSequence,
)
from clonedigger.settings import logger


class PairSequences:
    def __init__(self, sequences: list[StatementSequence], cfg=None):
        self._sequences = sequences
        self.cfg = cfg

    def __getitem__(self, *args):
        return self._sequences.__getitem__(*args)

    def __len__(self):
        return len(self[0])

    def getWeight(self):
        assert self[0].getWeight() == self[1].getWeight()
        return self[0].getWeight()

    def calcDistance(self):
        trees = [s.constructTree() for s in self]
        unifier = Unifier(trees[0], trees[1], cfg=self.cfg)
        return unifier.getSize()

    def subSequence(self, first: int, length: int):
        return PairSequences(
            [
                StatementSequence(self[0][first : first + length]),
                StatementSequence(self[1][first : first + length]),
            ],
            cfg=self.cfg,
        )

    def getMaxCoveredLineNumbersCount(self):
        return min([s.getCoveredLineNumbersCount() for s in self])


class Substitution:
    def __init__(self, initial_value: dict = None):
        if not initial_value:
            initial_value = {}
        self.map = initial_value

    def substitute(self, tree: AbstractSyntaxTree, without_copying: bool = False):
        if tree in list(self.map.keys()):
            return self.map[tree]
        else:
            if isinstance(tree, FreeVariable):
                return tree
            if without_copying:
                return tree
            else:
                r = AbstractSyntaxTree(tree.name)
                for child in tree.childs:
                    r.addChild(self.substitute(child, without_copying))
                return r

    def getSize(self, free_variable_cost: float):
        ret = 0
        for u, tree in self.map.items():
            ret += tree.getSize(False) - free_variable_cost
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

    def __init__(self, f_code: Callable):
        self._node = self.SuffixTreeNode()
        self._f_code = f_code

    def _add(self, string, prevelem):
        pos = 0
        node = self._node
        for pos in range(len(string)):
            e = string[pos]
            code = self._f_code(e)
            node.string_positions.append(self.StringPosition(string, pos, prevelem))
            if code not in node.childs:
                node.childs[code] = self.SuffixTreeNode()
            node = node.childs[code]
        node.ending_strings.append(self.StringPosition(string, pos + 1, prevelem))

    def add(self, string: StatementSequence):
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
                (not s1.prevelem) or (not s2.prevelem) or (s1.prevelem != s2.prevelem)
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
                            check_left_diverse_and_add(s1, s2, 1)
        for code, child in list(node.childs.items()):
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
    def __init__(
        self,
        t1: AbstractSyntaxTree,
        t2: AbstractSyntaxTree,
        cfg,
        ignore_parametrization: bool = False,
    ):
        self.cfg = cfg

        def combineSubs(node, s, t):
            # s and t are 2-tuples
            assert list(s[0].map) == list(s[1].map)
            assert list(t[0].map) == list(t[1].map)
            newt = (copy.copy(t[0]), copy.copy(t[1]))
            relabel = {}
            for si in s[0].map:
                if not ignore_parametrization:
                    foundone = False
                    for ti in t[0].map:
                        if (s[0].map[si] == t[0].map[ti]) and (
                            s[1].map[si] == t[1].map[ti]
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
                len(node1.childs) != len(node2.childs)
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
                count = len(node1.childs)
                for i in range(count):
                    (ai, si) = unify(
                        node1.childs[i],
                        node2.childs[i],
                    )
                    (ai, s) = combineSubs(ai, si, s)
                    retNode.addChild(ai)
                return retNode, s

        (self.tree, self.substitutions) = unify(t1, t2)
        self.tree.storeSize(free_variable_cost=cfg.free_variable_cost)
        for i in (0, 1):
            for v in self.substitutions[i].map.values():
                v.storeSize(free_variable_cost=cfg.free_variable_cost)

    def getSize(self):
        return sum([s.getSize(free_variable_cost=self.cfg.free_variable_cost) for s in self.substitutions])


class Cluster:
    count = 0

    def __init__(self, statement: AbstractSyntaxTree = None, cfg=None):
        self.cfg = cfg
        if statement:
            self.pattern = statement
            self._trees = [statement]
            self.max_covered_lines = len(statement.getCoveredLineNumbers())
        else:
            self.pattern = None
            self._trees = []
            self.max_covered_lines = 0
        Cluster.count += 1
        self._cluster_number = Cluster.count

    def __len__(self):
        return len(self._trees)

    def getAddCost(self, statement: AbstractSyntaxTree):
        unifier = Unifier(self.pattern, statement, cfg=self.cfg)
        return (
            len(self) * unifier.substitutions[0].getSize(free_variable_cost=self.cfg.free_variable_cost)
            + unifier.substitutions[1].getSize(free_variable_cost=self.cfg.free_variable_cost)
        )

    def unify(self, statement: AbstractSyntaxTree):
        self.pattern = Unifier(self.pattern, statement, cfg=self.cfg).tree
        self._trees.append(statement)

    def eraseAllTrees(self):
        self._trees = []

    def addWithoutUnification(self, statement: AbstractSyntaxTree):
        self._trees.append(statement)
        if len(statement.getCoveredLineNumbers()) > self.max_covered_lines:
            self.max_covered_lines = len(statement.getCoveredLineNumbers())


def calc_statement_sizes(statement_sequences, cfg):
    for sequence in statement_sequences:
        for statement in sequence:
            statement.storeSize(free_variable_cost=cfg.free_variable_cost)


def build_hash_to_statement(statement_sequences, cfg, dcup_hash=True):
    hash_to_statement = {}
    for sequence in statement_sequences:
        for statement in sequence:
            if dcup_hash:
                # 3 - CONSTANT HERE!
                h = statement.getDCupHash(cfg.hashing_depth)
            else:
                h = statement.getFullHash()
            if h not in hash_to_statement:
                hash_to_statement[h] = [statement]
            else:
                hash_to_statement[h].append(statement)
    return hash_to_statement


def build_unifiers(hash_to_statement, cfg):
    processed_statements_count = 0
    clusters = []
    ret = {}
    for h in list(hash_to_statement.keys()):
        local_clusters = []
        statements = hash_to_statement[h]
        for statement in statements:
            processed_statements_count += 1
            if (processed_statements_count % 1000) == 0:
                logger.debug(f"{processed_statements_count},")
            bestcluster = None
            mincost = sys.maxsize
            for cluster in local_clusters:
                cost = cluster.getAddCost(statement)
                if cost < mincost:
                    mincost = cost
                    bestcluster = cluster
            assert local_clusters == [] or bestcluster
            assert mincost >= 0
            if (not bestcluster) or mincost > cfg.clustering_threshold:
                newcluster = Cluster(statement, cfg=cfg)
                local_clusters.append(newcluster)
            else:
                bestcluster.unify(statement)
        ret[h] = local_clusters
        clusters.extend(local_clusters)
    return ret


def clusterize(hash_to_statement, clusters_map, cfg):
    # clusters_map contain hash values for statements, not unifiers
    # therefore it will work correct even if unifiers are smaller than hashing depth value
    for k, v in hash_to_statement.items():
        clusters = clusters_map[k]
        for statement in v:
            mincost = sys.maxsize
            for cluster in clusters:
                unifier = Unifier(cluster.pattern, statement, cfg=cfg)
                cost = unifier.getSize()
                if cost < mincost:
                    mincost = cost
                    statement.mark = cluster
                    cluster.addWithoutUnification(statement)


def filter_long_sequences(statement_sequences):
    sequences_without_restriction = statement_sequences
    statement_sequences = []
    for sequence in sequences_without_restriction:
        new_sequence = copy.copy(sequence._sequence)
        current_mark = None
        length = 0
        first_statement_index = None
        flag = False
        for i in range(len(sequence)):
            statement = sequence[i]
            if statement.mark != current_mark:
                if flag:
                    flag = False
                current_mark = statement.mark
                length = 0
                first_statement_index = i
            else:
                length += 1
                if length > 10:
                    new_sequence[i] = None
                    if not flag:
                        for i in range(first_statement_index, i):
                            new_sequence[i] = None
                        first_statement = sequence[first_statement_index]
                        logger.warning(
                            f"Warning: sequence of statements starting at "
                            f"{first_statement.source_file.file_name}:"
                            f"{min(first_statement.getCoveredLineNumbers())}"
                        )
                        logger.warning(
                            "consists of many similar statements; "
                            "It will be ignored. Use --force to override this restriction."
                        )
                        flag = True
        new_sequence = new_sequence + [None]
        cur_sequence = StatementSequence()
        for statement in new_sequence:
            if not statement:
                if cur_sequence:
                    statement_sequences.append(cur_sequence)
                    cur_sequence = StatementSequence()
            else:
                cur_sequence.addStatement(statement)
    return statement_sequences


def mark_using_hash(hash_to_statement, cfg):
    for h in hash_to_statement:
        cluster = Cluster(cfg=cfg)
        for statement in hash_to_statement[h]:
            cluster.addWithoutUnification(statement)
            statement.mark = cluster


def find_sequences(statement_sequences, cfg):
    def f_size(x):
        return x.max_covered_lines

    def f_elem(x):
        return StatementSequence(x).getCoveredLineNumbersCount()

    def f_code(x):
        return x.mark

    suffix_tree_instance = SuffixTree(f_code)
    for sequence in statement_sequences:
        suffix_tree_instance.add(sequence)
    return [
        PairSequences([StatementSequence(s1), StatementSequence(s2)], cfg=cfg)
        for (s1, s2) in suffix_tree_instance.getBestMaxSubstrings(
            cfg.size_threshold, f_size, f_elem
        )
    ]


def refine_duplicate_candidates(pairs_sequences, cfg):
    r = []
    flag = False
    while pairs_sequences:
        pair_sequences = pairs_sequences.pop()

        def all_pairsubsequences_size_n_threshold(n):
            lr = []
            for first in range(0, len(pair_sequences) - n + 1):
                new_pair_sequences = pair_sequences.subSequence(first, n)
                size = new_pair_sequences.getMaxCoveredLineNumbersCount()
                if size >= cfg.size_threshold:
                    lr.append((new_pair_sequences, first))
            return lr

        n = len(pair_sequences) + 1
        while n > 0:
            n -= 1
            new_pairs_sequences = all_pairsubsequences_size_n_threshold(n)
            for (candidate_sequence, first) in new_pairs_sequences:
                distance = candidate_sequence.calcDistance()
                if distance < cfg.distance_threshold:
                    r.append(candidate_sequence)
                    if first > 0:
                        pairs_sequences.append(
                            pair_sequences.subSequence(0, first - 1)
                        )
                    if first + n < len(pair_sequences):
                        pairs_sequences.append(
                            pair_sequences.subSequence(
                                first + n,
                                len(pair_sequences) - first - n,
                            )
                        )
                    n += 1
                    flag = True
                    break
            if flag:
                flag = False
                break
    return r


def remove_dominated_clones(clones):
    ret_clones = []
    statement_to_clone = {}
    for clone in clones:
        for sequence in clone:
            for statement in sequence:
                if statement not in statement_to_clone:
                    statement_to_clone[statement] = []
                statement_to_clone[statement].append(clone)
    for clone in clones:
        ancestors_2 = clone[1].getAncestors()
        flag = True
        for s1 in clone[0].getAncestors():
            if s1 in statement_to_clone:
                for clone2 in statement_to_clone[s1]:
                    if s1 in clone2[0]:
                        seq = clone2[1]
                    else:
                        assert s1 in clone2[1]
                        seq = clone2[0]
                    for s2 in seq:
                        if s2 in ancestors_2:
                            flag = False
                            break
                    if not flag:
                        break
            if not flag:
                break
        if flag:
            ret_clones.append(clone)
    return ret_clones


def main(source_files: list, cfg):
    statement_sequences = []
    statement_count = 0
    sequences_lengths = []
    for source_file in source_files:
        sequences = source_file._tree.getStatementSequences(size_threshold=cfg.size_threshold)
        statement_sequences += sequences
        sequences_lengths += [len(s) for s in sequences]
        statement_count += sum([len(s) for s in sequences])

    if not sequences_lengths:
        logger.error(
            "Input is empty or the size of the input is below the size threshold"
        )
        sys.exit(0)

    if logger.level <= logging.DEBUG:
        n_sequences = len(sequences_lengths)
        avg_seq_length = sum(sequences_lengths) / float(n_sequences)
        max_seq_length = max(sequences_lengths)

        logger.debug(f"{n_sequences} sequences")
        logger.debug("average sequence length: %f" % (avg_seq_length,))
        logger.debug("maximum sequence length: %d" % (max_seq_length,))
        sequences_without_restriction = statement_sequences
        sequences = []
        if not cfg.force:
            for sequence in sequences_without_restriction:
                if len(sequence) > 1000:
                    first_statement = sequence[0]
                    logger.warning(
                        f"Warning: sequences of statements, consists of {len(sequence)} elements is too long. "
                        f"It starts at {first_statement.source_file.file_name}:"
                        f"{min(first_statement.getCoveredLineNumbers())}. "
                        f"It will be ignored. Use --force to override this restriction."
                    )
                else:
                    sequences.append(sequence)

    logger.debug(f"Number of statements: {statement_count}. Calculating size for each statement...")
    calc_statement_sizes(statement_sequences, cfg)

    logger.debug("Building statement hash...")
    t0 = time.time()
    hash_to_statement = build_hash_to_statement(
        statement_sequences, cfg, dcup_hash=(not cfg.clusterize_using_hash)
    )
    logger.debug(f"Building statement hash: {time.time() - t0:.2f}s")
    logger.debug(f"Number of different hash values: {len(hash_to_statement)}")

    if cfg.clusterize_using_dcup or cfg.clusterize_using_hash:
        logger.debug("Marking each statement with its hash value")
        mark_using_hash(hash_to_statement, cfg)
    else:
        logger.debug("Building patterns...")
        t0 = time.time()
        clusters_map = build_unifiers(hash_to_statement, cfg)
        logger.debug(f"Building patterns: {time.time() - t0:.2f}s")
        logger.debug(
            f"{Cluster.count} patterns were discovered. Choosing pattern for each statement..."
        )

        t0 = time.time()
        clusterize(hash_to_statement, clusters_map, cfg)
        logger.debug(f"Marking similar statements: {time.time() - t0:.2f}s")

    mark_to_statement_hash = None
    if cfg.report_unifiers:
        logger.debug("Building reverse hash for reporting ...")
        reverse_hash = {}
        for sequence in statement_sequences:
            for statement in sequence:
                mark = statement.mark
                if mark not in reverse_hash:
                    reverse_hash[mark] = []
                reverse_hash[mark].append(statement)
        mark_to_statement_hash = reverse_hash

    logger.debug("Finding similar sequences of statements...")
    if not cfg.force:
        statement_sequences = filter_long_sequences(statement_sequences)

    t0 = time.time()
    duplicate_candidates = find_sequences(statement_sequences, cfg)
    logger.debug(f"Finding similar sequences: {time.time() - t0:.2f}s")
    logger.debug(f"{len(duplicate_candidates)} sequences were found. Refining candidates...")

    if cfg.distance_threshold != -1:
        t0 = time.time()
        duplicate_candidates = refine_duplicate_candidates(duplicate_candidates, cfg)
        logger.debug(f"Refining candidates: {time.time() - t0:.2f}s")

    logger.debug(f"{len(duplicate_candidates)} clones were found")
    if cfg.distance_threshold != -1:
        logger.debug("Removing dominated clones...")
        old_clone_count = len(duplicate_candidates)
        duplicate_candidates = remove_dominated_clones(duplicate_candidates)
        logger.debug(f"{len(duplicate_candidates) - old_clone_count} clones were removed")

    covered_source_lines = set()
    for clone in duplicate_candidates:
        for sequence in clone:
            covered_source_lines = covered_source_lines.union(
                sequence.getLineNumberHashables()
            )
    source_lines = set()
    for sequence in statement_sequences:
        source_lines = source_lines.union(sequence.getLineNumberHashables())

    return dict(
        clones=duplicate_candidates,
        mark_to_statement_hash=mark_to_statement_hash,
        all_source_lines_count=len(source_lines),
        covered_source_lines_count=len(covered_source_lines),
    )
