#!/usr/bin/python3.1 -OO
"""File containing the Indexer class and some tests for it"""
import os
import re
import marshal
import sys
import gzip
import copy

def immediate_print(string):
    """A function to print and flush the stdout immediately"""
    print(string)
    sys.stdout.flush()

class Indexer:
    """A class for generating index files and getting posting lists"""
    morfologik = {}
    morfologik_cache = {}
    index_cache = {}
    index_nopos_cache = {}
    titles = []
    document_count = 0

    def __init__(self, index_dir = "index", compressed = False, stemmed = False,
            debug = False, prefix_len = 3):

        self.stemmed = stemmed
        self.compressed = compressed
        self.index_dir = index_dir
        self.debug = debug
        self.prefix_len = prefix_len
        if self.stemmed:
            self.stemsufix = re.compile(r'''(.*)((logia|janin|owanie)|\
                                                (czyk|rzeć|arty|enie|ślać|acja|ować)|\
                                                (ość|cie|ski|cie|ium|owy|jać|ent|nie|lać|ieć|nąć|izm|iel|yzm|acz)|\
                                                (ny|ić|ać|na|eć|ki|yć|ek|yk|ik|ów)|\
                                                (a|y|e|o))$''')

    def detect_compression(self):
        '''Set the compressed flag according to the index'''
        comp_file = os.path.join(self.index_dir, 'COMPRESSED')
        if os.path.exists(comp_file):
            self.compressed = True
        else:
            self.compressed = False

    def detect_prefix_len(self):
        '''Set the prefix length according to the index'''
        prefix_len_file = os.path.join(self.index_dir, 'PREFIX_LENGTH')
        if os.path.exists(prefix_len_file):
            prefix_len_handle = open(prefix_len_file, 'r')
            self.prefix_len = int(next(prefix_len_handle))
        else:
            raise Exception("No prefix length information in the index")


    def create_index(self, data_file, morfologik_file):
        """Create a new index."""
        if not os.path.exists(self.index_dir):
            os.mkdir(self.index_dir)

        compflag = os.path.join(self.index_dir, 'COMPRESSED')
        
        if self.compressed:
            open(compflag, 'w').close()
        elif os.path.exists(compflag):
            os.remove(compflag)

        prefix_len_file = os.path.join(self.index_dir, 'PREFIX_LENGTH')
        prefix_len_handle = open(prefix_len_file, 'w')
        prefix_len_handle.write(str(self.prefix_len))

        if self.debug:
            immediate_print("initializing morfologik")
        self.initialize_morfologik(morfologik_file)
        
        if self.debug:
            immediate_print("sorting morfologik")
        Indexer.sort_file(morfologik_file, 'MORFOLOGIK.sorted')

        if self.debug:
            immediate_print("generating morfologik index")
        self.generate_dicts("MORFOLOGIK.sorted",
                os.path.join(self.index_dir, "morfologik"), True)

        if not self.debug:
            os.remove('MORFOLOGIK.sorted')

        if self.debug:
            immediate_print("gathering document data")
        self.generate_index_file(data_file, 'WORDS')

        if self.debug:
            immediate_print("dumping document titles")
        self.dump_titles('TITLES')

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


    def initialize_morfologik(self, morfologik_filename):
        """Generates morfologik dictionary from a file"""
        if self.morfologik == {}:
            morfologik_handle = open(morfologik_filename, 'r')
            for line in morfologik_handle:
                forms = line.rstrip().split(' ')
                self.morfologik[forms[0]] = forms[1:]

    def generate_index_file(self, filename, out_filename):
        """Generates unsorted index file with the word occurences"""

        doc_count = 0
        word_regexp = re.compile(r'\w+')
        file_handle = open(filename, 'r')
        indexfile_handle = open(out_filename, 'w') 
        word_count = 0
    
        illegal_char_regexp = re.compile(r'[^0-9a-zęóąśłżźćń]')

        for line in file_handle:
            if line[:9] == '##TITLE##':
                if self.debug and doc_count % 1000 == 0:
                    immediate_print('%(count)d documents indexed' 
                        % {'count': doc_count})
                doc_count += 1
                self.titles.append(line[10:].strip())
                word_count = 0
            else:
                for word in word_regexp.findall(line):
                    word_count += 1
                    bases = self.normalize(word)
                    for base in bases:
                        if illegal_char_regexp.search(base):
                            continue
                        indexfile_handle.write("%(b)s %(c)d %(p)d\n" %
                            {'b': base, 'c': doc_count, 'p': word_count})

    @staticmethod
    def sort_file(filename, dest):
        """Sorts the big index file"""
        os.system("LC_ALL=C sort -T. -k1,1 -s " + filename + " > " + dest)

    def generate_dicts(self, sorted_filename, out_dir, morfologik = False):
        """Generates prefix dictionaries from the sorted index file"""
        if not os.path.exists(out_dir):
            os.mkdir(out_dir)

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
            
            if key[:self.prefix_len] == prefix:
                if key in index_dict:
                    if index_dict[key][-1][0] == value[0]:
                        index_dict[key][-1][1].append(value[1])
                    else:
                        index_dict[key].append([value[0], [value[1]]])
                else:
                    if morfologik:
                        index_dict[key] = value
                    else:
                        index_dict[key] = [[value[0], [value[1]]]]
            else:
                if prefix != "":

                    if self.compressed and not morfologik:
                        index_dict = Indexer.differentiate_dict(index_dict)

                    self.dump(index_dict, os.path.join(out_dir, prefix))
                    if not morfologik:
                        self.dump(Indexer.deposition_dict(index_dict), os.path.join(out_dir, "%s.nopos" % prefix))

                    if self.debug:
                        immediate_print("dumping dict %(filename)s" % 
                            {'filename': os.path.join(out_dir, prefix)})

                    index_dict.clear()

                if morfologik:
                    index_dict[key] = value
                else:
                    index_dict[key] = [[value[0], [value[1]]]]
                prefix = key[:self.prefix_len]

        if self.compressed and not morfologik:
            index_dict = Indexer.differentiate_dict(index_dict)
        self.dump(index_dict, os.path.join(out_dir, prefix))
        if not morfologik:
            self.dump(Indexer.deposition_dict(index_dict), os.path.join(out_dir, "%s.nopos" % prefix))
    
    @staticmethod
    def deposition_dict(dic):
        for key in dic:
            dic[key] = list(Indexer.deposition_posting(dic[key]))
        return dic

    @staticmethod
    def deposition_posting(posting):
        return [elem[0] for elem in posting]

    @staticmethod
    def differentiate_dict(dic):
        '''Differentiate posting lists in a dict'''
        for key in dic:
            dic[key] = list(Indexer.differentiate_posting(dic[key]))
        return dic

    @staticmethod
    def differentiate_posting(posting, nopos = False):
        """Differentiaties posting lists"""
        if not posting == []:
            doc_counter = 0
            if not nopos:
                for elem in posting:
                    doc = elem[0]
                    pos = elem[1]
                    ndoc = doc - doc_counter
                    npos = list(Indexer.differentiate_posting(pos, nopos = True))
                    doc_counter = doc
                    yield (ndoc, npos)
            else:
                for elem in posting:
                    yield (elem - doc_counter)
                    doc_counter = elem

    @staticmethod
    def dedifferentiate_posting(posting, nopos = False):
        """Dedifferentiates posting lists"""
        if not posting == []:
            doc_counter = 0
            if nopos:
                for elem in posting:
                    doc_counter += elem
                    yield(doc_counter)
            else:
                for elem in posting:
                    doc = elem[0]
                    pos = elem[1]
                    doc_counter += doc
                    npos = Indexer.dedifferentiate_posting(pos, nopos = True)
                    yield (doc_counter, npos)

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
        '''morfologik wrapper to load_to_cache'''
        if words != []:
            filename = os.path.join(self.index_dir, 'morfologik', prefix)
            self.load_to_cache(self.morfologik_cache, words, filename)

    def load_to_index_cache(self, words, prefix):
        '''index wrapper to load_to_cache'''
        if words != []:
            filename = os.path.join(self.index_dir, prefix)
            self.load_to_cache(self.index_cache, words, filename)

    def load_to_index_nopos_cache(self, words, prefix):
        '''index nopos wrapper to load_to_cache'''
        if words != []:
            filename = os.path.join(self.index_dir, "%s.nopos" % prefix)
            self.load_to_cache(self.index_nopos_cache, words, filename)

    def load_to_cache(self, cache, words, filename):
        '''Load the info about words from a file to a cache'''
        if os.path.exists(filename):
            dic = self.load(filename)
            for word in words:
                if word in dic:
                    cache[word] = dic[word]

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
        if len(word) <= self.prefix_len:
            return word

        mat = self.stemsufix.match(word)
        if mat:
            return mat.group(1)
        else:
            return word
    
    def dump_titles(self, filename):
        """Dumps titles info into a marshalled file"""
        self.dump(self.titles, filename)

    def load_titles(self, filename):
        """Loads the titles count info"""
        self.titles = self.load(filename)
        self.document_count = len(self.titles)

    def get_title(self, article_number):
        """Gets a title from a marshalled file"""
        return self.titles[article_number - 1]
    
    def get_positional_posting(self, word):
        """Gets a document posting with positions for a given word"""
        if self.compressed:
            posting = Indexer.dedifferentiate_posting(copy.copy(self.index_cache.get(word, [])))
        else:
            posting = copy.copy(self.index_nopos_cache.get(word, []))
        for doc in posting:
            yield doc
    
    def get_posting(self, word):
        """Gets a document posting without positions for a given word"""
        if self.compressed:
            posting = Indexer.dedifferentiate_posting(copy.copy(self.index_nopos_cache.get(word, [])), nopos = True)
        else:
            posting = copy.copy(self.index_nopos_cache.get(word, []))
        for doc in posting:
            yield doc

def main():
    """Does some indexer testing"""

    indexer = Indexer(compressed = True, debug = True, prefix_len = 5)
    #indexer.create_index('data/wikipedia_dla_wyszukiwarek.txt',
    #indexer.create_index('data/wiki100k',
    #   'data/morfologik_do_wyszukiwarek.txt')
    indexer.load_to_index_cache('w', 'w')
    indexer.load_to_index_nopos_cache('w', 'w')
    print(list(indexer.get_positional_posting('w')))
    print(list(indexer.get_posting('w')))

if __name__ == "__main__":
    main()
