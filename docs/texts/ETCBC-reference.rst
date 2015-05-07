ETCBC Reference
###############

What is ETCBC
=============
The *etcbc* package has modules that go beyond *laf*.
They utilize extra knowledge of the specific LAF resource which is the ETCBC Hebrew Text Database.
They make available a better ordering of nodes, add more ways of querying the data, and ways of creating new annotations.
There is also a solution for the problem of getting relevant context around a node.
For example, if you do a walk through phrases, you want to be able to the clauses that contain the phrases that you iterate over,
or to siblings of it.

Most of the functionality is demonstrated in dedicated notebooks. This text is only a rough overview.

Layers
======
The ``L`` (*layer*) part of the API enables you to find objects that are embedded in other objects and vice versa.
It makes use of the ETCBC object types ``book``, ``chapter``, ``verse``, ``half_verse``, ``sentence``, ``sentence_atom``,
``clause``, ``clause_atom``, ``phrase``, ``phrase_atom``, ``subphrase``, ``word``.
An object of a certain type may contain objects of types following it, and is contained by objects of type preceding it.

By means of ``L`` you can go from an object to any object that contains it, and you can get lists of objects contained in it.
This is how it works. You have to import the ``prepare`` module::

    from etcbc.preprocess import prepare

and say in your load instructions::

    ``'prepare': prepare``
    
Then you can use the following functions::

    L.u(otype, node)
    L.d(otype, node)

``L.u`` (up in the hierarchy) gives you the object of type ``otype`` that contains it (in the ETCBC data there is at most one such an object).
If there is no such object, it returns ``None``.

``L.d`` (down in the hierarchy) gives you all objects of type ``otype`` that are contained in it as a list in the natural order.
If there are no such objects you get ``None``.

Examples (if ``phr`` is a node with object type ``phrase``)::

    b = L.u('book', phr)                  # the book node in which the node occurs
    F.book.v(b)                           # the name of that book

    b = F.code.v(L.u('clause_atom', phr)) # the *clause_atom_relationship* of the clause_atom of which the phrase is a part

It is now easy to get the full text contained in any object, e.g. the phrase ``phr``::

    ''.join('{}{}'.format(F.g_word_utf8.v(w), F.trailer_utf8.v(w)) for w in L.d(phr)) 

Node order
==========
The module ``etcbc.preprocess`` takes care of preparing a table that codes the optimal node order for working with ETCBC data. 

It orders the nodes in a way that combines the left-right ordering with the embedding ordering.
Left comes before right, and the embedder comes before the embedded.

More precisely: if we want to order node *a* and *b*, consider their monad sets *ma* and *mb*, and their object types *ta* and *tb*.
The object types have ranks, going from a low rank for books, to higher ranks for chapters, verses, half_verses, sentences, sentence_atoms,
clauses, clause_atoms, phrases, phrase_atoms, subphrases and words.

In the ETCBC data every node has a non-empty set of monads.

If *ma* is equal to *mb* and *ta* is equal to *tb*, then *a* and *b* have the same object type,
and cover the same monads, and in the etcbc that implies 
that *a* and *b* are the same node.

If *ma* is equal to *mb*, then if *ta* is less than *tb*, *a* comes before *b* and vice versa.

If *ma* is a proper subset of *mb*, then *a* comes *after* *b*, and vice versa.

If none of the previous conditions hold, then *ma* has monads not belonging to *mb* and vice versa.
Consider the smallest monads of both difference sets: *mma* = *min(ma-mb)* and *mmb = min(mb-ma)*.
If *mma* < *mmb* then *a* comes before *b* and vice versa.
Note that *mma* cannot be equal to *mmb*.

Back to your notebook. Say::

    from etcbc.preprocess import prepare

    processor.load('your source', '--', 'your task',
        {
            "xmlids": {"node": False, "edge": False},
            "features": { ... your features ...},
            "prepare": prepare,
        }
    )

then the following will happen:

* LAF-Fabric checks whether certain data files that define the order between nodes exist next to the binary compiled data, and whether these files
  are newer than your module *preprocess.py*.
* If so, it loads these data files quickly from disk.
* If not, it will compute the node order and write them to disk.  This may take some time! Then it replaces the *dumb* standard
  ordering by the *smart* ETCBC ordering.
* Likewise, it looks for computed files with the embedding relationship, and computes them if necessary.
  This takes even more time!

This data is only loaded
if you have done an import like this::

    from etcbc.preprocess import prepare

and if you have::

    'prepare': prepare

in your load instructions,

Transcription
=============
Hebrew
------
The ETCBC has a special way to transcribe Hebrew characters into latin characters.
Sometimes it is handier to work with transcriptions, because some applications do not render texts with mixed writing directions well.

In *etcbc.lib* there is a conversion tool. This is how it works::

    from etcbc.lib import Transcription

    tr = Transcription()

    t = 'DAF DAC'
    h = tr.to_hebrew(t)
    tb = tr.from_hebrew(h)

    print("{}\n{}\n{}".format(t, h, tb))

``to_hebrew(word)`` maps from transcription to Hebrew characters, ``from_hebrew(word)`` does the opposite.

There are some points to note:

* if characters to be mapped are not in the domain of the mapping, they will be left unchanged.
* there are two versions of the shin, each consists of two combined unicode characters.
  Before applying the mappings, these characters will be combined into a single character.
  After applying the mapping ``hebrew()``, these characters will be *always* decomposed.
* up till now we have only transcription conversions for *consonantal Hebrew*.

Syriac
------
We have a transcription for consonantal Syriac. The interface is nearly the same as for Hebrew, but now use::

    to_syriac(word)
    from_syriac(word)

Trees
=====
The module *etcbc.trees* gives you several relationships between nodes:
*parent*,  *children*, *sisters*, and *elder_sister*.::

    from etcbc.trees import Tree

    tree = Tree(API, otypes=('sentence', 'clause', 'phrase', 'subphrase', 'word'), 
        clause_type='clause',
        ccr_feature='rela',
        pt_feature='typ',
        pos_feature='sp',
        mother_feature = 'mother',
    )
    ccr_class = {
        'Adju': 'r',
        'Attr': 'r',
        'Cmpl': 'r',
        'CoVo': 'n',
        'Coor': 'x',
        'Objc': 'r',
        'PrAd': 'r',
        'PreC': 'r',
        'Resu': 'n',
        'RgRc': 'r',
        'Spec': 'r',
        'Subj': 'r',
        'NA':   'n',
    }
    
    tree.restructure_clauses(ccr_class)

    results = tree.relations()
    parent = results['rparent']
    sisters = results['sisters']
    children = results['rchildren']
    elder_sister = results['elder_sister']

When the ``Tree`` object is constructed, the monadset-embedding relations that exist between the relevant objects, will be used
to construct a tree.
A node is a parent of another node, which is then a child of that parent, if the monad set of the child is contained in the
monad set of the parent, and if there are not intermediate nodes (with respect to embedding) between the parent and the child.
So this *parent* relationship defines a *tree*, and the *children* relationship is just the inverse of the *parent* relationship.
Every node has at most 1 parent, but nodes may have multiple children.
If two nodes have the same monad set, then the object type of the nodes determines if one is a parent and which one that is.
A sentence can be parent of a phrase, but not vice versa.

It can not be the case that two nodes have the same monad set and the same object type.

You can customize your trees a little bit, by declaring a list of object types that you want to consider.
Only nodes of thos object types will enter in the parent and children relationships.
You should specify the types corresponding to the ranking of object types that you want to use.
If you do not specify anything, all available nodes will be used and the ranking is the default ranking, given in 
*etcbc.lib.object_rank*.

There is something curious going on with the *mother* relationship, i.e. the relationship that links on object to another on which it is
linguistically dependent. In the trees just constructed, the mother relationship is not honoured, and so we miss several kinds of
linguistic embeddings.

The function ``restructure_clauses()`` remedies this. If you want to see what it going on, consult the 
`trees_etcbc4 notebook <http://nbviewer.ipython.org/github/ETCBC/laf-fabric-nbs/blob/master/trees/trees_etcbc4.ipynb>`_.

Annotating
==========
The module ``etcbc.annotating`` helps you to generate data entry forms and translate filled in forms into new annotations in LAF format,
that actually refer to nodes and edges in the main ETCBC data source.

There is an example notebook that uses this module for incorporating extra data (coming from so-called *px* files) into the LAF resource.
See *Extra Data* below.

Extra Data
==========
The ETCBC data exists in so-called *px* files, from which the EMDROS databases are generated.
Some *px* data did not made it too EMDROS, hence this data does not show up in LAF.
Yet there might be useful data in the *px*. The module **etcbc.extra** helps to pull that data in, and delivers it in the form
of an extra annotation package.

You can also use this module to add other kinds of data.
You only need to write a function that delivers the data in the right form, and then *extra* turns it into a valid annotation set.

Usage::

    from etcbc.extra import ExtraData

More info:
`notebook para from px <http://nbviewer.ipython.org/github/ETCBC/laf-fabric-nbs/blob/master/extradata/para%20from%20px.ipynb>`_


Feature documentation
=====================
The module ``etcbc.featuredoc`` generates overviews of all available features in the main source, including information of their values,
how frequently they occur, how many times they are filled in with (un)defined values.
It can also look up examples in the main data source for you.

Usage::

    from etcbc.featuredoc import FeatureDoc

More info:
`notebook feature-doc <http://nbviewer.ipython.org/github/ETCBC/laf-fabric-nbs/blob/master/featuredoc/feature-doc.ipynb>`_

MQL
===
The module ``etcbc.mql`` lets you fire mql queries to the corresponding Emdros database, and process the results with LAF-Fabric.
More info over what MQL, EMDROS are, and how to use it, is in 
`notebook mql <http://nbviewer.ipython.org/github/ETCBC/laf-fabric-nbs/blob/master/querying/mql.ipynb>`_.

On the Mac and in Linux it runs out of the box, assuming Emdros is installed in such a way that the command to run MQL is ``/usr/local/bin/mql``.
If that is not the case, or if you work on windows, you should manually change the first line of *mql.py*.
Its default value is::

    MQL_PROC = '/usr/local/bin/mql'

and on windows is should become something like::

    MQL_PROC = 'c:\\Program Files (x86)\\Emdros\\Emdros 3.4.0\\bin\\mql'

(check your system).
After modifying this file, you should go to your *laf-fabric* directory and run again::

    python setup.py install

Regrattably, this must be repeated when you update laf-fabric from Github.
