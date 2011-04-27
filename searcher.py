#!/usr/bin/python3.1

import unittest

class EmptyQuery(Exception):
    pass

class Query:
    def __init__(self, query = ""):
        self.parse(query)

    def parse(self, query):
        if query != "":
            if query[0] == '"' and query[-1] == '"':
                self.parse_phrase(query)
            else:
                self.parse_cnf(query)
        else:
            self.type = ""

    def parse_phrase(self, phrase):
        self.terms = phrase[1:-1].split(' ')
        self.type = "phrase"
        if self.terms == ['']:
            raise EmptyQuery()

    def parse_cnf(self, cnf):
        self.type = "cnf"
        self.clauses = [clause.split('|') for clause in cnf.split(' ') 
                if clause != '']

class SearchResult:
    def __init__(self, docs = {}, negation = False):
        self.docs = docs
        self.negation = negation

class Searcher:
    def __init__(self, indexer):
        self.indexer = indexer

    def search(self, s):
        query = Query(s)
        if query.type == "cnf":
            results = self.search_cnf(query)
            if results.negation:
                docs = self.subtract_from_uni(self.indexer.document_count + 1, results.docs)
            else:
                docs = results.docs
        else:
            docs = []

        return list(map(self.indexer.get_title, docs))

    def search_cnf(self, query):
        clause_results = [self.search_clause(clause)
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
            return SearchResult(self.indexer.get_posting(term[1:]), True)
        else:
            return SearchResult(self.indexer.get_posting(term), False)

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
            d1 = res1.docs
            d2 = res2.docs
            i1 = i2 = 0
            res = []
            while i1 < len(d1) and i2 < len(d2):
                if d1[i1] < d2[i2]:
                    res.append(d1[i1])
                    i1 += 1
                elif d1[i1] > d2[i2]:
                    res.append(d2[i2])
                    i2 += 1
                else:
                    res.append(d1[i1])
                    i1 += 1
                    i2 += 1
            return SearchResult(res + d1[i1:] + d2[i2:], False)

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
            d1 = iter(res1.docs)
            d2 = iter(res2.docs)
            res = []
            try:
                e1 = d1.__next__()
                e2 = d2.__next__()
                while True:
                    if e1 < e2:
                        e1 = d1.__next__()
                    elif e1 > e2:
                        e2 = d2.__next__()
                    else:
                        res.append(e1)
                        e1 = d1.__next__()
                        e2 = d2.__next__()
            except StopIteration:
                return SearchResult(res, False)

    def subtract_from_uni(self, document_count, d):
        res = []
        start = 1
        for n in d:
            res += range(start,n)
            start = n+1
        res += range(start, document_count)
        return res

    def subtract(self, d1, d2):
        """subtracts two lists in O(m + n) time."""
        # x \ y
        res = []
        i1 = i2 = 0
        while i1 < len(d1) and i2 < len(d2):
            if d1[i1] < d2[i2]:
                res.append(d1[i1])
                i1 += 1
            elif d1[i1] > d2[i2]:
                i2 += 1
            else:
                i1 += 1
                i2 += 1
        return res + d1[i1:]

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
