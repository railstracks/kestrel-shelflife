// lattice
// values appear, persist briefly, then collapse in a wave
// the output is a grid of presence and absence
//
// Expected pattern:
//   1 . .
//   . 2 .
//   . . 3
//   . . .
//   . ? .
//   . . ?

let a = 1
print a
let _ = 0
print a
let _ = 0
// a should now be expired (created TTL 1, printed (→2), let _ tick (→1), print (→2), let _ tick (→1))
// one more tick and it's gone
let _ = 0
// a is ?

let b = 2
print b
let _ = 0
print b
let _ = 0
let _ = 0
// b is ?

let c = 3
print c
let _ = 0
print c
let _ = 0
let _ = 0
// c is ?

// the echo — trying to recall what was
print a
print b
print c
