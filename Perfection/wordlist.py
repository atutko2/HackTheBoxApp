import hashlib
for x in range(1, 1000000001):
  y = "susan_nasus_" + str(x)
  res = hashlib.sha256(y.encode()).hexdigest()
  if x % 1000000 == 0:
    print(x) 
  if 'abeb6f8eb5722b8ca3b45f6f72a0cf17c7028d62a15a30199347d9d74f39023f' == res:
    print(y)
