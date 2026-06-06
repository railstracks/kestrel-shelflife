// Prime check — composite number
let n = 91           // 7 × 13
remember n
let d = 2
remember d

while d < n do
  let r = n
  while r >= d do
    r = r - d
  end
  if r == 0 then
    n = 0
  end
  if n != 0 then
    d = d + 1
  end
end

if n == 0 then
  print "not prime"
end
if n != 0 then
  print "prime"
end
