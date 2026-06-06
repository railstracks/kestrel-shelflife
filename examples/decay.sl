// shelflife test: value decay
// x should expire before it can be used

let x = 42       // x TTL 1
let y = 10       // tick: x TTL → 0, y TTL 1
print x          // x has expired
print y          // y is still alive
