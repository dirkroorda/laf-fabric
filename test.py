import sys
test = {}
print(type(test))
if type(test) == list or type(test) == dict:
    print("YES")
else:
    print("NO: {}".format(type(test)))
