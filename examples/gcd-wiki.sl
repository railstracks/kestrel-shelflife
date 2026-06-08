// Euclidean GCD — both variables remembered
let a = 48
remember a
let b = 18
remember b
while a != b do
  if a > b then
    a = a - b
  end
  if b > a then
    b = b - a
  end
end
print a
