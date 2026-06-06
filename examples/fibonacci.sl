// shelflife test: fibonacci with attention management

let a = 0
remember a
let b = 1
remember b

while b < 1000 do
  let c = a + b
  a = b
  b = c
  print b
end
