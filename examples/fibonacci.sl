// Naive fibonacci — fails because loop variables are NOT remembered
// This demonstrates what happens without attention management
let a = 1
let b = 1
while b < 100 do
  let c = a + b
  print c
  a = b
  b = c
end
