#!/usr/bin/env python3.1

import os
import re
import time
import marshal

class Indexer:
    morphologic = {}

    def index_dir_slashes(self):
        return './' + self.index_dir + '/'
    
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

    def load_morphologic(self, filename):
        f = open(filename, 'rb')
        self.morphologic = marshal.load(f)

    def dump_morphologic(self, filename):
        f = open(filename, 'wb')
        marshal.dump(self.morphologic, f, 2)

    def initialize_morphologic(self, filename, cachefile):
        if os.path.exists(cachefile):
            self.load_morphologic(cachefile)
    
        if self.morphologic == {}:
            filehandle = open(filename)
            for line in filehandle:
                forms = line.split(' ')
                forms = list(map(lambda x: x.rstrip(), forms))
                word = forms[0]
                self.morphologic[word] = forms[1:]
            self.dump_morphologic(cachefile)

    def index_documents(self, filename):
        index_titles = True
        if os.path.exists(self.index_dir_slashes() + 'TITLES'):
            index_titles = False        
        else:
            t = open(self.index_dir_slashes() + 'TITLES','w')

        document_count = 0
        index_count = 0

        filehandle = open(filename)
        for line in filehandle:
            m = re.search(r'^##TITLE## (.*)$', line)
            if m:
                document_count += 1
                if index_titles: t.write(str(document_count) + ' ' + m.group(1) + '\n' )
            else:
                for word in re.findall(r'\w+', line):
                    bases = self.normalize(word)
                    for base in bases:
                        if len(base) >= 3:
                            indexfilehandle = open(self.index_dir_slashes() + base[0:3], "a")
                        else:
                            indexfilehandle = open(self.index_dir_slashes() + 'SHORT', "a") 
                        indexfilehandle.write(base + " " + str(document_count) + "\n")
                        indexfilehandle.close()
        t.close()

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

    def stem(w): #stub
        return w

import sys

if __name__ == "__main__":
    indexer = Indexer()

    print('initializing morphologic...', end="")
    sys.stdout.flush()
    indexer.initialize_morphologic('data/morfologik_do_wyszukiwarek.txt', 'data/morfologik.marshal')
    print('ok')

    print('running indexing...', end="")
    sys.stdout.flush()

    indexer.index_documents('data/wikipedia_dla_wyszukiwarek.txt')
    #indexer.index_documents('test.txt')
    #print ('ok')
