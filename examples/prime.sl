// Prime checker in shelflife
// Constraint: need n (number), d (divisor), r (remainder), AND result flag
// That's 4 values for 3 slots. Solution: encode result IN n itself.
// If we find a divisor, destroy n (set to 0). After loop, n==0 means not prime.
// This uses n for double duty — data AND signal.

let n = 97           // number to check
remember n           // slot 1

let d = 2            // divisor
remember d           // slot 2

// No slot 3 needed — r is maintained through careful reading
// The inner loop's `r = r - d` keeps r alive naturally (read extends TTL, tick reduces it, net neutral)

while d < n do
  let r = n          // r = n, TTL 1. Reads n (∞), TICK, create r TTL 1

  // Reduce r modulo d by repeated subtraction
  while r >= d do
    r = r - d        // reads r (TTL 1→2), reads d (∞), TICK: r 2→1. Update r. Net: r stays at TTL 1
  end

  // r now holds n mod d (alive — while condition read it, extending TTL)
  if r == 0 then
    n = 0            // DESTROY n to signal "not prime". n remembered, stays ∞ but value=0.
                     // Next loop check: d < 0 → false. Loop exits.
  end

  if n != 0 then
    d = d + 1        // only advance if we haven't found a divisor
  end
end

// Interpret the result encoded in n
if n == 0 then
  print "not prime"
end
if n != 0 then
  print "prime"
end
