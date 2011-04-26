#!/usr/bin/env python3.1

import os
import re
import marshal

class Indexer:
    morphologic = {}
    titles = {}

    def __init__(self, index_dir = "index", compressed = False, stemmed = False):
        self.stemmed = stemmed
        self.compressed = compressed
        self.index_dir = self.create_index_directory(index_dir)
        self.load_titles()

    def create_index_directory(self, dirname):
        if self.compressed or self.stemmed:
            dirname = dirname + '_'
            if self.compressed: dirname = dirname + 'C' 
            if self.stemmed: dirname = dirname + 'S'

        if not os.path.isdir(dirname + '/'):
            os.mkdir(dirname + '/')
        return dirname

    def initialize_morphologic(self, filename, cachefile):
        if os.path.exists(cachefile):
            self.load_dict(cachefile)
    
        if self.morphologic == {}:
            filehandle = open(filename)
            for line in filehandle:
                forms = line.split(' ')
                forms[-1] = forms[-1].rstrip()
                self.morphologic[forms[0]] = forms[1:]
            self.dump_dict(self.morphologic, cachefile)

    def unsorted_index_path(self):
        return os.path.join(self.index_dir, 'WORDS')

    def sorted_index_path(self):
        return os.path.join(self.index_dir, 'WORDS.sorted')

    def titles_path(self):
        return os.path.join(self.index_dir, 'TITLES')

    def titles_dict_path(self):
        return os.path.join(self.index_dir, 'TITLES.marshal')

    def dict_path(self, prefix):
        return os.path.join(self.index_dir, prefix + '.marshal')

    def generate_index_file(self, filename):
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
                if self.document_count % 500 == 0:
                    print('indexed ', self.document_count)
                    sys.stdout.flush()
                self.document_count += 1
                if index_titles:
                    title_handle.write(str(self.document_count) + ' ' + line[10:].strip() + '\n' )
            else:
                for word in word_regexp.findall(line):
                    bases = self.normalize(word)
                    for base in bases:
                        if all([(ord(w) >= ord('a') and ord(w) <= ord('z')) or (ord(w) >= ord('0') and ord(w) <= ord('9')) or (w in 'ążęźćśóńł') for w in base]):
                            indexfilehandle.write(base + ' ' + str(self.document_count) + '\n')

    def sort_index_file(self):
        os.system("sort --key=1.1,1.3 -s " + self.unsorted_index_path() + " > " + self.sorted_index_path())

    def generate_dicts(self):
        fh = open(self.sorted_index_path())
        index_dict = {}
        prefix = ""

        for i, line in enumerate(fh):
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
                self.dump_dict(index_dict, self.dict_path(prefix))
                index_dict.clear()
                index_dict[key] = [value]
                prefix = key[:3]

        self.dump_dict(index_dict, self.dict_path(prefix))

    def dump_titles(self):
        fh = open(self.titles_path())
        titles_dict = {}
            
        print("indexing titles")
        sys.stdout.flush()

        for line in fh:
            [key, value] = line.split(' ', 1)
            value = value.rstrip()
            key = int(key)
            titles_dict[key] = value

        self.dump_dict(titles_dict, self.titles_dict_path())

    def dump_dict(self, d, fn):
        dh = open(fn, 'wb')
        marshal.dump(d, dh, 2)
        
    def load_dict(self, fn):
        dh = open(fn, 'rb')
        return marshal.load(dh)

    def normalize(self, w):
        w = w.lower()
 
        if w in self.morphologic:
            lemated = self.morphologic[w] 
        else:
            lemated = [w]

        if self.stemmed:
            return [stem(w) for w in lemated]
        else:
            return lemated

    def stem(self, w): #stub
        return w
    
    def load_titles(self):
        filename = self.titles_dict_path()
        self.titles = self.load_dict(filename)
        self.document_count = len(self.titles)

    def get_title(self, t):
        if self.titles == {}:
            self.load_titles()
        return self.titles[t]

    def get_posting(self, s):
        forms = self.normalize(s)
        res = []
        for form in forms:
            filename = self.dict_path(form[:3])
            if os.path.exists(filename):
                d = self.load_dict(filename)
                if form in d:
                    res += d[form]
        return sorted([int(x) for x in res])

import sys

def main():
    indexer = Indexer()

    #print('initializing morphologic...', end="")
    #sys.stdout.flush()
    #indexer.initialize_morphologic('data/morfologik_do_wyszukiwarek.txt', 'data/morfologik.marshal')
    #print('ok')

    #print('running indexing...')
    #sys.stdout.flush()
    #indexer.generate_index_file('data/wikipedia_dla_wyszukiwarek.txt')
    #indexer.generate_index_file('data/mini_wiki.txt')
    #print('ok')

    #print('sorting the index file...')
    #sys.stdout.flush()
    #indexer.sort_index_file()
    #print('ok')

    #print('generating dictionaries...')
    #sys.stdout.flush()
    #indexer.generate_dicts()
    #print('ok')

    #print('generating title dictionary...')
    #sys.stdout.flush()
    #indexer.dump_titles()
    #print('ok')

    #print(indexer.get_posting('niemagiczny'))

if __name__ == "__main__":
    main()
