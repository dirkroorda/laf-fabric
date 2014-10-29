ETCBC Reference
###############

What is ETCBC
=============
The *etcbc* package has modules that go beyond *laf*.
They utilize extra knowledge of the specific LAF resource which is the ETCBC Hebrew Text Database.
They make available a better ordering of nodes, add more ways of querying the data, and ways of creating new annotations.

Most of the functionality is demonstrated in dedicated notebooks. This text is only a rough overview.

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

Node order
==========
The module ``etcbc.preprocess`` takes care of preparing a table that codes the optimal node order for working with ETCBC data. 

It orders the nodes in a way that combines the left-right ordering with the embedding ordering.
Left comes before right, and the embedder comes before the embedded.

More precisely: if we want to order node *a* and *b*, consider their monad sets *ma* and *mb*, and their object types *ta* and *tb*.
The object types have ranks, going from a low rank for books, to higher ranks for chapters, verses, half_verses, sentences, sentence_atoms,
clauses, clause_atoms, phrases, phrase_atoms, subphrases and words.

In the etcbc data every node has a non-empty set of monads.

If *ma* is equal to *mb* and *ta* is equal to *mb*, then *a* and *b* have the same object type, and cover the same monads, and in the etcbc that implies 
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

* LAF-Fabric checks whether file *Z/etcbc/zG00(node_sort)* and *Z/etcbc/zG00(node_sort_inv)* exist next to the binary compiled data, and whether these files
  are newer than your module *preprocess.py*.
* If so, it loads this data from disk.
* If not, it will execute the *node_order* function in *preprocess.py*, which sorts the nodes more completely than LAF-Fabric can, and write this data to disk
  in *Z/etcbc/zG00(node_sort)* and it also computes *node_order_inv* in order to get an inverse: *Z/etcbc/zG00(node_sort_inv)*.

Note that these functions can be programmed using the API of LAF-Fabric itself. Preparing data always takes place after full loading.
The prepared data will be subsequently loaded.

The *True* component in the dictionary *prepare* tells LAF-Fabric to use this data **instead of previously compiled data**.
In this case, there should be a data item keyed with ``mG00(node_sort)`` in the already loaded data (otherwise you get an error).
In fact, LAF-Fabric uses a data item with this name to help *NN()* iterate over its nodes in a convenient order.
So you have effectively supplanted LAF-Fabric's standard ordering of the nodes by your own ordering, which makes better use
of the particular structure of this data. 

If you had said ``False`` instead, no attempt of overriding existing data would have been made. If you want to use this data,
you can refer to it by:: 

        API['data_items']['zG00(node_sort)']

The *etcbc* directory corresponds to the ``etcbc`` component in the dictionary *prepare*.
In this way, different modules may keep their computed data separate from each other.
Computed data is always separated from the previously compiled data.

This data is only loaded if you have ``'prepare': etcbc.preprocess.prepare`` in your load instructions,
or if you have done an import like this::

    from etcbc.preprocess import prepare

then ``'prepare': prepare`` suffices.

In order to know the data that LAF-Fabric uses natively, look at the list in the ``names`` module.

First of all, getting information out of the LAF resource.
But there are also methods for writing to and reading from task-related files and
for progress messages.

Finally, there is information about aspects of the organization of the LAF information,
e.g. the sort order of nodes.

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
`notebook mql <http://nbviewer.ipython.org/github/ETCBC/laf-fabric-nbs/blob/master/querying/mql.ipynb>`_
