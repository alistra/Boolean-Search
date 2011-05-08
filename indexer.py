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

    morfologik_cache = {}
    index_cache = {}

    titles = []
    document_count = 0

    def __init__(self, index_dir = "index", compressed = False, stemmed = False, debug = False):
        self.stemmed = stemmed
        self.compressed = compressed
        self.index_dir = index_dir
        self.debug = debug
        if self.stemmed:
            self.stemsufix = re.compile(r'(.*)((logia|janin|owanie)|(czyk|rzeć|arty|enie|ślać|acja|ować)|(ość|cie|ski|cie|ium|owy|jać|ent|nie|lać|ieć|nąć|izm|iel|yzm|acz)|(ny|ić|ać|na|eć|ki|yć|ek|yk|ik|ów)|(a|y|e|o))$')

    def create_index(self, data_file, morfologik_file):
        """Create new index."""
        if not os.path.exists(self.index_dir):
            os.mkdir(self.index_dir)

        if self.debug:
            immediate_print("initializing morfologik")
        self.initialize_morfologik(morfologik_file)
        
        if self.debug:
            immediate_print("gathering document data")
        self.generate_index_file(data_file, 'WORDS')

        if self.debug:
            immediate_print("sorting document data")
        Indexer.sort_file('WORDS', 'WORDS.sorted')

        if not self.debug:
            os.remove('WORDS')

        if self.debug:
            immediate_print("generating index")
        self.generate_dicts('WORDS.sorted', self.index_dir)

        if not self.debug:
            os.remove('WORDS.sorted')

        if self.debug:
            immediate_print("dumping document titles")
        self.dump_titles()

        if self.debug:
            immediate_print("sorting morfologik")
        Indexer.sort_file(morfologik_file, 'MORFOLOGIK.sorted')

        self.generate_dicts("MORFOLOGIK.sorted",
                os.path.join(self.index_dir, "morfologik"), True)

        if not self.debug:
            os.remove('MORFOLOGIK.sorted')

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

    def generate_index_file(self, filename, out_filename):
        """Generates big unsorted index file with the info about all word occurences"""

        self.document_count = 0
        word_regexp = re.compile(r'\w+')
        file_handle = open(filename, 'r')
        indexfile_handle = open(out_filename, 'w') 
        word_per_doc_count = 0
    
        illegal_char_regexp = re.compile(r'[^1234567890qwertyuiopasdfghjklzxcvbnmęóąśłżźćń]')

        for line in file_handle:
            if line[:9] == '##TITLE##':
                if self.debug and self.document_count % 1000 == 0:
                    immediate_print('%(count)d documents indexed' % {'count': self.document_count})
                self.document_count += 1
                self.titles.append(line[10:].strip())
                word_per_doc_count = 0
            else:
                for word in word_regexp.findall(line):
                    word_per_doc_count += 1
                    bases = self.normalize(word)
                    for base in bases:
                        if illegal_char_regexp.search(base):
                            continue
                        indexfile_handle.write("%(base)s %(count)d %(pos)d\n" % {'base': base, 'count': self.document_count, 'pos': word_per_doc_count})

    @staticmethod
    def sort_file(filename, dest):
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
            if self.debug and i % 1000000 == 0:
                immediate_print("%(count)d parsed lines" % {'count': i})
            words = line.rstrip().split(' ')
            key = words[0]
            if not morfologik:
                value = (int(words[1]), int(words[2]))
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
                if prefix != "":

                    if self.compressed and not morfologik:
                        index_dict = Indexer.differentiate_dict(index_dict)
                    self.dump(index_dict, os.path.join(out_directory, prefix))

                    if self.debug:
                        immediate_print("dumping dict %(filename)s" % {'filename': os.path.join(out_directory, prefix)})

                    index_dict.clear()

                if morfologik:
                    index_dict[key] = value
                else:
                    index_dict[key] = [value]

                prefix = key[:3]

        if self.compressed and not morfologik:
            index_dict = Indexer.differentiate_dict(index_dict)
        self.dump(index_dict, os.path.join(out_directory, prefix))
    
    @staticmethod
    def differentiate_dict(dic):
        '''Differentiate posting lists in a dict'''
        for key in dic:
            dic[key] = list(Indexer.differentiate_posting(dic[key]))
        return dic


    @staticmethod
    def differentiate_posting(posting):
        """Differentiaties posting lists"""
        if not posting == []:
            doc_counter = 0
            pos_counter = 0
            for elem in posting:
                doc = elem[0]
                pos = elem[1]
                if doc > doc_counter:
                    pos_counter = 0
                ndoc = doc - doc_counter
                npos = pos - pos_counter
                doc_counter = doc
                pos_counter = pos
                yield (ndoc,npos)

    @staticmethod
    def dedifferentiate_posting(posting):
        """Dedifferentiates posting lists"""
        if not posting == []:
            doc_counter = 0
            pos_counter = 0
            for elem in posting:
                doc = elem[0]
                pos = elem[1]
                if doc > 0:
                    pos_counter = 0
                doc_counter += doc
                pos_counter += pos
                yield (doc_counter, pos_counter)

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

    def load_to_morfologik_cache(self, words, prefix):
        '''Load the info about words from a morfologik file to a morfologik cache'''
        if words != []:
            filename = os.path.join(self.index_dir, 'morfologik', prefix)
            self.load_to_cache(self.morfologik_cache, words, filename)

    def load_to_index_cache(self, words, prefix):
        '''Load the info about words from an index file to the index cache'''
        if words != []:
            filename = os.path.join(self.index_dir, prefix)
            self.load_to_cache(self.index_cache, words, filename)

    def load_to_cache(self, cache, words, filename):
        '''Load the info about words from a file to a cache'''
        if os.path.exists(filename):
            dic = self.load(filename)
            for word in words:
                if word in dic:
                    if self.compressed:
                        posting = Indexer.dedifferentiate_posting(dic[word])
                    else:
                        posting = dic[word]
                    cache[word] = posting

    def lemmatize(self, word):
        """Lemmatize a word"""
        if self.morfologik != {}:
            morfologik = self.morfologik
        else:
            morfologik = self.morfologik_cache
        
        return morfologik.get(word, [word])

    def normalize(self, word):
        """Normalizes and possibly stems the word"""
        lemmated = self.lemmatize(word.lower())

        if self.stemmed:
            return (self.stem(word) for word in lemmated)
        else:
            return lemmated
    
    def stem(self, word):
        """Stems the word"""
        if len(word) <= 3:
            return word

        mat = self.stemsufix.match(word)
        if mat:
            return mat.group(1)
        else:
            return word
    
    def load_titles(self):
        """Loads the titles count info"""
        if self.debug:
            immediate_print("loading titles from a file")
        filename = self.titles_path()
        self.titles = self.load(filename)
        self.document_count = len(self.titles)

    def get_title(self, article_number):
        """Gets a title from a marshalled file"""
        return self.titles[article_number - 1]

    def get_positional_posting(self, word):
        """Gets a positional posting for a given word"""
        return self.index_cache.get(word, [])

    def get_posting(self, word):
        """Gets a document posting for a given word"""
        posposting = self.get_positional_posting(word)
        old = 0
        for pos in posposting:
            if pos[0] != old:
                yield(pos[0])
                old = pos[0]

def main():
    """Does some indexer testing"""

    indexer = Indexer(compressed = True, debug = True)
    indexer.create_index('data/wikipedia_dla_wyszukiwarek.txt', 'data/morfologik_do_wyszukiwarek.txt')
if __name__ == "__main__":
    main()
