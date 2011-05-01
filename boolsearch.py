#!/usr/bin/python3.1
"""An executable file for handling queries in an interactive or a batch mode"""

import searcher, indexer, sys

def print_results(results):
    """Prints the result of a query"""
    print('TOTAL: ', len(results))
    print('\n'.join(results))

s = searcher.Searcher(indexer.Indexer(compressed = True))
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
