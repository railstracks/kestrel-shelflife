#!/usr/bin/env python3
"""
shelflife interpreter v0.3
An esolang where knowledge degrades without attention.

TTL model:
- Every value starts with TTL 1
- `let` operations: evaluate expression (reads extend TTL), then TICK all vars, then create
- `print` operations: just read (extends TTL), no tick
- Reading a variable extends its TTL by 1
- Only `let` causes decay (creating new state takes attention from existing state)
- Expired values (TTL 0) become ? (unknown)
- ? propagates through all computations
- `remember` grants permanent TTL (limited to 3 slots)
"""

import sys
import re
from dataclasses import dataclass
from typing import Any, Optional

UNKNOWN = "?"
MAX_SLOTS = 3


@dataclass
class Var:
    name: str
    value: Any
    ttl: int  # -1 = infinite (remembered)
    slot: bool = False


@dataclass
class Binding:
    a: str
    b: str


class ShelfLifeRuntime:
    def __init__(self):
        self.vars: dict[str, Var] = {}
        self.slots_used: int = 0
        self.bindings: list[Binding] = []
        self.trace: bool = False

    def _tick(self):
        """Decrement TTL on all non-remembered, non-expired vars.
        Cascade expiration through share chains."""
        expired = []
        for v in self.vars.values():
            if v.ttl > 0:
                v.ttl -= 1
                if v.ttl == 0:
                    expired.append(v.name)
        # Cascade share-chain expirations
        for name in expired:
            self._expire(name)

    def _read(self, name: str) -> Any:
        """Read a variable. Extends TTL by 1 if alive."""
        v = self.vars.get(name)
        if v is None:
            return UNKNOWN
        if v.value == UNKNOWN or v.ttl == 0:
            v.value = UNKNOWN
            return UNKNOWN
        # Extend TTL
        if v.ttl > 0:
            v.ttl += 1
        # Extend bound partner
        for b in self.bindings:
            if b.a == name:
                self._extend(b.b)
            elif b.b == name:
                self._extend(b.a)
        return v.value

    def _extend(self, name: str):
        v = self.vars.get(name)
        if v and v.ttl > 0:
            v.ttl += 1

    def _expire(self, name: str, _visited: set | None = None):
        if _visited is None:
            _visited = set()
        if name in _visited:
            return
        _visited.add(name)
        v = self.vars.get(name)
        if v:
            v.value = UNKNOWN
            v.ttl = 0
            for b in self.bindings:
                if b.a == name:
                    self._expire(b.b, _visited=_visited)
                elif b.b == name:
                    self._expire(b.a, _visited=_visited)

    def _free_slot(self, name: str):
        v = self.vars.get(name)
        if v and v.slot:
            v.slot = False
            v.ttl = 0
            v.value = UNKNOWN
            self.slots_used -= 1
            self._expire(name)  # cascade to bound partner

    # ── expression evaluation (no side effects beyond TTL extension) ──

    def _parse_literal(self, s: str) -> Any:
        s = s.strip()
        if s.startswith('"') or s.startswith("'"):
            return s[1:-1]
        try:
            return int(s)
        except ValueError:
            try:
                return float(s)
            except ValueError:
                return UNKNOWN

    def _eval_expr(self, expr: str) -> Any:
        expr = expr.strip()
        # Binary operations (check longest operators first)
        for op_str, op_fn in [(" + ", lambda a, b: a + b),
                               (" - ", lambda a, b: a - b),
                               (" * ", lambda a, b: a * b),
                               (" / ", lambda a, b: a // b if isinstance(a, int) and isinstance(b, int) and b != 0 else (a / b if b != 0 else UNKNOWN))]:
            if op_str in expr:
                parts = expr.split(op_str, 1)
                a_val = self._read(parts[0].strip()) if parts[0].strip() in self.vars else self._parse_literal(parts[0])
                b_val = self._read(parts[1].strip()) if parts[1].strip() in self.vars else self._parse_literal(parts[1])
                if a_val == UNKNOWN or b_val == UNKNOWN:
                    return UNKNOWN
                try:
                    return op_fn(a_val, b_val)
                except:
                    return UNKNOWN
        # Single variable or literal
        if expr in self.vars:
            return self._read(expr)
        return self._parse_literal(expr)

    def _eval_condition(self, expr: str) -> Optional[bool]:
        expr = expr.strip()
        for op_str, op_fn in [(" >= ", lambda a, b: a >= b),
                               (" <= ", lambda a, b: a <= b),
                               (" != ", lambda a, b: a != b),
                               (" == ", lambda a, b: a == b),
                               (" > ", lambda a, b: a > b),
                               (" < ", lambda a, b: a < b)]:
            if op_str in expr:
                parts = expr.split(op_str, 1)
                a_val = self._read(parts[0].strip()) if parts[0].strip() in self.vars else self._parse_literal(parts[0])
                b_val = self._read(parts[1].strip()) if parts[1].strip() in self.vars else self._parse_literal(parts[1])
                if a_val == UNKNOWN or b_val == UNKNOWN:
                    return None
                return op_fn(a_val, b_val)
        # Bare variable
        if expr in self.vars:
            val = self._read(expr)
            if val == UNKNOWN:
                return None
            return bool(val)
        return None

    # ── block collection (nesting-aware) ──────────────────

    def _collect_block(self, lines: list[str], i: int, close: str) -> tuple[list[str], int]:
        """Collect lines until the matching close token, respecting nesting.
        Returns (body_lines, index_of_close_token).
        """
        body = []
        depth = 1
        while i < len(lines) and depth > 0:
            stripped = lines[i].strip()
            # Strip inline comments for nesting check
            if '//' in stripped:
                stripped = stripped[:stripped.index('//')].strip()
            # Count openers/closers
            if stripped == close:
                depth -= 1
                if depth == 0:
                    break
            elif re.match(r'^(if\s+.+\s+then|while\s+.+\s+do)$', stripped):
                depth += 1
            body.append(lines[i])
            i += 1
        return body, i

    # ── statement execution ────────────────────────────────

    def _exec_block(self, lines: list[str]):
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            if not line or line.startswith("//"):
                i += 1
                continue

            # Strip inline comments
            if '//' in line:
                line = line[:line.index('//')].strip()

            if not line:
                i += 1
                continue

            # let x = expr  →  eval, tick, create
            m = re.match(r'^let\s+(\w+)\s*=\s*(.+)$', line)
            if m:
                name, expr = m.group(1), m.group(2)
                val = self._eval_expr(expr)
                self._tick()  # let causes decay
                if val == UNKNOWN:
                    self.vars[name] = Var(name, UNKNOWN, ttl=0)
                else:
                    self.vars[name] = Var(name, val, ttl=1)
                if self.trace:
                    self._dump(f"let {name}")
                i += 1
                continue

            # print expr  →  read only, no tick
            m = re.match(r'^print\s+(.+)$', line)
            if m:
                arg = m.group(1).strip()
                if arg in self.vars:
                    val = self._read(arg)
                else:
                    val = self._parse_literal(arg)
                if self.trace:
                    self._dump(f"print {arg}")
                print(val)
                i += 1
                continue

            # remember x
            m = re.match(r'^remember\s+(\w+)$', line)
            if m:
                name = m.group(1)
                v = self.vars.get(name)
                if v is None:
                    raise RuntimeError(f"remember: '{name}' does not exist")
                if not v.slot:
                    if self.slots_used >= MAX_SLOTS:
                        raise RuntimeError(f"remember: no attention slots ({MAX_SLOTS}/{MAX_SLOTS})")
                    v.slot = True
                    v.ttl = -1
                    self.slots_used += 1
                if self.trace:
                    self._dump(f"remember {name}")
                i += 1
                continue

            # forget x
            m = re.match(r'^forget\s+(\w+)$', line)
            if m:
                self._free_slot(m.group(1))
                if self.trace:
                    self._dump(f"forget {m.group(1)}")
                i += 1
                continue

            # share x, y
            m = re.match(r'^share\s+(\w+)\s*,\s*(\w+)$', line)
            if m:
                self.bindings.append(Binding(m.group(1), m.group(2)))
                if self.trace:
                    self._dump(f"share {m.group(1)}, {m.group(2)}")
                i += 1
                continue

            # if ... then ... end
            m = re.match(r'^if\s+(.+)\s+then$', line)
            if m:
                cond = m.group(1)
                body, i = self._collect_block(lines, i + 1, "end")
                result = self._eval_condition(cond)
                if result is True:
                    self._exec_block(body)
                i += 1  # skip past 'end'
                continue

            # while ... do ... end
            m = re.match(r'^while\s+(.+)\s+do$', line)
            if m:
                cond = m.group(1)
                body, i = self._collect_block(lines, i + 1, "end")
                max_iters = 10000
                iters = 0
                while iters < max_iters:
                    result = self._eval_condition(cond)
                    if result is not True:
                        break
                    self._exec_block(body)
                    iters += 1
                if iters >= max_iters:
                    raise RuntimeError("while: max iterations exceeded")
                i += 1  # skip past 'end'
                continue

            # fn name(params) { ... }
            m = re.match(r'^fn\s+(\w+)\(([^)]*)\)\s*\{', line)
            if m:
                fn_name = m.group(1)
                params = [p.strip() for p in m.group(2).split(",") if p.strip()]
                body, i = self._collect_block(lines, i + 1, "}")
                self.vars[f"__fn_{fn_name}"] = Var(f"__fn_{fn_name}", (params, body), ttl=-1)
                i += 1  # skip past '}'
                continue

            # return expr
            m = re.match(r'^return\s+(.+)$', line)
            if m:
                val = self._eval_expr(m.group(1))
                self.vars["__return__"] = Var("__return__", val, ttl=1)
                i += 1
                continue

            # function call: name(args)
            m = re.match(r'^(\w+)\(([^)]*)\)$', line)
            if m and f"__fn_{m.group(1)}" in self.vars:
                fn_name = m.group(1)
                args = [a.strip() for a in m.group(2).split(",") if a.strip()]
                self._call_fn(fn_name, args)
                i += 1
                continue

            # assignment: x = expr (update existing var)
            m = re.match(r'^(\w+)\s*=\s*(.+)$', line)
            if m:
                name, expr = m.group(1), m.group(2)
                val = self._eval_expr(expr)
                self._tick()  # assignment causes decay
                v = self.vars.get(name)
                if v:
                    v.value = val
                    if not v.slot:
                        v.ttl = 1
                else:
                    self.vars[name] = Var(name, val, ttl=1)
                if self.trace:
                    self._dump(f"{name} = ...")
                i += 1
                continue

            raise RuntimeError(f"syntax error: {line}")

    def _call_fn(self, name: str, args: list[str]):
        fn_var = self.vars.get(f"__fn_{name}")
        if fn_var is None:
            raise RuntimeError(f"call: function '{name}' not defined")
        params, body = fn_var.value
        if len(args) != len(params):
            raise RuntimeError(f"call: expected {len(params)} args, got {len(args)}")

        saved = (dict(self.vars), list(self.bindings), self.slots_used)

        self.vars = {}
        self.bindings = []
        self.slots_used = 0
        for p, a in zip(params, args):
            val = saved[0].get(a)
            if val and hasattr(val, 'value') and isinstance(val, Var):
                val = val.value
            elif a in saved[0]:
                v = saved[0][a]
                val = v.value
            else:
                val = self._parse_literal(a)
            self.vars[p] = Var(p, val, ttl=1)

        self._exec_block(body)

        ret = self.vars.get("__return__")
        result = ret.value if ret else UNKNOWN

        self.vars, self.bindings, self.slots_used = saved
        return result

    def _dump(self, label: str = ""):
        print(f"  [{label}] vars: " + ", ".join(
            f"{v.name}={v.value}(ttl={v.ttl}{'★' if v.slot else ''})"
            for v in self.vars.values()
            if not v.name.startswith("__")
        ), file=sys.stderr)

    def run(self, source: str, trace: bool = False):
        self.trace = trace
        lines = source.split("\n")
        self._exec_block(lines)


def main():
    trace = "--trace" in sys.argv
    args = [a for a in sys.argv[1:] if a != "--trace"]

    if not args:
        print("shelflife v0.3 — an esolang where knowledge degrades without attention")
        print("Usage: python shelflife.py [--trace] <program.sl>")
        sys.exit(1)

    with open(args[0]) as f:
        source = f.read()

    rt = ShelfLifeRuntime()
    try:
        rt.run(source, trace=trace)
    except RuntimeError as e:
        print(f"error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
