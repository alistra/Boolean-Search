#!/usr/bin/python

import os
import re
import time
import marshal

class Indexer:
    morphologic = {}

    def __init__(self, index_dir = "index", compressed = False, stemmed = False):
        self.index_dir = self.create_index_directory(index_dir, compressed, stemmed)

    def create_index_directory(self, dirname, compressed, stemmed):
        if compressed or stemmed:
            dirname = dirname + '_'
            if compressed: dirname = dirname + 'C' 
            if stemmed: dirname = dirname + 'S'

        if not os.path.isdir('./' + dirname + '/'):
            os.mkdir('./' + dirname + '/')
        return dirname

    def load_morphologic(self, filename):
        f = open(filename, 'r')
        self.morphologic = marshal.load(f)

    def dump_morphologic(self, filename):
        f = open(filename, 'w')
        marshal.dump(self.morphologic, f, 2)

    def initialize_morphologic(self, filename):
        filehandle = open(filename)
        for line in filehandle:
            forms = line.split(' ')
            word = forms[0]
            self.morphologic[word] = forms[1:]

    def index_documents(self, filename):
        t = open('./' + self.index_dir + '/TITLES','w') #what if already exists
        document_count = 0

        filehandle = open(filename)
        for line in filehandle:
            m = re.search(r'^##TITLE## (.*)$', line)
            if m:
                document_count += 1
                t.write(str(document_count) + ' ' + m.group(1) + '\n' )
            else:
                pass
                #for word in re.findall(r'\w+', line):
                #    print(word + " " + str(normalize(word, m, stemmed)))
        
        t.close()

    def normalize(w, stemmed):
        w = w.lower()
 
        if w in self.morphologic:
            lemated = self.morphologic[w] 
        else:
            lemated = [w]

        if stemmed:
            return [stem(w) for w in lemated]
        else:
            return lemated

    def stem(w): #stub
        return w

import sys

if __name__ == "__main__":
    indexer = Indexer()

    print 'initializing morphologic...',
    sys.stdout.flush()
    indexer.initialize_morphologic('../morfologik_do_wyszukiwarek.txt')
    #indexer.load_morphologic('morphologic.pickle')
    print 'ok'

    #indexer.dump_morphologic('morphologic.pickle')
    #print 'indexing...',
    #sys.stdout.flush()
    #indexer.index_documents('../wikipedia_dla_wyszukiwarek.txt')
    #indexer.index_documents('test.txt')
    #print 'ok'
