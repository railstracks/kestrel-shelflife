// Collatz sequence — 2 remembered variables, slot cycling for arithmetic
let n = 27
remember n
let i = 2
remember i                  // used as temp divisor

while n != 1 do
  print n
  // Compute n mod 2
  i = 2
  let half = n / i           // reads n (remembered) and i (remembered) — free
  remember half              // slot 3
  let even = half + half     // reads half (now remembered) — free
  let r = n - even           // reads n (remembered) and even (ephemeral) — ticks even. But r is new.
  // r is ephemeral. Use it immediately.
  if r == 0 then
    n = half                 // n = n/2 (both remembered, free)
  end
  forget half                // free slot 3
  if r == 1 then
    let t = n + n            // 2n — reads n (remembered), free
    remember t               // slot 3
    n = t + n                // 3n — reads t (remembered) and n (remembered), free
    n = n + 1                // 3n+1 — reads n (remembered), free
    forget t
  end
end
print n
