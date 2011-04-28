#!/usr/bin/env python3.1
"""File containing the Indexer class and some tests for it"""
import os
import re
import marshal

class NonPolishCharacter(Exception):
    """Exception for an occurence of a polish character"""
    pass

class Indexer:
    """Class for generating index files and getting posting lists"""
    morphologic = {}
    titles = {}

    def __init__(self, index_dir = "index", compressed = False, stemmed = False):
        self.stemmed = stemmed
        self.compressed = compressed
        self.index_dir = self.create_index_directory(index_dir)
        self.document_count = 0

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

    def initialize_morphologic(self, filename, cachefile):
        """Generates morfologic-data dictionary and caches it, restores if it was cached already"""
        if os.path.exists(cachefile):
            Indexer.load_dict(cachefile)
    
        if self.morphologic == {}:
            filehandle = open(filename)
            for line in filehandle:
                forms = line.split(' ')
                forms[-1] = forms[-1].rstrip()
                self.morphologic[forms[0]] = forms[1:]
            Indexer.dump_dict(self.morphologic, cachefile)

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
        if os.path.exists(self.titles_path()):
            index_titles = False        
        else:
            index_titles = True
            title_handle = open(self.titles_path(), 'w')

        self.document_count = 0
        word_regexp = re.compile(r'\w+')

        filehandle = open(filename)
                        
        indexfilehandle = open(self.unsorted_index_path(), 'a') 

        for line in filehandle:
            if line[:9] == '##TITLE##':
                if self.document_count % 1000 == 0:
                    print('indexed ', self.document_count)
                    sys.stdout.flush()
                self.document_count += 1
                if index_titles:
                    title_handle.write(str(self.document_count) + ' ' + line[10:].strip() + '\n' )
            else:
                for word in word_regexp.findall(line):
                    bases = self.normalize(word)
                    for base in bases:
                        try:
                            for char in base:
                                if not( (ord(char) >= ord('a') and ord(char) <= ord('z')) or
                                        (ord(char) >= ord('0') and ord(char) <= ord('9')) or
                                        (char in 'ążęźćśóńł')):
                                    raise NonPolishCharacter
                            indexfilehandle.write(base + ' ' + str(self.document_count) + '\n')
                        except NonPolishCharacter:
                            pass

    def sort_index_file(self):
        """Sorts the big index file"""
        os.system("sort -T. -k1,1 -s " + self.unsorted_index_path() + " > " + self.sorted_index_path())

    def generate_dicts(self):
        """Generates the three letter dictionary files from the big sorted index file"""
        index_filehandle = open(self.sorted_index_path())
        index_dict = {}
        prefix = ""

        for i, line in enumerate(index_filehandle):
            if i % 1000000 == 0:
                print(str(i) + " parsed lines")
                sys.stdout.flush()
            [key, value] = line.split(' ', 1)
            value = int(value.rstrip())
            
            if key[:3] == prefix:
                if key in index_dict:
                    if index_dict[key][-1] != value:
                        index_dict[key].append(value)
                else:
                    index_dict[key] = [value]
            else:
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

    def dump_titles(self):
        """Dumps titles info into a marshalled file"""
        titles_filehandle = open(self.titles_path())
        titles_dict = {}
            
        print("indexing titles")
        sys.stdout.flush()

        for line in titles_filehandle:
            [key, value] = line.split(' ', 1)
            value = value.rstrip()
            key = int(key)
            titles_dict[key] = value

        Indexer.dump_dict(titles_dict, self.titles_dict_path())

    @staticmethod
    def dump_dict(dictionary, dict_filename):
        """Dups a dictionary to a file"""
        dict_filehandle = open(dict_filename, 'wb')
        marshal.dump(dictionary, dict_filehandle, 2)
        
    @staticmethod
    def load_dict(dict_filename):
        """Loads a dictionary from a file"""
        dict_filehandle = open(dict_filename, 'rb')
        return marshal.load(dict_filehandle)

    def normalize(self, word):
        """Normalizes and possibly stems the word"""
        word = word.lower()
        
        if self.morphologic == {}:
            self.initialize_morphologic('data/morfologik_do_wyszukiwarek.txt', 'data/morfologik.marshal')

        if word in self.morphologic:
            lemated = self.morphologic[word] 
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

import sys

def main():
    """Does some indexer testing"""
    indexer = Indexer()

    print('running indexing...')
    sys.stdout.flush()
    indexer.generate_index_file('data/wikipedia_dla_wyszukiwarek.txt')
    print('ok')

    print('sorting the index file...')
    sys.stdout.flush()
    indexer.sort_index_file()
    print('ok')

    print('generating dictionaries...')
    sys.stdout.flush()
    indexer.generate_dicts()
    print('ok')

    print('generating title dictionary...')
    sys.stdout.flush()
    indexer.dump_titles()
    print('ok')

    print(indexer.get_posting('jest'))

if __name__ == "__main__":
    main()
