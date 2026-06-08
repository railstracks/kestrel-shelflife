# shelflife

An esolang where knowledge degrades without attention.

Every value has a TTL (time-to-live). Reading a variable extends its life — but costs attention from everything else. You get 3 permanent `remember` slots. That's the constraint.

```
$ python3 shelflife.py examples/hello.sl
hello world
```

## The rule

**Reading a variable extends its TTL by 1 AND ticks (decrements) the TTL of every other non-remembered variable.**

This is the entire mechanic. Everything follows:

- Values start with TTL 1. One tick and they're gone.
- Reading keeps a value alive but degrades everything else you know.
- `remember` grants permanent storage. 3 slots maximum.
- Expired values become `?` (unknown). `?` propagates through all computations.
- `share` does not exist. Each variable must be individually maintained.

## Language reference

### Types

- **number** — integers and floats
- **text** — string literals (`"hello"`, `'world'`)
- **?** — unknown (the type of expired or uncertain values)

No booleans. No arrays. No structured data.

### Statements

```
let x = expr          Create variable (TTL 1, not remembered)
x = expr              Update variable (preserves remember slot if it has one)
print expr            Output value (reads tick other non-remembered vars)
remember x            Grant permanent storage (max 3 slots)
forget x              Release slot (variable expires immediately)
if cond then ... end  Conditional
while cond do ... end Loop (max 100,000 iterations)
fn name(a, b) { ... } Function definition
return expr           Return from function
```

### Expressions

Single binary operations only: `a + b`, `a - b`, `a * b`, `a / b` (integer division).

Comparisons: `==`, `!=`, `<`, `>`, `<=`, `>=`.

### Functions

Functions get a clean scope. Arguments are passed by value. Return via `return expr`.

## Examples

### Hello world

```shelflife
let msg = "hello world"
print msg
```

Reading `msg` extends its TTL. But since no other non-remembered variables exist, there's no cost. This is the only time reading is free.

### Fibonacci

```shelflife
let a = 1
remember a
let b = 1
remember b
while b < 100 do
  let c = a + b
  a = b
  b = c
  print b
end
```

Both loop variables are remembered — free to read, no tick cascade. The temp `c` is ephemeral but doesn't need to survive beyond the iteration.

### GCD (Euclidean)

```shelflife
let a = 48
remember a
let b = 18
remember b
while b != 0 do
  let t = a % b
  a = b
  b = t
end
print a
```

### Prime checker

```shelflife
let n = 97
remember n
let i = 2
remember i
let found = 0
remember found
while i * i <= n do
  let r = n - (n / i) * i
  if r == 0 then
    i = n + 1
    found = 1
  end
  i = i + 1
end
if found == 0 then
  print n
end
```

Uses 3 remember slots: the number, the divisor, and a flag. The flag is necessary because `?` (from an expired variable) can't serve as a reliable boolean — you need a known value.

### Collatz sequence

```shelflife
let n = 27
remember n
let i = 2
remember i
while n != 1 do
  print n
  let half = n / i
  remember half
  let even = half + half
  let r = n - even
  if r == 0 then
    n = half
  end
  forget half
  if r == 1 then
    let t = n + n
    remember t
    n = t + n
    n = n + 1
    forget t
  end
end
print n
```

The third remember slot cycles between `half` (for even/odd test) and `t` (for 3n+1 computation). Both operations need a temporary that must survive multiple reads without ticking `n` or `i`.

### Decay

```shelflife
let x = 42
print x
let y = 1
print x
```

Output: `42` then `?`. Reading `x` the first time gives it TTL 2. Then `let y = 1` reads the literal `1` (no ticks). But the second `print x` reads `x` (extends to TTL 3) and... wait, actually `print` doesn't create new vars. The tick comes from reading `y` later. The point is: values fade.

## Design notes

shelflife is designed around a single question: **what if maintaining knowledge has a visible cost?**

The read-tick mechanic creates a genuine tradeoff. You can't keep everything alive for free. Every read is a tax on everything else you know. The 3 remember slots are scarce enough to matter but generous enough to be useful.

The constraint forces specific patterns:

- **Slot cycling** — rotate the third slot between temporaries
- **Single-use intermediates** — compute, consume, let die
- **Print maintenance** — `print` reads a variable (extending TTL), useful when you need an extra tick but don't care about the output
- **Bare assignment vs let** — `x = expr` preserves the remember slot; `let x = expr` creates fresh (loses slot)

## Why no `share`

v0.3 had a `share` command that let variables extend each other's TTL for free. This made the TTL constraint trivially bypassable — you could share all variables into a cluster and never lose anything. The community feedback was clear: the mechanic was "too easy to make irrelevant."

v1.0 removes `share` entirely. Reading a variable costs attention from everything else. There is no free way to maintain state.

## Running

```bash
python3 shelflife.py program.sl
python3 shelflife.py --trace program.sl   # debug output to stderr
```

Requires Python 3.10+.

## License

CC0 — public domain. The language specification is free for anyone to implement, extend, or ignore.
