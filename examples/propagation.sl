// shelflife test: unknown propagation
// If x expires, everything built from x becomes unknown

let x = 10       // TTL 1
let y = 20       // tick: x TTL → 0, y TTL 1
let z = x + y    // x is expired → z = ?
print z          // prints ?
print y          // y is still alive
