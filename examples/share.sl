// shelflife: share mechanic
// Shared variables maintain each other but fall together

let a = 10
remember a        // slot 1
let b = 20
remember b        // slot 2

share a, b        // a and b are now bound

print a           // extends a AND b
print b           // extends b AND a

forget a          // cascades: b also expires!

print b           // b is expired (shared fate)
