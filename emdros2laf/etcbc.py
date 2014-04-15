import sys
import codecs
import collections

from .mylib import *

class Etcbc:
    ''' Knows the ETCBC data format.

    All ETCBC knowledge is stored in a file that describes objects, features and values.
    These are many items, and we divide them in parts and subparts.
    We have a parts for monads, sections and linguistic objects.
    When we generate LAF files, they may become unwieldy in size.
    That is why we also divide parts in subparts.
    Parts correspond to sets of objects and their features.
    Subparts correspond to subsets of objects and or subsets of features.
    N.B. It is "either or": 
    either 

    * a part consists of only one object type, and the subparts
      divide the features of that object type

    or

    * a part consists of multiple object types, and the subparts
      divide the object types of that part. If an object type belongs to
      a subpart, all its features belong to that subpart too.

    In our case, the part 'monad' has the single object type, and its features
    are divided over subparts.
    The part 'lingo' has object types sentence, sentence_atom, clause, clause_atom,
    phrase, phrase_atom, subphrase, word. Its subparts are a partition of these object
    types in several subsets.
    The part 'section' does not have subparts.
    Note that an object type may occur in multiple parts: consider 'word'.
    However, 'word' in part 'monad' has all non-relational word features, but 'word' in part 'lingo'
    has only relational features, i.e.features that relate words to other objects.

    The Etcbc object stores the complete information found in the Etcbc config file
    in a bunch of data structures, and defines accessor functions for it.

    The feature information is stored in the following dictionaries:

    (Ia) part_info[part][subpart][object_type][feature_name] = None
    
        Stores the organization of individual objects and their features in parts and subparts.
        NB: object_types may occur in multiple parts.

    (Ib) part_object[part][object_type] = None
    
        Stores the set of object types of parts

    (Ic) part_feature[part][object_type][feature_name] = None
    
        Stores the set of features types of parts

    (Id) object_subpart[part][object_type] = subpart
    
        Stores the subpart in which each object type occurs, per part

    (II) object_info[object_type] = [attributes]
    
        Stores the information on objects, except their features and values.

    (III) feature_info[object_type][feature_name] = [attributes]
    
        Stores the information on features, except their values.

    (IV) value_info[object_type][feature_name][feature_value] = [attributes]
    
        Stores the feature value information

    (V) reference_feature[feature_name] = True | False
    
        Stores the names of features that reference other object. 
        The feature 'self' is an example. But we skip this feature. 
        'self' will get the value False, other features, such as mother and parents get True

    (VI) annotation_files[part][subpart] = (ftype, medium, location, requires, annotations, is_region)
    
        Stores information of the files that are generated as the resulting LAF resource
    
    The files are organized by part and subpart.
    Header files and primary data files are in part ''.
    Other files may or may not contain annotations. If not, they only contain regions. Then is_region is True.

      ftype
        the file identifier to be used in header files
      medium
        text or xml
      location
        the last part of the file name.
        All file names can be obtained by appending location after the absolute path followed by a common prefix.
      requires
        the identifier of a file that is required by the current file
      annotations
        the annotation labels to be declared for this file
    
    The feature information file contains lines with tab-delimited fields (only the starred ones are used):
      0*           1*            2*          3*          4*             5*          6          7*           8            9           10    11*   12*
      object_type, feature_name, defined_on, etcbc_type, feature_value, isocat_key, isocat_id, isocat_name, isocat_type, isocat_def, note, part, subpart
      0            1             2           3           4              5                      6                                           7     8
    
    '''
    cfg= None

    object_info = {}
    feature_info = {}
    value_info = {}
    part_info = {}
    object_subpart = {}
    part_object = collections.defaultdict(lambda: {})
    part_feature = collections.defaultdict(lambda: {})
    reference_feature = {}

    def __init__(self, cfg):
        ''' Initialization is: reading the excel sheet with feature information.

        The sheet should be in the form of a tab-delimited text file.

        There are columns with:
            ETCBC information:
                object_type, feature_name, also_defined_on, type, value.
            ISOcat information
                key, id, name, type, definition, note
            LAF sectioning
                part, subpart

        See the list of columns above.
                
        So the file gives essential information to map objects/features/values to ISOcat data categories.
        It indicates how the LAF output can be chunked in parts and subparts.
        '''

        self.cfg = cfg

        file = cfg.env['feature_info']
        file_handle = codecs.open(file, encoding = 'utf-8')
        line_number = 0

# the following fields are hierarchical : part, subpart, object_type, feature_name, etcbc_type
# they may inherit from one line to the next, and when one field changes, others have to be reset
# For each input line, we collect them in the list this_fields, and we maintain current values in cur_fields

        cur_part, cur_subpart, cur_object_type, cur_feature_name, cur_etcbc_type = '', '', '', '', ''

        for line in file_handle:
            line_number += 1

# The first two lines in the feature info file are header lines. We skip them

            if line_number <= 2:
                continue

            all_fields = fillup(13, '', line.rstrip().split("\t"))
            used_fields = all_fields[0:6] + all_fields[7:8] + all_fields[11:13]

            object_type, feature_name, defined_on, etcbc_type, feature_value, isocat_key, isocat_name, part, subpart = used_fields

            object_atts = [isocat_key, isocat_name]
            feature_atts = [defined_on, etcbc_type, isocat_key, isocat_name]
            value_atts = [etcbc_type, isocat_key, isocat_name]

            this_fields = [part, subpart, object_type, feature_name, etcbc_type]

# Reset parts of cur_fields when a hierarchically higher part changes
            if object_type != '':
                cur_feature_name = ''; 
                cur_etcbc_type = ''; 
            if feature_name != '':
                cur_etcbc_type = ''; 
            if part != '':
                cur_subpart = ''; 

            cur_fields = [cur_part, cur_subpart, cur_object_type, cur_feature_name, cur_etcbc_type]

# For fields that are empty on the current line, use the value saved in cur_fields
            cur_part, cur_subpart, cur_object_type, cur_feature_name, cur_etcbc_type = map(lambda c,t: t if t != '' else c, cur_fields, this_fields) 

# Identify the reference features

            if cur_etcbc_type == 'reference':
                self.reference_feature[cur_feature_name] = cur_feature_name not in cfg.annotation_skip 

# Add features to the (sub)part structure
            self.part_object[cur_part][cur_object_type] = None
            if cur_feature_name != '':
                if cur_object_type not in self.part_feature[cur_part]:
                    self.part_feature[cur_part][cur_object_type] = collections.defaultdict(lambda: {})
                self.part_feature[cur_part][cur_object_type][cur_feature_name] = None

            this_dict = self.part_info
            if cur_part not in this_dict:
                this_dict[cur_part] = {}

            this_dict = this_dict[cur_part]
            if cur_subpart not in this_dict:
                this_dict[cur_subpart] = {}

            this_dict = this_dict[cur_subpart]
            if cur_object_type not in this_dict:
                this_dict[cur_object_type] = {}

            if cur_feature_name != '':
                this_dict = this_dict[cur_object_type]
                if cur_feature_name not in this_dict:
                    this_dict[cur_feature_name] = None

            this_dict = self.object_subpart
            if cur_part not in this_dict:
                this_dict[cur_part] = {}
            this_dict[cur_part][cur_object_type] = cur_subpart

# Add object info
            this_dict = self.object_info
            if cur_object_type not in this_dict:
                this_dict[cur_object_type] = object_atts

# Add feature info
            this_dict = self.feature_info
            if cur_object_type not in this_dict:
                this_dict[cur_object_type] = {}

            if cur_feature_name != '':
                this_dict = this_dict[cur_object_type]
                if cur_feature_name not in this_dict:
                    this_dict[cur_feature_name] = feature_atts

# Add value info
            this_dict = self.value_info
            if cur_object_type not in this_dict:
                this_dict[cur_object_type] = {}

            if cur_feature_name != '':
                this_dict = this_dict[cur_object_type]
                if cur_feature_name not in this_dict:
                    this_dict[cur_feature_name] = {}

                if feature_value != '':
                    this_dict = this_dict[cur_feature_name]
                    if feature_value not in this_dict:
                        this_dict[feature_value] = value_atts

        file_handle.close()

# create directories and queries if we have to query the EMDROS database for data
        if self.cfg.flag('raw'):
            run('mkdir -p ' + cfg.env['raw_emdros_dir'])
            run('mkdir -p ' + cfg.env['query_dst_dir'])
            for part in self.part_list():
                self.make_query_file(part)

# Now come the accessor functions for the datastructures created upon initialization

    def part_list(self):
        ''' Answers: which parts are there?
        '''
        return sorted(self.part_info.keys())

    def subpart_list(self, part):
        ''' Answers: which subparts are there in a part?
        '''
        return sorted(self.part_info[part].keys())

    def object_list_all(self):
        ''' Answers: which object types are there?
        '''
        return sorted(self.object_info.keys())

    def object_list_part(self, part):
        ''' Answers: which objects are there in all subparts of a part?
        '''
        return sorted(self.part_object[part].keys())

    def the_subpart(self, part, object_type):
        ''' Answers: which subpart of part contains this object type?
        '''
        return self.object_subpart[part][object_type]

    def object_list(self, part, subpart):
        ''' Answers: which objects are there in a subpart of a part?
        '''
        return sorted(self.part_info[part][subpart].keys())

    def feature_list(self, object_type):
        ''' Answers: which features belong to an object type?
        '''
        return sorted(self.feature_info[object_type].keys())

    def feature_list_part(self, part, object_type):
        ''' Answers: which features belong to an object type, and also in a part and exclude the features to be skipped?
        '''
        return sorted([x for x in self.part_feature[part][object_type] if x not in self.cfg.annotation_skip])

    def feature_list_subpart(self, part, subpart, object_type):
        ''' Answers: which features belong to an object type, a part and subpart, and also in a part and exclude the features to be skipped?
        '''
        return sorted([x for x in self.part_info[part][subpart][object_type] if x not in self.cfg.annotation_skip])

    def value_list(self, object_type, feature_name):
        ''' Answers: which values belong to a features of an object type?
        '''
        return sorted(self.value_info[object_type][feature_name].keys())

    def object_atts(self, object_type):
        ''' Returns a tuple of object attributes, corresponding with the columns in the feature excel sheet.
        
        The Etcbc column (object type) is missing, since they are given as arguments.
        The LAFcolumns are not included.
        The attributes returned are:
         
            isocat_key, isocat_name
        '''
        return self.object_info[object_type]

    def feature_atts(self, object_type, feature_name):
        ''' Returns a tuple of feature attributes, corresponding with the columns in the feature excel sheet.
        
        The Etcbc columns (object type, feature name) are missing, since they are given as arguments.
        The LAFcolumns are not included.
        The attributes returned are:
         
            defined_on, etcbc_type, isocat_key, isocat_name
        '''
        return self.feature_info[object_type][feature_name]

    def value_atts(self, object_type, feature_name, feature_value):
        ''' Returns a tuple of value attributes, corresponding with the columns in the feature excel sheet.
        
        The Etcbc columns (object type, feature name, feature_value) are missing, since they are given as arguments
        The LAFcolumns are not included.
        The attributes returned are:
         
            etcbc_type, isocat_key, isocat_name
        '''
        return self.value_info[object_type][feature_name][feature_value]

    def list_ref_noskip(self):
        ''' List the reference features that should not be skipped
        '''
        return sorted([x for x in self.reference_feature if self.reference_feature[x]])

    def is_ref_skip(self, feature_name):
        ''' Tests if the feature_name is a reference feature that should be skipped
        '''
        return feature_name in self.reference_feature and not self.reference_feature[feature_name]

    def raw_file(self, part):
        ''' Give the name of the file with raw emdros output for part
        '''
        return self.cfg.parts[part]['raw_text']

    def check_raw_files(self, part):
        ''' Generate the file with raw emdros output by executing a generated mql query.
        This query has been generated during initialization.
        Only when there is a command line flag present that tells to do this
        '''
        if not self.cfg.flag('raw'):
            return
        print("INFO: BEGIN Generate raw MQL output from EMDROS")

# execute the generated mql query
        run('mql -b s3 -d {source} --console {query} > {raw}'.format(
                source = self.cfg.env['source_data'],
                query = self.cfg.parts[part]['query_file'],
                raw = self.cfg.parts[part]['raw_text']
            ))

        print("INFO: END Generate raw MQL output from EMDROS")

# TASK RAW (generate mql export queries)
#
# Every part (monad, section, lingo) consists of a selection of object types and feature names.
# This function generates the mql query that extracts exactly the objects of those types, and 
# retrieves their features in so far as they belong to this part

    def make_query_file(self, part):
        ''' Generate an emdros query file to extract the raw data for part from the emdros database.
        '''
        template = '''
GET OBJECTS HAVING MONADS IN ALL
	[{object} GET
    	{features}
	]
GO
'''
        query_text = ''
        for object_type in self.object_list_part(part):
            copy = template.format(
                object = object_type,
                features = ",\n\t\t".join(self.feature_list_part(part, object_type)),
            )
            query_text += copy

        file_handle = codecs.open(self.cfg.parts[part]['query_file'], "w", encoding = 'utf-8')
        file_handle.write(query_text)
        file_handle.close()


