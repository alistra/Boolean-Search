#!/usr/bin/python3.1
"""An executable file for handling queries in an interactive or a batch mode"""

import searcher, indexer, sys

try:
    import readline
except:
    pass

def search(s, i, num):
    queries = []
    results = []
    query_words = {}
    query_normalized_words = {}
    eof = False

    i.morfologik_cache.clear()
    i.index_cache.clear()

    for _ in range(num):
        try:
            query = searcher.Query(input())
            for word in query.get_words():
                query_words.setdefault(word[:3], set()).add(word)
            queries.append(query)
        except EOFError:
            eof = True
            break

    print('normalizing')

    for prefix in query_words:
        words = query_words[prefix]
        i.load_to_morfologik_cache(words, prefix)
        for word in words:
            for base in i.normalize(word):
                query_normalized_words.setdefault(base[:3], set()).add(base)
            
    print('loading index')

    for prefix in query_normalized_words:
        i.load_to_index_cache(query_normalized_words[prefix], prefix)

    print('searching')

    for query in queries:
        results.append(s.search(query))

    i.morfologik_cache.clear()
    i.index_cache.clear()

    i.load_titles()

    print('printing')

    for nr in range(len(results)):
        res_list = list(results[nr])
        print('QUERY:', queries[nr], 'TOTAL:', len(res_list))
        for doc in res_list:
            print(i.get_title(doc))

    return not eof

i = indexer.Indexer(compressed = True)
s = searcher.Searcher(i)

while search(s, i, 1000):
    pass
