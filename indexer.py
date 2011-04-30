#!/usr/bin/env python3.1
"""File containing the Indexer class and some tests for it"""
import os
import re
import marshal
import sys

def immediate_print(string):
    """A function to print and flush the stdout immediately"""
    print(string)
    sys.stdout.flush()

class IllegalCharacter(Exception):
    """An exception for an occurence of a polish character"""
    pass

class Indexer:
    """A class for generating index files and getting posting lists"""
    morfologik = {}
    titles = {}
    document_count = 0

    def __init__(self, index_dir = "index", compressed = False, stemmed = False):
        self.stemmed = stemmed
        self.compressed = compressed
        self.index_dir = self.create_index_directory(index_dir)

    def create_index_directory(self, dirname):
        """Creates the index directory, if it doesn't exist yet"""
        if self.compressed or self.stemmed:
            dirname = dirname + '_'
            if self.compressed:
                dirname = dirname + 'C' 
            if self.stemmed:
                dirname = dirname + 'S'

        if not os.path.isdir(dirname + '/'):
            os.mkdir(dirname + '/')
        return dirname

    def initialize_morfologik(self, morfologik_filename, morfologik_cachefile):
        """Generates morfologic-data dictionary and caches it, restores if it was cached already"""

        immediate_print("loading morfologik")

        if os.path.exists(morfologik_cachefile):
            self.morfologik = Indexer.load_dict(morfologik_cachefile)
            immediate_print("loaded morfologik from the cache")
    
        if self.morfologik == {}:
            immediate_print("regenerating morfologik")
            morfologik_handle = open(morfologik_filename, 'r')
            for line in morfologik_handle:
                forms = line.split(' ')
                forms[-1] = forms[-1].rstrip()
                self.morfologik[forms[0]] = forms[1:]
            Indexer.dump_dict(self.morfologik, morfologik_cachefile)

    def unsorted_index_path(self):
        """Returns path to the unsorted index file"""
        return os.path.join(self.index_dir, 'WORDS')

    def sorted_index_path(self):
        """Returns path to the sorted index file"""
        return os.path.join(self.index_dir, 'WORDS.sorted')

    def titles_path(self):
        """Returns path to the titles info file"""
        return os.path.join(self.index_dir, 'TITLES')

    def titles_dict_path(self):
        """Returns path to the titles dictionary file"""
        return os.path.join(self.index_dir, 'TITLES.marshal')

    def dict_path(self, prefix):
        """Returns path to the apropriate dictionary file for a word"""
        return os.path.join(self.index_dir, prefix + '.marshal')

    def generate_index_file(self, filename):
        """Generates big unsorted index file with the info about all word occurences"""

        self.document_count = 0
        word_regexp = re.compile(r'\w+')

        titles_handle = open(self.titles_path(), 'w')
        file_handle = open(filename, 'r')
        indexfile_handle = open(self.unsorted_index_path(), 'w') 
    
        immediate_print('indexing articles')

        ord_a = ord('a')
        ord_z = ord('z')
        ord_0 = ord('0')
        ord_9 = ord('9')

        for line in file_handle:
            if line[:9] == '##TITLE##':
                if self.document_count % 1000 == 0:
                    immediate_print('%(count)d documents indexed' % {'count': self.document_count})
                self.document_count += 1
                titles_handle.write("%(count)d %(title)s\n" % {'count': self.document_count, 'title': line[10:].strip()})
            else:
                for word in word_regexp.findall(line):
                    bases = self.normalize(word)
                    for base in bases:
                        try:
                            for char in base:
                                ord_char = ord(char)
                                if not ((ord_char >= ord_a and ord_char <= ord_z) or
                                        (ord_char >= ord_0 and ord_char <= ord_9) or
                                        (char in 'ążęźćśóńł')):
                                    raise IllegalCharacter
                            indexfile_handle.write("%(base)s %(count)d\n" % {'base': base, 'count': self.document_count})
                        except IllegalCharacter:
                            pass

    def sort_index_file(self):
        """Sorts the big index file"""
        immediate_print('sorting the index file')

        os.system("LC_ALL=C sort -T. -k1,1 -s " + self.unsorted_index_path() + " > " + self.sorted_index_path())

    def generate_dicts(self):
        """Generates the three letter dictionary files from the big sorted index file"""
        immediate_print('generating dictionaries')
        
        indexfile_handle = open(self.sorted_index_path())
        index_dict = {}
        prefix = ""

        for i, line in enumerate(indexfile_handle):
            if i % 1000000 == 0:
                immediate_print( "%(count)d parsed lines" % {'count': i})
            [key, value] = line.split(' ', 1)
            value = int(value.rstrip())
            
            if key[:3] == prefix:
                if key in index_dict:
                    if index_dict[key][-1] != value:
                        index_dict[key].append(value)
                else:
                    index_dict[key] = [value]
            else:
                if os.path.exists(self.dict_path(prefix)) and prefix != "":
                    immediate_print("ERROR: %(filename)s already exists" % {'filename': self.dict_path(prefix)})
                if self.compressed:
                    Indexer.dump_dict(Indexer.compress_dict(index_dict), self.dict_path(prefix))
                else:
                    Indexer.dump_dict(index_dict, self.dict_path(prefix))

                index_dict.clear()
                index_dict[key] = [value]
                prefix = key[:3]

        if self.compressed:
            Indexer.dump_dict(Indexer.compress_dict(index_dict), self.dict_path(prefix))
        else:
            Indexer.dump_dict(index_dict, self.dict_path(prefix))

    @staticmethod
    def compress_dict(dictionary):#stub
        """Compresses the contents of a dictionary"""
        return dictionary

    @staticmethod
    def decompress_posting(posting):#stub
        """Decompresses the posting list from a dictionary with compressed posting lists"""
        return posting

    @staticmethod
    def differentiate_posting(posting):
        if not posting == []:
            counter = 0
            res = []
            for elem in posting:
                res.append(elem - counter)
                counter = elem
            return res
        else:
            return []

    def dump_titles(self):
        """Dumps titles info into a marshalled file"""
        titles_handle = open(self.titles_path())
        titles_dict = {}
            
        immediate_print("indexing titles")

        for line in titles_handle:
            [key, value] = line.split(' ', 1)
            value = value.rstrip()
            key = int(key)
            titles_dict[key] = value
        
        immediate_print("dumping titles")

        Indexer.dump_dict(titles_dict, self.titles_dict_path())

    @staticmethod
    def dump_dict(dictionary, dict_filename):
        """Dumps a dictionary to a file"""
        dict_handle = open(dict_filename, 'wb')
        marshal.dump(dictionary, dict_handle, 2)
        
    @staticmethod
    def load_dict(dict_filename):
        """Loads a dictionary from a file"""
        dict_handle = open(dict_filename, 'rb')
        return marshal.load(dict_handle)

    def normalize(self, word):
        """Normalizes and possibly stems the word"""
        word = word.lower()
        
        if self.morfologik == {}:
            self.initialize_morfologik('data/morfologik_do_wyszukiwarek.txt', 'data/morfologik.marshal')

        if word in self.morfologik:
            lemated = self.morfologik[word] 
        else:
            lemated = [word]

        if self.stemmed:
            return [Indexer.stem(word) for word in lemated]
        else:
            return lemated
    
    @staticmethod
    def stem(word): #stub
        """Stems the word"""
        return word
    
    def load_titles(self):
        """Loads the titles count info"""

        immediate_print("loading titles from a file")

        filename = self.titles_dict_path()
        self.titles = Indexer.load_dict(filename)
        self.document_count = len(self.titles)

    def get_title(self, article_number):
        """Gets a title from a marshalled file"""
        if self.titles == {}:
            self.load_titles()
        return str(self.titles[article_number])

    def get_posting(self, word):
        """Gets a posting from a marshalled file for a given word"""
        forms = self.normalize(word)
        res = []
        for form in forms:
            filename = self.dict_path(form[:3])
            if os.path.exists(filename):
                prefix_dict = Indexer.load_dict(filename)
                if form in prefix_dict:
                    if self.compressed:
                        res += Indexer.decompress_posting(prefix_dict[form])
                    else:
                        res += prefix_dict[form]
        return sorted(res)


def main():
    """Does some indexer testing"""
    indexer = Indexer()

    #indexer.generate_index_file('data/wikipedia_dla_wyszukiwarek.txt')

    #indexer.sort_index_file()

    #indexer.generate_dicts()

    #indexer.dump_titles()

    print(Indexer.differentiate_posting([2,2,5,8,10]))

if __name__ == "__main__":
    main()
