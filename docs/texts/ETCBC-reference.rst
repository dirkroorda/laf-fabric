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
The ETCBC has a special way to transcribe Hebrew characters into latin characters.
Sometimes it is handier to work with transcriptions, because some applications do not render texts with mixed writing directions well.

In *etcbc.lib* there is a conversion tool. This is how it works::

    from etcbc.lib import Transcription

    tr = Transcription()

    t = 'DAF DAC'
    h = tr.hebrew(t)
    tb = tr.trans(h)

    print("{}\n{}\n{}".format(t, h, tb))

``hebrew(word)`` maps from transcription to Hebrew characters, ``trans(word)`` does the opposite.

There are some points to note:

* if characters to be mapped are not in the domain of the mapping, they will be left unchanged.
* there are two versions of the shin, each consists of two combined unicode characters.
  Before applying the mappings, these characters will be combined into a single character.
  After applying the mapping ``hebrew()``, these characters will be *always* decomposed.



Node order
==========
The module ``etcbc.preprocess`` takes care of preparing a table that codes the optimal node order for working with ETCBC data. 
The API deals with several aspects of task processing.

Usage::

    from etcbc.preprocess import prepare

    fabric.load('bhs3', '--', 'trees', {
        ...
        "prepare": prepare,
    }

Here is how it works. The example is that of adding additional order to the nodes
based on the informal embedding levels between books, chapters, sentences, clauses etc.

Suppose you are working with a specific resource, say the ETCBC Hebrew Text Database.
Probably there is already a package *etcbc* to streamline the tasks relevant to this resource.
To this package you can add a module, say *preprocess.py* in which you can define
an additional sort order on nodes.
Here is the actual contents of *etcbc.preprocess* in this distribution::

    import collections
    import array

    def node_order(API):
        '''Creates a form based on the information passed when creating this object.'''

        API['fabric'].load_again({"features": {"shebanq": {"node": ["db.otype,minmonad,maxmonad",]}}}, add=True)
        msg = API['msg']
        F = API['F']
        NN = API['NN']
        object_rank = {
            'book': -4,
            'chapter': -3,
            'verse': -2,
            'half_verse': -1,
            'sentence': 1,
            'sentence_atom': 2,
            'clause': 3,
            'clause_atom': 4,
            'phrase': 5,
            'phrase_atom': 6,
            'subphrase': 7,
            'word': 8,
        }

        def etcbckey(node):
            return (int(F.minmonad.v(node)), -int(F.maxmonad.v(node)), object_rank[F.otype.v(node)])

        nodes = sorted(NN(), key=etcbckey)
        return array.array('I', nodes)

    def node_order_inv(API):
        make_array_inverse = API['make_array_inverse']
        data_items = API['data_items']
        return make_array_inverse(data_items['zG00(node_sort)'])

    prepare = collections.OrderedDict((
        ('zG00(node_sort)', (node_order, __file__, True, 'etcbc')),
        ('zG00(node_sort_inv)', (node_order_inv, __file__, True, 'etcbc')),
    ))


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

Usage::

    from etcbc.annotating import GenForm

More info: 
`notebook annotating <http://nbviewer.ipython.org/github/ETCBC/laf-fabric-nbs/blob/master/annotating.ipynb>`_

Feature documentation
=====================
The module ``etcbc.featuredoc`` generates overviews of all available features in the main source, including information of their values,
how frequently they occur, how many times they are filled in with (un)defined values.
It can also look up examples in the main data source for you.

Usage::

    from etcbc.featuredoc import FeatureDoc

More info:
`notebook feature-doc <http://nbviewer.ipython.org/github/ETCBC/laf-fabric-nbs/blob/master/feature-doc.ipynb>`_

MQL
===
The module ``etcbc.mql`` lets you fire mql queries to the corresponding Emdros database, and process the results with LAF-Fabric.
More info over what MQL, EMDROS are, and how to use it, is in 
`notebook mql <http://nbviewer.ipython.org/github/ETCBC/laf-fabric-nbs/blob/master/mql.ipynb>`_
