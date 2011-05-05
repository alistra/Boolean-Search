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
query_words = {}
query_normalized_words = {}

print('normalizing')

while True:
    try:
        query = searcher.Query(input())
        for word in query.get_words():
            query_words.setdefault(word[:3], set()).add(word)
        queries.append(query)
    except EOFError:
        break

for prefix in query_words:
    words = query_words[prefix]
    i.load_to_morfologik_cache(words, prefix)
    for word in words:
        for base in i.normalize(word):
            query_normalized_words.setdefault(base[:3], set()).add(base)
        
for prefix in query_normalized_words:
    i.load_to_index_cache(query_normalized_words[prefix], prefix)

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
