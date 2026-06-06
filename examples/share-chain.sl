// Share chain cascade test — proper version
// Variables must be alive when share is declared

let a = 10          // a TTL 1
print a             // a TTL → 2 (read extends)
let b = 20          // TICK: a TTL 2→1. b TTL 1
print a             // a TTL 1→2
print b             // b TTL 1→2
let c = 30          // TICK: a 2→1, b 2→1. c TTL 1
print a             // a 1→2
print b             // b 1→2
print c             // c 1→2

// Now all are alive (TTL 2). Create share chain.
share a, b          // a and b linked
share b, c          // b and c linked → chain: a-b-c

// Tick all down to 0. Each let ticks all vars.
// With cascade: when a expires, b should cascade, then c.
let dummy = 0       // TICK: a 2→1, b 2→1, c 2→1
// All at TTL 1
print a             // a 1→2, b extended by 1 → 2
print b             // b 2→3, a extended → 3, c extended → 2
print c             // c 2→3, b extended → 4

// Now: a=3, b=4, c=3
// Let them all decay without maintenance
let dummy = 0       // TICK: a 3→2, b 4→3, c 3→2
let dummy = 0       // TICK: a 2→1, b 3→2, c 2→1
let dummy = 0       // TICK: a 1→0→EXPIRED!
                     // Cascade: a expired → check share a,b → b expires
                     // b expired → check share b,c → c expires
                     // Chain collapse! All three die at once.
print a
print b
print c
