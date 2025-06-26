import json
import math
import operator
import itertools
from dataclasses import dataclass
from typing import Any, Callable, List, Tuple, Dict, Iterator, Optional, cast

# ---------------- DSL definition constants ---------------- #
CONST_VALUES = [
    0, 1, 2, 3, 4, 5, 10, 15, 20, 25,
    50, 75, 100, 120, 150, 180, 200, 250, 300, 400, 500, 600, 800, 1000,
]
VAR_NAMES = ["d", "m", "r"]
MULTIPLIERS = [0.01, 0.1, 0.25, 0.4, 0.58, 0.8, 1.05]
ROUND_P = [0, 2]

# Comparison operators mapping
COMP_OPS: Dict[str, Callable[[float, float], bool]] = {
    "<": operator.lt,
    "<=": operator.le,
    ">": operator.gt,
    ">=": operator.ge,
    "==": operator.eq,
}

# ---------------- AST node classes ---------------- #
@dataclass(frozen=True)
class Expr:
    def eval(self, env: Dict[str, float]) -> float:
        raise NotImplementedError

    def size(self) -> int:
        """Number of nodes used (for enumeration complexity)."""
        raise NotImplementedError


@dataclass(frozen=True)
class Const(Expr):
    value: float

    def eval(self, env: Dict[str, float]) -> float:  # noqa: D401
        return float(self.value)

    def __str__(self):
        if isinstance(self.value, int):
            return str(self.value)
        return f"{self.value}"

    def size(self) -> int:
        return 1


@dataclass(frozen=True)
class Var(Expr):
    name: str

    def eval(self, env: Dict[str, float]) -> float:
        return float(env[self.name])

    def __str__(self):
        return self.name

    def size(self) -> int:
        return 1


@dataclass(frozen=True)
class Binary(Expr):
    op: str  # '+', '-', 'max', 'min'
    left: Expr
    right: Expr

    def eval(self, env: Dict[str, float]) -> float:
        l = self.left.eval(env)
        r = self.right.eval(env)
        if self.op == '+':
            return l + r
        elif self.op == '-':
            return l - r
        elif self.op == 'max':
            return max(l, r)
        elif self.op == 'min':
            return min(l, r)
        else:
            raise ValueError(f"Unknown op {self.op}")

    def __str__(self):
        if self.op in {'+', '-'}:
            return f"({self.left} {self.op} {self.right})"
        else:
            return f"{self.op}({self.left}, {self.right})"

    def size(self) -> int:
        return 1 + self.left.size() + self.right.size()


@dataclass(frozen=True)
class Scale(Expr):
    op: str  # '*' or '/'
    expr: Expr
    k: float

    def eval(self, env: Dict[str, float]) -> float:
        val = self.expr.eval(env)
        if self.op == '*':
            return val * self.k
        else:
            return val / self.k

    def __str__(self):
        if self.op == '*':
            return f"({self.expr} * {self.k})"
        else:
            return f"({self.expr} / {self.k})"

    def size(self) -> int:
        return 1 + self.expr.size()


@dataclass(frozen=True)
class Round(Expr):
    expr: Expr
    p: int

    def eval(self, env: Dict[str, float]) -> float:
        return round(self.expr.eval(env), self.p)

    def __str__(self):
        return f"round({self.expr}, {self.p})"

    def size(self) -> int:
        return 1 + self.expr.size()


# Predicate
@dataclass(frozen=True)
class Pred:
    left: Expr
    op: str  # one of COMP_OPS keys
    right: Expr

    def eval(self, env: Dict[str, float]) -> bool:
        return COMP_OPS[self.op](self.left.eval(env), self.right.eval(env))

    def size(self) -> int:
        return 1 + self.left.size() + self.right.size()

    def __str__(self):
        return f"({self.left} {self.op} {self.right})"


# Statement classes
@dataclass(frozen=True)
class ReturnStmt:
    expr: Expr

    def eval(self, env: Dict[str, float]) -> float:
        return self.expr.eval(env)

    def size(self) -> int:
        return 1 + self.expr.size()

    def __str__(self):
        return f"return {self.expr}"


@dataclass(frozen=True)
class IfStmt:
    pred: Pred
    then_branch: 'Stmt'
    else_branch: 'Stmt'

    def eval(self, env: Dict[str, float]) -> float:
        if self.pred.eval(env):
            return self.then_branch.eval(env)
        else:
            return self.else_branch.eval(env)

    def size(self) -> int:
        return 1 + self.pred.size() + self.then_branch.size() + self.else_branch.size()

    def __str__(self):
        return f"if {self.pred}: {self.then_branch} else: {self.else_branch}"

# Alias for typing
Stmt = Any  # ReturnStmt or IfStmt


# ---------------- Enumeration utilities ---------------- #

def generate_terms() -> List[Expr]:
    """Generate base terms (Var and Const)."""
    # Use cast because list concatenation with heterogeneous types confuses type checker
    terms = [Var(n) for n in VAR_NAMES] + [Const(c) for c in CONST_VALUES]
    return cast(List[Expr], terms)


def combine_binary(op: str, exprs_left: List[Expr], exprs_right: List[Expr]) -> Iterator[Expr]:
    for l in exprs_left:
        for r in exprs_right:
            yield Binary(op, l, r)


def combine_scale(op: str, exprs: List[Expr]) -> Iterator[Expr]:
    for e in exprs:
        for k in MULTIPLIERS:
            yield Scale(op, e, k)


def combine_round(exprs: List[Expr]) -> Iterator[Expr]:
    for e in exprs:
        for p in ROUND_P:
            yield Round(e, p)


COMMUTATIVE_OPS = {'+', 'max', 'min'}


def enumerate_exprs(max_size: int) -> List[Expr]:
    """Enumerate all unique expressions whose AST size ≤ max_size."""
    # Dynamic programming: build lists per size.
    memo: Dict[int, List[Expr]] = {1: generate_terms()}

    # Helper to avoid generating obvious duplicates for commutative ops
    def should_emit_binary(op: str, left: Expr, right: Expr) -> bool:
        if op in COMMUTATIVE_OPS:
            # Use string ordering as proxy for structural ordering
            return str(left) <= str(right)
        return True

    for size in range(2, max_size + 1):
        current: List[Expr] = []

        # Scale and Round constructions: 1 (root) + child_size = size
        child_size = size - 1
        if child_size in memo:
            for expr in memo[child_size]:
                # scale operations
                for op in ['*', '/']:
                    for k in MULTIPLIERS:
                        current.append(Scale(op, expr, k))
                # round operations
                for p in ROUND_P:
                    current.append(Round(expr, p))

        # Binary constructions: 1 (root) + left_size + right_size = size
        for left_size in range(1, size - 1):
            right_size = size - 1 - left_size
            if right_size < 1:
                continue
            for left_expr in memo[left_size]:
                for right_expr in memo[right_size]:
                    for op in ['+', '-', 'max', 'min']:
                        if should_emit_binary(op, left_expr, right_expr):
                            current.append(Binary(op, left_expr, right_expr))

        memo[size] = current

    # Aggregate all expressions up to max_size
    all_exprs: List[Expr] = []
    for s in range(1, max_size + 1):
        all_exprs.extend(memo.get(s, []))
    return all_exprs


# ---------------- Program enumeration (placeholder) ---------------- #


def main():
    print("Search framework skeleton loaded. TODO: implement enumeration.")

    # Load public cases just to ensure file path ok
    with open('public_cases.json', 'r') as f:
        data = json.load(f)
    print(f"Loaded {len(data)} public cases.")


if __name__ == '__main__':
    main()