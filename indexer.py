#!/usr/bin/python3.1
import os
import re
import time

def create_index_directory(compressed, stemmed):
    dirname = 'index'
    
    if compressed or stemmed:
        dirname = dirname + '_'
        if compressed: dirname = dirname + 'C' 
        if stemmed: dirname = dirname + 'S'

    if not os.path.isdir('./' + dirname + '/'):
        os.mkdir('./' + dirname + '/')
    return dirname

def initialize_morfologik(filename):
    m = dict()

    filehandle = open(filename)
    for line in filehandle:
        linewords = line.split()
        m[linewords[0]] = linewords[1:]

    return m

def generate_index(filename, compressed = False, stemmed = False):
    dirname = create_index_directory(compressed, stemmed)
    m = initialize_morfologik('morfologik_do_wyszukiwarek.txt')

    filehandle = open(filename)
    for line in filehandle:
        for word in re.findall(r'\w+', line):
            try:
                print(m[word])
                time.sleep(1)
            except:
                print('>> ' + word)


generate_index('wikipedia_dla_wyszukiwarek.txt')
