bmonad = 100
monads = '100-110,115,118,130-150'
#monads = F.monads.v(node)
rangesi = [[int(a)-bmonad for a in r.split('-')] for r in monads.split(',')] 
monadss = ','.join('-'.join(str(a) for a in r) for r in rangesi)
print(monadss)
