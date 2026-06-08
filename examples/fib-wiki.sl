// Fibonacci — wiki example
// Both loop variables remembered (free reads, no tick cascade)
let a = 1
remember a
let b = 1
remember b
while b < 100 do
  let c = a + b
  a = b
  b = c
  print b
end
