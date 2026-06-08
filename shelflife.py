#!/usr/bin/env python3
"""
shelflife interpreter v1.0
An esolang where knowledge degrades without attention.

TTL model (v1.0):
- Every value starts with TTL 1
- Reading a variable extends its TTL by 1 AND ticks all other non-remembered variables
- Remembered variables are immune to tick and don't cause tick when read
- let/assignment evaluate expressions (reads tick others), then store/update
- print evaluates and outputs (reads still tick others)
- Expired values (TTL 0) become ? (unknown)
- ? propagates through all computations
- remember grants permanent TTL (limited to 3 slots)
- share is REMOVED — each variable must be individually maintained
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


class ShelfLifeRuntime:
    def __init__(self):
        self.vars: dict[str, Var] = {}
        self.slots_used: int = 0
        self.trace: bool = False

    def _tick_all_except(self, exempt: set[str]):
        """Tick all non-remembered, non-expired variables except those in exempt set."""
        expired = []
        for v in self.vars.values():
            if v.ttl > 0 and not v.slot and v.name not in exempt:
                v.ttl -= 1
                if v.ttl == 0:
                    expired.append(v.name)
        for name in expired:
            v = self.vars.get(name)
            if v:
                v.value = UNKNOWN

    def _read(self, name: str) -> Any:
        """Read a variable. Extends its TTL by 1. Ticks all other non-remembered vars."""
        v = self.vars.get(name)
        if v is None:
            return UNKNOWN
        if v.value == UNKNOWN or v.ttl == 0:
            v.value = UNKNOWN
            return UNKNOWN

        # Extend this variable's TTL (if not permanent)
        if v.ttl > 0:
            v.ttl += 1

        # Tick all other non-remembered variables (reading costs attention)
        if not v.slot:
            # Only tick others if this var is NOT remembered
            # (remembered vars are free to read)
            self._tick_all_except({name})

        return v.value

    def _read_silent(self, name: str) -> Any:
        """Read without ticking others. Used internally during expression eval
        to avoid double-ticking when multiple variables are read in one expression."""
        v = self.vars.get(name)
        if v is None:
            return UNKNOWN
        if v.value == UNKNOWN or v.ttl == 0:
            v.value = UNKNOWN
            return UNKNOWN
        # Extend TTL but don't tick others
        if v.ttl > 0:
            v.ttl += 1
        return v.value

    def _free_slot(self, name: str):
        v = self.vars.get(name)
        if v and v.slot:
            v.slot = False
            v.ttl = 0
            v.value = UNKNOWN
            self.slots_used -= 1

    # ── expression evaluation ──────────────────────────────

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

    def _is_var(self, name: str) -> bool:
        return name in self.vars

    def _eval_expr(self, expr: str) -> Any:
        """Evaluate expression. Reads all referenced variables with tick side-effects.

        For binary expressions, we read the first operand (which ticks others),
        then read the second operand (which ticks others again, including
        potentially the first if it's not remembered).

        Single variable reads tick all other non-remembered vars.
        """
        expr = expr.strip()
        # Binary operations (check longest operators first)
        for op_str, op_fn in [(" + ", lambda a, b: a + b),
                               (" - ", lambda a, b: a - b),
                               (" * ", lambda a, b: a * b),
                               (" / ", lambda a, b: a // b if isinstance(a, int) and isinstance(b, int) and b != 0 else (a / b if b != 0 else UNKNOWN))]:
            if op_str in expr:
                parts = expr.split(op_str, 1)
                left = parts[0].strip()
                right = parts[1].strip()

                # Read left operand (ticks others)
                if self._is_var(left):
                    a_val = self._read(left)
                else:
                    a_val = self._parse_literal(left)

                # Read right operand (ticks others)
                if self._is_var(right):
                    b_val = self._read(right)
                else:
                    b_val = self._parse_literal(right)

                if a_val == UNKNOWN or b_val == UNKNOWN:
                    return UNKNOWN
                try:
                    return op_fn(a_val, b_val)
                except Exception:
                    return UNKNOWN

        # Single variable or literal
        if self._is_var(expr):
            return self._read(expr)
        return self._parse_literal(expr)

    def _eval_condition(self, expr: str) -> Optional[bool]:
        """Evaluate a condition. Same tick rules as expressions."""
        expr = expr.strip()
        for op_str, op_fn in [(" >= ", lambda a, b: a >= b),
                               (" <= ", lambda a, b: a <= b),
                               (" != ", lambda a, b: a != b),
                               (" == ", lambda a, b: a == b),
                               (" > ", lambda a, b: a > b),
                               (" < ", lambda a, b: a < b)]:
            if op_str in expr:
                parts = expr.split(op_str, 1)
                left = parts[0].strip()
                right = parts[1].strip()

                if self._is_var(left):
                    a_val = self._read(left)
                else:
                    a_val = self._parse_literal(left)

                if self._is_var(right):
                    b_val = self._read(right)
                else:
                    b_val = self._parse_literal(right)

                if a_val == UNKNOWN or b_val == UNKNOWN:
                    return None
                try:
                    return op_fn(a_val, b_val)
                except Exception:
                    return None

        # Bare variable
        if self._is_var(expr):
            val = self._read(expr)
            if val == UNKNOWN:
                return None
            return bool(val)
        return None

    # ── block collection (nesting-aware) ──────────────────

    def _collect_block(self, lines: list[str], i: int, close: str) -> tuple[list[str], int]:
        body = []
        depth = 1
        while i < len(lines) and depth > 0:
            stripped = lines[i].strip()
            if '//' in stripped:
                stripped = stripped[:stripped.index('//')].strip()
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

            if '//' in line:
                line = line[:line.index('//')].strip()
            if not line:
                i += 1
                continue

            # let x = expr → eval (reads tick others), create var
            m = re.match(r'^let\s+(\w+)\s*=\s*(.+)$', line)
            if m:
                name, expr = m.group(1), m.group(2)
                val = self._eval_expr(expr)
                if val == UNKNOWN:
                    self.vars[name] = Var(name, UNKNOWN, ttl=0)
                else:
                    self.vars[name] = Var(name, val, ttl=1)
                if self.trace:
                    self._dump(f"let {name}")
                i += 1
                continue

            # print expr → eval and output (reads tick others)
            m = re.match(r'^print\s+(.+)$', line)
            if m:
                arg = m.group(1).strip()
                if self._is_var(arg):
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

            # if ... then ... end
            m = re.match(r'^if\s+(.+)\s+then$', line)
            if m:
                cond = m.group(1)
                body, i = self._collect_block(lines, i + 1, "end")
                result = self._eval_condition(cond)
                if result is True:
                    self._exec_block(body)
                i += 1
                continue

            # while ... do ... end
            m = re.match(r'^while\s+(.+)\s+do$', line)
            if m:
                cond = m.group(1)
                body, i = self._collect_block(lines, i + 1, "end")
                max_iters = 100000
                iters = 0
                while iters < max_iters:
                    result = self._eval_condition(cond)
                    if result is not True:
                        break
                    self._exec_block(body)
                    iters += 1
                if iters >= max_iters:
                    raise RuntimeError("while: max iterations exceeded")
                i += 1
                continue

            # fn name(params) { ... }
            m = re.match(r'^fn\s+(\w+)\(([^)]*)\)\s*\{', line)
            if m:
                fn_name = m.group(1)
                params = [p.strip() for p in m.group(2).split(",") if p.strip()]
                body, i = self._collect_block(lines, i + 1, "}")
                self.vars[f"__fn_{fn_name}"] = Var(f"__fn_{fn_name}", (params, body), ttl=-1)
                i += 1
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

        saved = (dict(self.vars), self.slots_used)

        self.vars = {}
        self.slots_used = 0
        for p, a in zip(params, args):
            if a in saved[0]:
                v = saved[0][a]
                val = v.value
            else:
                val = self._parse_literal(a)
            self.vars[p] = Var(p, val, ttl=1)

        self._exec_block(body)

        ret = self.vars.get("__return__")
        result = ret.value if ret else UNKNOWN

        self.vars, self.slots_used = saved
        return result

    def _dump(self, label: str = ""):
        items = []
        for v in self.vars.values():
            if v.name.startswith("__"):
                continue
            marker = "★" if v.slot else ""
            items.append(f"{v.name}={v.value}(ttl={v.ttl}{marker})")
        print(f"  [{label}] {', '.join(items)}", file=sys.stderr)

    def run(self, source: str, trace: bool = False):
        self.trace = trace
        lines = source.split("\n")
        self._exec_block(lines)


def main():
    trace = "--trace" in sys.argv
    args = [a for a in sys.argv[1:] if a != "--trace"]

    if not args:
        print("shelflife v1.0 — an esolang where knowledge degrades without attention")
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
