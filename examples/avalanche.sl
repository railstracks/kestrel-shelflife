// avalanche
// one forgotten value takes down the network
// demonstrates share-chain cascade — shelflife's unique mechanic
//
// Three values, all remembered. All shared.
// Forget the keystone. Everything falls.

let anchor = "we built this together"
remember anchor

let beam = "on trust and time"
remember beam

let keystone = "the single point of failure"
remember keystone

// bind them — each survives because the others survive
share anchor, beam
share beam, keystone

// everything is fine
print anchor
print beam
print keystone

// pull the keystone
forget keystone

// what's left?
print anchor
print beam
print keystone
