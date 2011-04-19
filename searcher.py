#!/usr/bin/python

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

class QueryTest(unittest.TestCase):
    def test_phrase(self):
        q = Query('"foo bar baz"')
        self.assertEqual(q.terms, ['foo', 'bar', 'baz'])
        self.assertEqual(q.type, 'phrase')

    def test_single_word(self):
        q = Query('"term1"')
        self.assertEqual(q.terms, ['term1'])
        self.assertEqual(q.type, 'phrase')

    def test_cnf(self):
        q = Query("foo bar|baz ~not term1|~term2")
        self.assertEqual(q.clauses, [['foo'], ['bar', 'baz'], ['~not'], ['term1', '~term2']])
        self.assertEqual(q.type, 'cnf')
    
    def test_single_word(self):
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

if __name__ == "__main__":
   unittest.main()
