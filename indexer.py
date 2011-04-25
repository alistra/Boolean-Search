#!/usr/bin/env python3.1

import os
import re
import marshal

class Indexer:
    morphologic = {}

    def __init__(self, index_dir = "index", compressed = False, stemmed = False):
        self.stemmed = stemmed
        self.compressed = compressed
        self.index_dir = self.create_index_directory(index_dir)

    def create_index_directory(self, dirname):
        if self.compressed or self.stemmed:
            dirname = dirname + '_'
            if self.compressed: dirname = dirname + 'C' 
            if self.stemmed: dirname = dirname + 'S'

        if not os.path.isdir('./' + dirname + '/'):
            os.mkdir('./' + dirname + '/')
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

    def index_documents(self, filename):
        title_path = os.path.join(self.index_dir, 'TITLES')
        if os.path.exists(title_path):
            index_titles = False        
        else:
            index_titles = True
            title_handle = open(title_path, 'w')

        document_count = 0
        regexp = re.compile(r'\w+')

        filehandle = open(filename)
        for line in filehandle:
            if line[:9] == '##TITLE##':
                if document_count % 500 == 0:
                    print('indexed ', document_count)
                    sys.stdout.flush()
                document_count += 1
                if index_titles:
                    title_handle.write(str(document_count) + ' ' + line[10:].strip() + '\n' )
            else:
                for word in regexp.findall(line):
                    # skip foreign letters
                    bases = self.normalize(word)
                    for base in bases:
                        if any([(ord(w) < ord('a') or ord(w) > ord('z')) and w not in 'ążęźćśóńł' for w in base]):
                            continue 
                        if len(base) >= 3:
                            path = os.path.join(self.index_dir, base[:3])
                        else:
                            path = os.path.join(self.index_dir, 'SHORT') 

                        #indexfilehandle = open(path, 'a') 
                        #indexfilehandle.write(base + ' ' + str(document_count) + '\n')

    def generate_dicts(self):
        for i, filename in enumerate(os.listdir(self.index_dir)):
            if os.path.exists(os.path.join(self.index_dir, filename + '.marshal')) or filename[-8:] == '.marshal':
                continue

            if i % 1000 == 0:
                print('generated ', i)
                sys.stdout.flush()

            fh = open(os.path.join(self.index_dir, filename))
            index_dict = {}
            for line in fh:
                [key, value] = line.split(' ', 1)
                value = value.rstrip()
                # this will probably change with positional index
                if key in index_dict and index_dict[key][-1] != value:
                    index_dict[key].append(value)   
                else:
                    index_dict[key] = [value]
            self.dump_dict(index_dict, os.path.join(self.index_dir, filename + '.marshal'))

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

    def get_posting(self, s):
        if len(s) < 3:
            filename = os.path.join(self.index_dir, 'SHORT.marshal')
        else:
            filename = os.path.join(self.index_dir, s[:3] + '.marshal')
        if os.path.exists(filename):
            d = self.load_dict(filename)
            forms = self.normalize(s)
            res = []
            for form in forms:
                if form in d:
                    res += d[form]
            return [int(x) for x in sorted(res)]
        else:
            return []

import sys

def main():
    indexer = Indexer()

    #print('initializing morphologic...', end="")
    #sys.stdout.flush()
    #indexer.initialize_morphologic('data/morfologik_do_wyszukiwarek.txt', 'data/morfologik.marshal')
    #print('ok')

    print('running indexing...')
    sys.stdout.flush()
    #indexer.index_documents('data/wikipedia_dla_wyszukiwarek.txt')
    indexer.index_documents('data/mini_wiki.txt')
    print('ok')

    print('generating dictionaries...')
    sys.stdout.flush()
    indexer.generate_dicts()
    print('ok')
    print(indexer.get_posting('niemagiczny'))

if __name__ == "__main__":
    main()
