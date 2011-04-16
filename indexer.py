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
    t = open('./' + dirname + '/TITLES','w') #what if already exists
    document_count = 0

    filehandle = open(filename)
    for line in filehandle:
        m = re.search(r'##TITLE## (\w+)', line)
        if m:
            document_count += 1
            t.write(str(document_count) + ' ' + m.group(1) + '\n' )
        else:
            for word in re.findall(r'\w+', line):
                print(word + " " + str(normalize(word, m, stemmed)))
    
    t.close()

def normalize(w, m, stemmed):
    w = w.lower()
    try:
        print(w)
        res = m[w] 
    except TypeError:
        res = [w]
    except KeyError:
        res = [w]
    if stemmed:
        return stem(res)
    else:
        return res

def stem(w): #stub
    return w

generate_index('wikipedia_dla_wyszukiwarek.txt')
