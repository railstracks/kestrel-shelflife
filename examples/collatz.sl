// Collatz sequence from 27 (longest under 100)
// Track n (current value) and steps — 2 remember slots
// Slot 3 for temporary parity computation

let n = 27
remember n           // slot 1

let steps = 0
remember steps       // slot 2

// Slot 3: temporary use per iteration

while n > 1 do
  // Parity check: compute n mod 2 via subtraction
  let p = n          // p = n, TTL 1
  remember p          // slot 3

  while p > 1 do
    p = p - 2        // p remembered, stays ∞
  end
  // p is 0 (even) or 1 (odd)

  if p == 0 then
    forget p          // free slot 3
    n = n / 2         // single binary operation: n / 2. n remembered.
  end

  if p == 1 then
    forget p          // free slot 3
    // n = 3n + 1, but must split into single binary ops
    let tmp = n * 3   // tmp TTL 1
    print tmp          // tmp TTL → 2 (maintenance)
    n = tmp + 1       // reads tmp (2→3), TICK: tmp 3→2. n updated (remembered).
  end

  steps = steps + 1
end

print steps
print n
