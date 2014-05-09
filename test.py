import collections
import pickle

def init():
    return "aap"
test = collections.defaultdict(init)
for x in range(10000):
    test[x] += ' noot'
for x in range(5000):
    test[x] += ' mies'
f = open('/Users/dirk/Downloads/test.pic', 'wb')
pickle.dump(test, f, protocol=4)
f.close()
