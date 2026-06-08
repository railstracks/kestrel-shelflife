// Prime checker — non-prime input (91 = 7 * 13)
let n = 91
remember n
let i = 2
remember i

while i < n do
  let q = n / i
  remember q
  let p = q * i
  let r = n - p
  if r == 0 then
    i = n
  end
  forget q
  if i < n then
    i = i + 1
  end
end

if i == n then
  print n
end
