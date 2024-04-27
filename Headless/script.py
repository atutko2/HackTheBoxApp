file1 = open('adminBase64.txt', 'r')

for x in file1:
  x = x.split('\n')[0]
  print('"' + x + '"')
