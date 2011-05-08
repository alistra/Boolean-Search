#!/usr/bin/python3.1
"""An executable file for handling queries in an interactive or a batch mode"""

import searcher, indexer, sys

try:
    import readline
except:
    pass

def search(s, i, queries):
    '''Perform a search on a batch of queries'''
    query_words = {}
    query_normalized_words = {}
    
    for query in queries:
        for word in query.get_words():
            query_words.setdefault(word[:3], set()).add(word)

    #print('normalizing')

    for prefix in query_words:
        words = query_words[prefix]
        i.load_to_morfologik_cache(words, prefix)
        for word in words:
            for base in i.normalize(word):
                query_normalized_words.setdefault(base[:3], set()).add(base)
    
    #print('loading index')

    for prefix in query_normalized_words:
        i.load_to_index_cache(query_normalized_words[prefix], prefix)
        #for word in query_normalized_words[prefix]:
        #    i.index_cache[word] = [(1, 2), (2, 5), (3, 1)]
 
    #size_sum = 0
    #for word in i.index_cache:
    #    size = i.index_cache[word].__sizeof__()
    #    print('size of', word, 'is', size)
    #    size_sum += size
    #print('sum =', size_sum)

    i.load_titles()

    #print('searching')

    for query in queries:
        result = list(s.search(query))
        print('QUERY:', query, 'TOTAL:', len(result))
        for doc in result:
            print(i.get_title(doc))
    
    i.titles = []
    i.morfologik_cache.clear()
    i.index_cache.clear()


if __name__ == "__main__":
    i = indexer.Indexer()
    s = searcher.Searcher(i)

    if len(sys.argv) > 1 and sys.argv[1] == 'i':
        n = 1
    else:
        n = 10

    try:
        eof = False
        while not eof:
            queries = []
            for _ in range(n):
                try:
                    queries.append(searcher.Query(input()))
                except EOFError:
                    eof = True
                    break
            if queries != []:
                search(s, i, queries)
    except KeyboardInterrupt:
        pass
