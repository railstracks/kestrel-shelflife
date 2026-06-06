// Bubble sort on 3 values in shelflife
// Strategy: remember all 3 (uses all slots), swap using print-maintenance
// The swap pattern: let tmp = a → print tmp → assign a → assign b from tmp
// Each print extends tmp's TTL by 1, surviving the tick from the next assignment

// Create and remember 3 values (careful: each let ticks previous vars)
let v0 = 5
remember v0          // slot 1

let v1 = 3           // v0 safe (remembered)
remember v1          // slot 2

let v2 = 8           // v0, v1 safe (remembered)
remember v2          // slot 3 — all slots used

// Bubble sort: 3 passes guarantee sorted order for 3 elements
// Pass 1: compare v0,v1 then v1,v2
// Pass 2: compare v0,v1 then v1,v2

// Swap v0 and v1 if v0 > v1
if v0 > v1 then
  let tmp = v0       // tmp = 5, TTL 1
  print tmp          // tmp TTL → 2 (read extends by 1)
  v0 = v1            // eval v1 (∞), TICK: tmp TTL 2→1. v0 = 3, remembered so TTL stays ∞
  v1 = tmp           // eval tmp (TTL 1→2), TICK: tmp TTL 2→1. v1 = 5, remembered, TTL ∞
end

// Swap v1 and v2 if v1 > v2
if v1 > v2 then
  let tmp = v1       // tmp = v1, TTL 1
  print tmp          // tmp TTL → 2
  v1 = v2            // TICK: tmp TTL 2→1
  v2 = tmp           // eval tmp (TTL 1→2), TICK: tmp TTL 2→1
end

// Pass 2: check v0,v1 again
if v0 > v1 then
  let tmp = v0
  print tmp
  v0 = v1
  v1 = tmp
end

// Print sorted result
print v0
print v1
print v2
