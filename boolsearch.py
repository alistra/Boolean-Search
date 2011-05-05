#!/usr/bin/python3.1
"""An executable file for handling queries in an interactive or a batch mode"""

import searcher, indexer, sys

try:
    import readline
except:
    pass

i = indexer.Indexer()
s = searcher.Searcher(i)

queries = []
results = []

print('normalizing')

while True:
    try:
        query = searcher.Query(input())
        i.load_to_morfologik_cache(query.get_words())
        i.load_to_index_cache(query.get_words())
        queries.append(query)
    except EOFError:
        break

print('searching')

for query in queries:
    results.append(s.search(query))

i.morfologik_cache.clear()
i.index_cache.clear()
i.load_titles()

print('printing')

for res in results:
    print('QUERY:', query, 'TOTAL:', len(res))
    for doc in res:
        print(i.get_title(doc))
