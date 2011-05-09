#!/usr/bin/python3.1
"""An executable file for handling queries in an interactive or a batch mode"""

import searcher, indexer, sys

try:
    import readline
except: #pylint: disable=W0702
    pass

def get_words_from_queries(indexer_obj, query_list):
    '''Extracts words from queries in a prefix dict form'''
    query_words = {}
    for query in query_list:
        for word in query.get_words():
            query_words.setdefault(word[:indexer_obj.prefix_len], set()).add(word)
    return query_words

def normalize_words(indexer_obj, query_words):
    '''Creates prefix dict for normalized words'''
    query_normalized_words = {}
    for prefix in query_words:
        words = query_words[prefix]
        indexer_obj.load_to_morfologik_cache(words, prefix)
        for word in words:
            for base in indexer_obj.normalize(word):
                query_normalized_words.setdefault(base[:indexer_obj.prefix_len], set()).add(base)
    return query_normalized_words

def search(searcher_obj, indexer_obj, queries):
    '''Perform a search on a batch of queries'''
    query_words = get_words_from_queries(indexer_obj, queries)

    query_normalized_words = normalize_words(indexer_obj, query_words)
    
    for prefix in query_normalized_words:
        indexer_obj.load_to_index_cache(query_normalized_words[prefix], prefix)

    indexer_obj.load_titles('TITLES')

    for query in queries:
        result = [indexer_obj.get_title(doc) 
                    for doc in searcher_obj.search(query)]
        result_str = "\n".join(result)
        print('QUERY:', query, 'TOTAL:', len(result))
        print(result_str)
    
    indexer_obj.titles = []
    indexer_obj.morfologik_cache.clear() #moze zostawic te 2 linie?
    indexer_obj.index_cache.clear() 

if __name__ == "__main__":
    indexer_obj = indexer.Indexer()
    indexer_obj.detect_compression()
    searcher_obj = searcher.Searcher(indexer_obj)

# nie wiem co kurwa sie dzieje ponizej tej linii

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
                search(searcher_obj, indexer_obj, queries)
    except KeyboardInterrupt:
        pass
