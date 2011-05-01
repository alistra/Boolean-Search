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
        """Load files from index directory."""
        self.load_titles()

    def create_index(self, data_file, morfologik_file):
        """Create new index."""
        if not os.path.exists(self.index_dir):
            os.mkdir(self.index_dir)

        immediate_print("initializing morfologik")
        self.initialize_morfologik(morfologik_file)
        
        immediate_print("gathering document data")
        self.generate_index_file(data_file, 'WORDS')

        immediate_print("sorting document data")
        self.sort_file('WORDS', 'WORDS.sorted')

        immediate_print("generating index")
        self.generate_dicts('WORDS.sorted', self.index_dir)

        immediate_print("dumping document titles")
        self.dump_titles()

        immediate_print("sorting morfologik")
        self.sort_file(morfologik_file, 'MORFOLOGIK.sorted')

        self.generate_dicts("MORFOLOGIK.sorted",
                os.path.join(self.index_dir, "morfologik"), True)

    def initialize_morfologik(self, morfologik_filename):
        """Generates morfologic-data dictionary and caches it, restores if it was cached already"""
        if self.morfologik == {}:
            morfologik_handle = open(morfologik_filename, 'r')
            for line in morfologik_handle:
                forms = line.rstrip().split(' ')
                self.morfologik[forms[0]] = forms[1:]

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

    def generate_index_file(self, filename, out_filename):
        """Generates big unsorted index file with the info about all word occurences"""

        self.document_count = 0
        word_regexp = re.compile(r'\w+')
        file_handle = open(filename, 'r')
        indexfile_handle = open(out_filename, 'w') 
    
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

    def sort_file(self, filename, dest):
        """Sorts the big index file"""
        os.system("LC_ALL=C sort -T. -k1,1 -s " + filename + " > " + dest)

    def generate_dicts(self, sorted_filename, out_directory, morfologik = False):
        """Generates the three letter dictionary files from the big sorted index file"""
        if not os.path.exists(out_directory):
            os.mkdir(out_directory)

        indexfile_handle = open(sorted_filename)
        index_dict = {}
        prefix = ""

        for i, line in enumerate(indexfile_handle):
            if i % 1000000 == 0:
                immediate_print( "%(count)d parsed lines" % {'count': i})
            words = line.rstrip().split(' ')
            key = words[0]
            if not morfologik:
                value = int(words[1])
            else:
                value = words[1:]
            
            if key[:3] == prefix:
                if key in index_dict:
                    if index_dict[key][-1] != value:
                        index_dict[key].append(value)
                else:
                    if morfologik:
                        index_dict[key] = value
                    else:
                        index_dict[key] = [value]
            else:
                if os.path.exists(os.path.join(out_directory, prefix)) and prefix != "":
                    immediate_print("ERROR: %(filename)s already exists"
                            % {'filename': self.dict_path(prefix)})

                if prefix != "":
                    self.dump(index_dict, os.path.join(out_directory, prefix))

                index_dict.clear()
                if morfologik:
                    index_dict[key] = value
                else:
                    index_dict[key] = [value]
                prefix = key[:3]

        self.dump(index_dict, os.path.join(out_directory, prefix))
    
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

    @staticmethod
    def dedifferentiate_posting(posting):
        """Dedifferentiates posting lists"""
        if not posting == []:
            counter = 0
            res = []
            for elem in posting:
                res.append(elem + counter)
                counter += elem
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

    def lemmatize(self, word):
        if self.morfologik != {}:
            morfologik = self.morfologik
        else:
            filename = os.path.join(self.index_dir, "morfologik", word[:3])
            morfologik = self.load(filename)

        if word in morfologik:
            return morfologik[word] 
        else:
            return [word]

    def normalize(self, word):
        """Normalizes and possibly stems the word"""
        lemmated = self.lemmatize(word.lower())

        if self.stemmed:
            return (Indexer.stem(word) for word in lemmated)
        else:
            return lemmated
    
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
            filename = os.path.join(self.index_dir, form[:3])
            if os.path.exists(filename):
                prefix_dict = self.load(filename)
                if form in prefix_dict:
                    res.update(prefix_dict[form])
        return sorted(res) #maybe try merge_or

def main():
    """Does some indexer testing"""
    #indexer = Indexer()
    indexer = Indexer(compressed = True)

    #indexer.initialize_morfologik('data/morfologik_do_wyszukiwarek.txt')

    #indexer.create_index('data/wikipedia_dla_wyszukiwarek.txt', 'data/morfologik_do_wyszukiwarek.txt')
    #indexer.create_index('data/mini_wiki.txt', 'data/morfologik_do_wyszukiwarek.txt')
    
    indexer.load_index()
    print(indexer.get_posting('penis'))

if __name__ == "__main__":
    main()
