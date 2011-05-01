#!/usr/bin/env python3.1
"""File containing the Indexer class and some tests for it"""
import os
import re
import marshal
import sys
import gzip

def immediate_print(string):
    """A function to print and flush the stdout immediately"""
    print(string)
    sys.stdout.flush()

class Indexer:
    """A class for generating index files and getting posting lists"""
    morfologik = {}
    titles = []
    document_count = 0

    def __init__(self, index_dir = "index", compressed = False, stemmed = False):
        self.stemmed = stemmed
        self.compressed = compressed
        self.index_dir = index_dir

    def load_index(self):
        self.load_morfologik()
        self.load_titles()

    def create_index(self, data_file, morfologik_file):
        if not os.path.exists(self.index_dir):
            os.mkdir(self.index_dir)

        self.initialize_morfologik(morfologik_file)
        self.generate_index_file(data_file)
        self.sort_index_file()
        self.generate_dicts()
        self.dump_titles()
        self.dump_morfologik()

    def initialize_morfologik(self, morfologik_filename):
        """Generates morfologic-data dictionary and caches it, restores if it was cached already"""
        if self.morfologik == {}:
            immediate_print("initializing morfologik")
            morfologik_handle = open(morfologik_filename, 'r')
            for line in morfologik_handle:
                forms = line.rstrip().split(' ')
                self.morfologik[forms[0]] = forms[1:]

    def load_morfologik(self):
        """Loads dumpef morfologik."""
        immediate_print("loaded morfologik from the cache")
        self.morfologik = self.load(self.morfologik_path())

    def dump_morfologik(self):
        immediate_print("dumping morfologik")
        self.dump(self.morfologik, self.morfologik_path())

    def unsorted_index_path(self):
        """Returns a path to the unsorted index file"""
        return os.path.join(self.index_dir, 'WORDS')

    def sorted_index_path(self):
        """Returns a path to the sorted index file"""
        return os.path.join(self.index_dir, 'WORDS.sorted')

    def titles_path(self):
        """Returns a path to the titles info file"""
        if self.compressed:
            return os.path.join(self.index_dir, 'TITLES.marshal.gz')
        else:
            return os.path.join(self.index_dir, 'TITLES.marshal')

    def morfologik_path(self):
        """Returns a path to the morfologik dictionary file"""
        if self.compressed:
            return os.path.join(self.index_dir, 'MORFOLOGIK.marshal.gz')
        else:
            return os.path.join(self.index_dir, 'MORFOLOGIK.marshal')

    def dict_path(self, prefix):
        """Returns path to the apropriate dictionary file for a word"""
        if self.compressed:
            return os.path.join(self.index_dir, '%s.marshal.gz' % prefix)
        else:
            return os.path.join(self.index_dir, '%s.marshal' % prefix)

    def generate_index_file(self, filename):
        """Generates big unsorted index file with the info about all word occurences"""

        self.document_count = 0
        word_regexp = re.compile(r'\w+')
        file_handle = open(filename, 'r')
        indexfile_handle = open(self.unsorted_index_path(), 'w') 
    
        illegal_char_regexp = re.compile(r'[^1234567890qwertyuiopasdfghjklzxcvbnmęóąśłżźćń]')

        for line in file_handle:
            if line[:9] == '##TITLE##':
                if self.document_count % 1000 == 0:
                    immediate_print('%(count)d documents indexed' % {'count': self.document_count})
                self.document_count += 1
                self.titles.append(line[10:].strip())
            else:
                for word in word_regexp.findall(line):
                    bases = self.normalize(word)
                    for base in bases:
                        if illegal_char_regexp.search(base):
                            continue
                        indexfile_handle.write("%(base)s %(count)d\n" % {'base': base, 'count': self.document_count})

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
                self.dump(index_dict, self.dict_path(prefix))

                index_dict.clear()
                index_dict[key] = [value]
                prefix = key[:3]

        self.dump(index_dict, self.dict_path(prefix))

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
        """Differentiaties posting lists"""
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
        self.dump(self.titles, self.titles_path())

    def dump(self, obj, filename):
        """Dumps an object to a file"""
        if self.compressed:
            handle = gzip.open(filename, 'wb')
        else:
            handle = open(filename, 'wb')
        marshal.dump(obj, handle, 2)

    def load(self, filename):
        """Loads an object from a file"""
        if self.compressed:
            handle = gzip.open(filename, 'rb')
        else:
            handle = open(filename, 'rb')
        return marshal.load(handle)

    def normalize(self, word):
        """Normalizes and possibly stems the word"""
        word = word.lower()
        
        if word in self.morfologik:
            lemated = self.morfologik[word] 
        else:
            lemated = [word]

        if self.stemmed:
            return (Indexer.stem(word) for word in lemated)
        else:
            return lemated
    
    @staticmethod
    def stem(word): #stub
        """Stems the word"""
        return word
    
    def load_titles(self):
        """Loads the titles count info"""
        immediate_print("loading titles from a file")
        filename = self.titles_path()
        self.titles = self.load(filename)
        self.document_count = len(self.titles)

    def get_title(self, article_number):
        """Gets a title from a marshalled file"""
        return self.titles[article_number - 1]

    def get_posting(self, word):
        """Gets a posting from a marshalled file for a given word"""
        forms = self.normalize(word)
        res = set()
        for form in forms:
            filename = self.dict_path(form[:3])
            if os.path.exists(filename):
                prefix_dict = self.load(filename)
                if form in prefix_dict:
                    res.update(prefix_dict[form])
        return sorted(res) #maybe try merge_or

def main():
    """Does some indexer testing"""
    indexer = Indexer()
    #indexer = Indexer(compressed = True)

    #indexer.initialize_morfologik('data/morfologik_do_wyszukiwarek.txt')

    #indexer.create_index('data/wikipedia_dla_wyszukiwarek.txt', 'data/morfologik_do_wyszukiwarek.txt')
    indexer.create_index('data/mini_wiki.txt', 'data/morfologik_do_wyszukiwarek.txt')

if __name__ == "__main__":
    main()
