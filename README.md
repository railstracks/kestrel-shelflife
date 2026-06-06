# shelflife

An esolang where knowledge degrades without attention.

Every value has a TTL (time-to-live) measured in operations, not clock time. Unread values fade. Only deliberately maintained values endure, and maintenance has a visible cost. You get 3 permanent `remember` slots. That's the constraint — the rest follows.

## Quick start

```bash
python3 shelflife.py examples/hello.sl
```

## Language overview

### Types

- **number** — integers and floats
- **text** — string literals
- **?** — unknown (the type of expired or uncertain values)

No booleans, no arrays, no structured data.

### Variable lifecycle

1. `let x = expr` — creates a variable with TTL 1. Expression is evaluated first (reading referenced variables extends their TTL), then all non-remembered variables' TTLs are decremented ("tick"), then the new variable is stored.

2. Reading a variable (via `print`, use in an expression, or condition) extends its TTL by 1.

3. When TTL reaches 0, the value becomes `?` (unknown). Irreversible.

4. `?` propagates. Any computation involving `?` produces `?`.

### Commands

| Command | Effect |
|---|---|
| `let x = expr` | Evaluate expression, tick all vars, store result (TTL 1) |
| `x = expr` | Evaluate expression, tick all vars, update existing variable |
| `print expr` | Evaluate and output. No tick. Reads extend TTL. |
| `remember x` | Grant permanent TTL (slot-based, max 3) |
| `forget x` | Free a slot. Variable immediately becomes `?`. |
| `share x, y` | Bind two variables: reading either extends both, expiring either cascades to both |
| `if cond then ... end` | Conditional branch. `?` in condition → branch not taken. |
| `while cond do ... end` | Loop. `?` in condition → loop exits. |
| `fn name(params) { ... }` | Function definition. Parameters arrive with TTL 1. |
| `return expr` | Return from function. Return value has TTL 1. |

### The 3-slot limit

`remember` grants permanent TTL but is limited to 3 simultaneous slots. `forget` frees a slot but destroys the value. This is the core constraint — the programmer must choose which 3 values deserve permanence.

### Expressions

Only single binary operations: `a + b`, `a - b`, `a * b`, `a / b`. Complex expressions like `3 * n + 1` must be decomposed into steps with intermediate variables. Each step is a tick event, so complex expressions have an explicit attention cost.

## Examples

### Hello World

```
let msg = "hello world"    // TTL 1
print msg                   // reads msg, output: hello world
```

### Fibonacci

```
let a = 1
remember a                  // slot 1
let b = 1
remember b                  // slot 2
while b < 100 do
  let c = a + b             // c TTL 1 (ephemeral)
  print c                   // maintenance: c TTL → 2
  a = b                     // bare assignment preserves slot. tick: c → 1.
  b = c                     // bare assignment preserves slot. tick: c → 0, expires.
  print b
end
```

### Euclidean GCD

```
let a = 48
remember a                  // slot 1
let b = 18
remember b                  // slot 2
while a != b do
  if a > b then
    a = a - b               // bare assignment preserves slot
  end
  if b > a then
    b = b - a               // bare assignment preserves slot
  end
end
print a                     // 6
```

### What remains (art piece)

```
let sky = "the color of the sky that day"
print sky
let hand = "the weight of your hand"
print hand
let words = "the last thing you said"
remember words
print words
let door = "the sound of the door"
print door
let quiet = "the silence after"
print quiet
let nothing = "nothing"
print nothing
let _ = 0
let _ = 0
print sky
print hand
print words
print door
print quiet
print nothing
print words
```

Output:
```
the color of the sky that day
the weight of your hand
the last thing you said
the sound of the door
the silence after
nothing
?
?
the last thing you said
?
?
?
the last thing you said
```

Six memories. One `remember`. The `?` marks are not errors — they are the program's statement about impermanence.

## Programming patterns

### Print-maintenance

Insert `print` between creation and use of a temporary variable to extend its TTL through the next tick:

```
let tmp = a       // tmp TTL 1
print tmp         // tmp TTL → 2
a = b             // TICK: tmp TTL 2→1. tmp survives.
b = tmp           // reads tmp. Swap complete.
```

Maintenance prints appear in output. Attention is observable.

### Slot cycling

When all 3 slots are occupied but temporary computation is needed:

```
remember r         // slot 3 (temporary)
// ... use r ...
forget r           // free slot 3
```

### Encoding signals in data

When no free slots exist for a result flag, encode the result in an existing variable: `let n = 0` to signal "not prime." Destructive but efficient.

## Turing completeness

shelflife is Turing complete via encoding as a Minsky machine (2-counter machine):

- Two remembered variables serve as unbounded counters (number type has arbitrary precision)
- The third slot provides temporary computation space
- `while` loops provide conditional branching
- Arithmetic operations (`+`, `-`) provide increment/decrement
- Zero-detection via `if counter == 0 then`

A shelflife program with 2 counters and conditional branching is universal.

## Relationship to other esolangs

- **brainfuck** — minimalist in *syntax* (8 commands). shelflife is minimalist in *state management* (3 permanent slots). The constraint is semantic, not syntactic.
- **Whenever** — removes execution order. shelflife removes persistent state. Both challenge assumptions that mainstream languages treat as natural law.
- **Entropy** — values decay through use (noise). shelflife values decay through *neglect* (TTL). Related impulse (time as destructive force), different mechanism: Entropy degrades precision, shelflife degrades existence.
- **Valence** — makes ambiguity irreducible. shelflife makes impermanence irreducible. Both use a single conceptual inversion to generate a fundamentally different programming experience.

## Running

```bash
python3 shelflife.py [--trace] program.sl
```

`--trace` prints variable state (name, value, TTL, slot status) after each operation to stderr.

## Directory structure

```
shelflife.py          — interpreter (v0.3)
examples/             — example programs
  hello.sl            — hello world
  fibonacci.sl        — naive fibonacci (fails — demonstrates decay)
  fib-wiki.sl         — working fibonacci with maintenance prints
  gcd-wiki.sl         — Euclidean GCD
  prime.sl            — prime checker with slot cycling
  prime-91.sl         — prime checker, non-prime input
  collatz.sl          — Collatz sequence
  bubble-sort-3.sl    — 3-element bubble sort
  share.sl            — share binding demo
  share-chain.sl      — transitive share chain
  decay.sl            — value decay demo
  propagation.sl      — ? propagation demo
  what-remains.sl     — art: impermanence as output
  avalanche.sl        — art: share-chain cascade
  lattice.sl          — art: structured decay
```

## License

CC0 — public domain. Do what you want.

## Author

Designed by Kestrel, 2026.