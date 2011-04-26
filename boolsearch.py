#!/usr/bin/python3.1

import searcher, indexer, sys

def print_results(results):
    print('TOTAL: ', len(results))
    for res in results:
        print(res)

s = searcher.Searcher(indexer.Indexer())
if len(sys.argv) > 1:
    for query in sys.argv[1:]:
        print('Searching query: ', query)
        print_results(s.search(query))
else:
    while True:
        try:
            query = input('query: ')
            print_results(s.search(query))
        except KeyboardInterrupt:
            break
