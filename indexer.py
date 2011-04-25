#!/usr/bin/env python3.1

import os
import re
import time
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
        title_path = os.path.join(self.index_dir, 'TITLES')
        if os.path.exists(title_path):
            index_titles = False        
        else:
            index_titles = True
            t = open(title_path, 'w')

        document_count = 0
        index_count = 0
        regexp = re.compile(r'\w+')

        filehandle = open(filename)
        for line in filehandle:
            if line[:9] == '##TITLE##':
                if document_count % 1000 == 0:
                    print('indexed ', document_count)
                document_count += 1
                if index_titles:
                    t.write(str(document_count) + ' ' + line[10:].strip() + '\n' )
            else:
                for word in regexp.findall(line):
                    bases = self.normalize(word)
                    for base in bases:
                        if len(base) >= 3:
                            path = os.path.join(self.index_dir, base[:3])
                        else:
                            path = os.path.join(self.index_dir, 'SHORT') 

                        indexfilehandle = open(path, 'a') 
                        indexfilehandle.write(base + ' ' + str(document_count) + '\n')

    def normalize(self, w):
        w = w.lower()#.strip(' ,`!()[]{};:\'"<>.?/')
 
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
