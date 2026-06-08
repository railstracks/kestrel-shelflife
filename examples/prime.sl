// Prime checker — terminate by setting i = n + 1 when divisor found
let n = 97
remember n
let i = 2
remember i

while i < n do
  let q = n / i
  remember q
  let p = q * i
  let r = n - p
  if r == 0 then
    i = n + 1               // set i beyond n to signal "not prime"
  end
  forget q
  if i < n then
    i = i + 1
  end
end

// If i == n, we exhausted all divisors → prime
// If i == n + 1, we found a divisor → not prime
if i == n then
  print n
end
