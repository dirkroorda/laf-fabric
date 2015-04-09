
# coding: utf-8

# In[1]:

import sys
import collections
import subprocess

from lxml import etree

import laf
from laf.fabric import LafFabric
from etcbc.preprocess import prepare
from etcbc.mql import MQL
fabric = LafFabric()


# In[2]:

API = fabric.load('etcbc4', '--', 'mql', {
    "xmlids": {"node": False, "edge": False},
    "features": ('''
        oid otype monads
        g_word g_word_utf8 g_cons lex 
        typ code function rela det
        book chapter verse label
    ''',''),
    "prepare": prepare,
}, verbose='DETAIL')
exec(fabric.localnames.format(var='fabric'))


# In[3]:

i = 0
for n in NN():
    i += 1
print(i)


# The number of nodes that you see should be ``1441144`` and the number below should have the same value.

# In[4]:

Q = MQL(API)
print('There are {} objects'.format(len(Q.index2node)))


# In[5]:

yesh_query = '''
select all objects where
[book [chapter [verse
[clause
    [clause_atom
        [phrase
            [phrase_atom
                [word lex="JC/" or lex=">JN/"]
            ]
        ]
    ]
]
]]]
'''


# In[10]:

sheaf = Q.mql(yesh_query)


# In[7]:

for x in sheaf.results():
    print(x)
    break


# In[15]:

nresults = 0
n_yesh = 0
n_ein = 0
for ((book, 
      ((chapter, 
        ((verse, 
          ((clause, 
            ((clause_atom, 
              ((phrase, 
                ((phrase_atom, 
                  ((word,),
                  )),
                )),
              )),
            )),
          )),
        )),
      )),
     ) in sheaf.results():
    nresults += 1
    lex = F.lex.v(word)
    if lex == 'JC/':
        n_yesh += 1
    else:
        n_ein += 1
    
    print('{:<15s} {:>3}:{:>3} {:<5s} {:<15s} {:>5}-{:<3} {}-{} {}'.format(
        F.book.v(book), 
        F.chapter.v(chapter), 
        F.verse.v(verse),
        lex,
        F.g_word.v(word),
        F.typ.v(clause),
        F.code.v(clause_atom),
        F.function.v(phrase),
        F.det.v(phrase_atom),
        F.g_word_utf8.v(word),
    ))
print('There are {} results, {} yesh and {} ein'.format(nresults, n_yesh, n_ein))


# In[ ]:



