#!/usr/bin/python3.1
'''File for the Searcher class and tests for it'''
import unittest

class EmptyQuery(Exception):
    pass

class Query:
    def __init__(self, query = ""):
        self.terms = []
        self.clauses = []
        self.type = ""
        self.parse(query)

    def parse(self, query):
        if query != "":
            if query[0] == '"' and query[-1] == '"':
                self.parse_phrase(query)
            else:
                self.parse_cnf(query)

    def parse_phrase(self, phrase):
        self.terms = phrase[1:-1].split(' ')
        self.type = "phrase"
        if self.terms == ['']:
            raise EmptyQuery()

    def parse_cnf(self, cnf):
        self.type = "cnf"
        self.clauses = [clause.split('|') for clause in cnf.split(' ') 
                if clause != '']

    def get_words(self):
        '''Generator for the words in queries'''
        if self.type == 'cnf':
            for clause in self.clauses:
                for term in clause:
                    if term[0] == '~':
                        yield term[1:]
                    else:
                        yield term
        elif self.type == 'phrase' :
            for term in self.terms:
                if term[0] == '~':
                    yield term[1:]
                else:
                    yield term

    def __str__(self):
        if self.type == 'cnf':
            return ' '.join(['|'.join(c) for c in self.clauses])
        elif self.type == 'phrase':
            return '"' + ' '.join(self.terms) + '"'

class SearchResult:
    def __init__(self, docs = {}, negation = False):
        self.docs = docs
        self.negation = negation

class Searcher:
    def __init__(self, indexer):
        self.indexer = indexer

    def search(self, query):
        if query.type == "cnf":
            results = self.search_cnf(query)
            if results.negation:
                docs = self.subtract_from_uni(self.indexer.document_count,
                        results.docs)
            else:
                docs = results.docs
        else:
            docs = []

        return docs

    def search_cnf(self, query):
        to_list = lambda res: SearchResult(list(res.docs), res.negation)
        clause_results = [to_list(self.search_clause(clause))
                for clause in query.clauses]

        # sort by result length
        clause_results.sort(key = lambda x: len(x.docs))

        results = clause_results[0]
        for clause_result in clause_results[1:]:
            results = self.merge_and(results, clause_result)
        return results
      
    def search_clause(self, clause):
        term_results = [self.search_term(term) for term in clause]
        results = term_results[0]
        for term_result in term_results[1:]:
            results = self.merge_or(results, term_result)
        return results

    def search_term(self, term):
        if term[0] == '~':
            neg = True
            word = term[1:]
        else:
            neg = False
            word = term

        postings = [SearchResult(self.indexer.get_posting(form), False)
            for form in self.indexer.normalize(word)]   
       
        res = postings[0]
        for pos in postings[1:]:
            res = self.merge_or(res, pos)
        res.negation = neg
        return res

    def merge_or(self, res1, res2):
        """Merges with OR two search results in O(m + n) time."""
        if res1.negation and res2.negation:
            # ~x | ~y  <=>  ~(x & y)
            res1.negation = res2.negation = False
            res = self.merge_and(res1, res2)
            res.negation = True
            return res
        elif res1.negation:
            # ~x | y  <=>  ~(x \ y)
            return SearchResult(self.subtract(res1.docs, res2.docs), True)
        elif res2.negation:
            # x | ~y  <=>  ~(y \ x)
            return SearchResult(self.subtract(res2.docs, res1.docs), True)
        else:
            # x | y
            return SearchResult(self.merge_or_docs(res2.docs, res1.docs), False)

    def merge_or_docs(self, docs1, docs2):
        '''Generator for or-merging lists'''
        gen1 = iter(docs1)
        gen2 = iter(docs2)
        last_added = -1
        elem1 = None
        elem2 = None
        try:
            elem1 = next(gen1)
            elem2 = next(gen2)
            while True:
                if elem1 < elem2:
                    yield(elem1)
                    last_added = elem1
                    elem1 = next(gen1)
                elif elem1 > elem2:
                    yield(elem2)
                    last_added = elem2
                    elem2 = next(gen2)
                else:
                    yield(elem1)
                    last_added = elem1
                    elem1 = next(gen1)
                    elem2 = next(gen2)
        except StopIteration:
            if elem1 and elem2:
                tmin = min(elem1, elem2)
                tmax = max(elem1, elem2)
                if tmin > last_added:
                    yield(tmin)
                    if tmin != tmax:
                        yield(tmax)
                elif tmax > last_added:
                    yield(tmax)
            elif elem1 and elem1 > last_added:
                yield(elem1)
            elif elem2 and elem2 > last_added:
                yield(elem2)

        for elem1 in gen1:
            yield(elem1)
        for elem2 in gen2:
            yield(elem2)

    def merge_and(self, res1, res2):
        """Merges with AND two search results in O(m + n) time."""
        if res1.negation and res2.negation:
            # ~x & ~y  <=>  ~(x | y)
            res1.negation = res2.negation = False
            res = self.merge_or(res1, res2)
            res.negation = True
            return res
        elif res1.negation:
            # ~x & y  <=> y \ x
            return SearchResult(self.subtract(res2.docs, res1.docs), False)
        elif res2.negation:
            # x & ~y  <=> x \ y
            return SearchResult(self.subtract(res1.docs, res2.docs), False)
        else:
            # x & y
            return SearchResult(self.merge_and_docs(res1.docs, res2.docs), False)

    def merge_and_docs(self, docs1, docs2):
        '''Generator for and-merging lists'''
        gen1 = iter(docs1)
        gen2 = iter(docs2)
        try:
            elem1 = next(gen1)
            elem2 = next(gen2)
            while True:
                if elem1 < elem2:
                    elem1 = next(gen1)
                elif elem1 > elem2:
                    elem2 = next(gen2)
                else:
                    yield(elem1)
                    elem1 = next(gen1)
                    elem2 = next(gen2)
        except StopIteration:
            pass

    def subtract_from_uni(self, document_count, docs):
        '''Generator for subtracting a posting from the universe'''
        start = 1
        for n in docs:
            for i in range(start, n):
                yield(i)
            start = n+1
        for i in range(start, document_count+1):
            yield(i)

#który jest dobrze?
#    def subtract_from_uni(self, N, d):
#        '''Generator for subtracting a posting from the universe'''
#        e2 = next(d)
#        for n in range(1, N + 1):
#            if i >= len(d) or n < d[i]:
#                yield n
#            elif n == d[i]:
#                i += 1
#            else:
#                while d[i] < n:
#                    i += 1


    def subtract(self, docs1, docs2):
        """Generator for subtracting two lists in O(m + n) time."""
        # x \ y
        gen1 = iter(docs1)
        gen2 = iter(docs2)
        try:
            elem2 = next(gen2)
            elem1 = next(gen1)
            while True:
                if elem1 < elem2:
                    yield(elem1)
                    elem1 = next(gen1)
                elif elem1 > elem2:
                    elem2 = next(gen2)
                else:
                    elem2 = next(gen2)
                    elem1 = next(gen1)
        except StopIteration:
            for elem1 in gen1:
                yield elem1


class QueryTest(unittest.TestCase):
    def test_phrase(self):
        q = Query('"foo bar baz"')
        self.assertEqual(q.terms, ['foo', 'bar', 'baz'])
        self.assertEqual(q.type, 'phrase')

    def test_single_word_phrase(self):
        q = Query('"term1"')
        self.assertEqual(q.terms, ['term1'])
        self.assertEqual(q.type, 'phrase')

    def test_cnf(self):
        q = Query("foo bar|baz ~not term1|~term2")
        self.assertEqual(q.clauses, [['foo'], ['bar', 'baz'], ['~not'], ['term1', '~term2']])
        self.assertEqual(q.type, 'cnf')
    
    def test_single_word_cnf(self):
        q = Query("single")
        self.assertEqual(q.clauses, [['single']])
        self.assertEqual(q.type, 'cnf')

    def test_parse_after_phrase(self):
        q = Query('"aaa bbb ccc"')
        q.parse('foo bar|baz')
        self.assertEqual(q.type, 'cnf')
        self.assertEqual(q.clauses, [['foo'], ['bar', 'baz']])

    def test_parse_after_cnf(self):
        q = Query('"aaa bbb|ccc"')
        q.parse('"foo bar"')
        self.assertEqual(q.terms, ['foo', 'bar'])
        self.assertEqual(q.type, 'phrase')

    def test_empty_query(self):
        q = Query()
        self.assertEqual(q.type, "")

    def test_empty_phrase(self):
        q = Query()
        self.assertRaises(EmptyQuery, q.parse, '""')

class SearcherTest(unittest.TestCase):
    def setUp(self):
        self.docs = {
                    'foo' : [1, 2, 3, 4, 5],
                    'bar' : [2, 3, 7, 8, 9],
                    'baz' : [1, 2, 7],
                    'alone' : [6, 10]
                }

        class IndexerMock:
            document_count = 10
            def get_title(self, doc):
                return doc

            def get_posting(self2, term):
                return self.docs[term]

        self.searcher = Searcher(IndexerMock())

    def test_single(self):
        res = self.searcher.search('foo')
        self.assertEqual(res, self.docs['foo'])

    def test_single_negation(self):
        res = self.searcher.search('~foo')
        self.assertEqual(res, [6, 7, 8, 9, 10])

    def test_plain_and(self):
        res = self.searcher.search('foo bar baz')
        self.assertEqual(res, [2])

    def test_plain_and_negation(self):
        res = self.searcher.search('foo ~bar baz')
        self.assertEqual(res, [1])

    def test_plain_and_negation2(self):
        res = self.searcher.search('~foo ~bar')
        self.assertEqual(res, [6, 10])

    def test_plain_or(self):
        res = self.searcher.search('foo|alone')
        self.assertEqual(res, [1, 2, 3, 4, 5, 6, 10])

    def test_plain_of_negation(self):
        res = self.searcher.search('~foo|bar')
        self.assertEqual(res, [2, 3, 6, 7, 8, 9, 10])

    def test_plain_of_negation2(self):
        res = self.searcher.search('~foo|~alone')
        self.assertEqual(res, [1, 2, 3, 4, 5, 6, 7, 8, 9, 10])

    def test_empty_intersection(self):
        res = self.searcher.search('bar|~baz foo|baz alone')
        self.assertEqual(res, [])

if __name__ == "__main__":
    unittest.main()
