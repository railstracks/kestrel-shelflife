let a = 1
remember a
let b = 1
remember b
while b < 100 do
  let c = a + b
  print c
  a = b
  b = c
  print b
end
