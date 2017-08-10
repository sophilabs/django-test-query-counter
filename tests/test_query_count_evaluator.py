import json
import re
from io import StringIO
from unittest import TestCase

from test_query_counter.query_count import QueryCountEvaluator


class TestQueryCountEvaluator(TestCase):

    @staticmethod
    def make(test_cases):
        return StringIO(json.dumps({
            'test_cases': test_cases,
            'total': 0
        }))

    def setUp(self):
        self.evaluator = QueryCountEvaluator(10, self.make([]), self.make([]),
                                             StringIO())

    def test_empty(self):
        violations = self.evaluator.compare_test_cases('test-case-id', [], [])
        self.assertFalse(any(violations))

    def test_new_api_call(self):
        violations = self.evaluator.compare_test_cases(
            'test-case-id',
            [
                {
                    "method": "post",
                    "path": "/api/events",
                    "total": 45
                }
            ],
            []
        )
        self.assertFalse(any(violations))

    def test_api_call_removed(self):
        violations = self.evaluator.compare_test_cases(
            'test-case-id',
            [],
            [
                {
                    "method": "post",
                    "path": "/api/events",
                    "total": 45
                }
            ],
        )
        self.assertFalse(any(violations))

    def test_api_below_threshold_limit(self):
        violations = self.evaluator.compare_test_cases(
            'test-case-id',
            [
                {
                    "method": "post",
                    "path": "/api/events",
                    "total": 90
                }
            ],
            [
                {
                    "method": "post",
                    "path": "/api/events",
                    "total": 100
                }
            ]
        )
        self.assertFalse(any(violations))

    def test_on_threshold_limit(self):
        violations = self.evaluator.compare_test_cases(
            'test-case-id',
            [
                {
                    "method": "post",
                    "path": "/api/events",
                    "total": 110
                }
            ],
            [
                {
                    "method": "post",
                    "path": "/api/events",
                    "total": 100
                }
            ]
        )
        self.assertFalse(any(violations))

    def test_above_threshold_limit(self):
        violations = self.evaluator.compare_test_cases(
            'test-case-id',
            [
                {
                    "method": "post",
                    "path": "/api/events",
                    "total": 120
                }
            ],
            [
                {
                    "method": "post",
                    "path": "/api/events",
                    "total": 100
                }
            ]
        )
        violation = next(violations)

        self.assertEqual(violation.test_case_id, 'test-case-id')
        self.assertEqual(violation.method, 'post')
        self.assertEqual(violation.path, '/api/events')
        self.assertEqual(violation.threshold, 110)
        self.assertEqual(violation.total, 120)

    def test_one_above_one_below(self):
        violations = list(self.evaluator.compare_test_cases(
            'test-case-id',
            [
                {
                    "method": "post",
                    "path": "/api/events",
                    "total": 100
                },
                {
                    "method": "get",
                    "path": "/api/events",
                    "total": 120
                }
            ],
            [
                {
                    "method": "post",
                    "path": "/api/events",
                    "total": 100
                },
                {
                    "method": "get",
                    "path": "/api/events",
                    "total": 100
                }
            ]
        ))

        self.assertEqual(len(violations), 1)
        self.assertEqual(violations[0].method, 'get')

    def test_run_wo_violations(self):
        violations = self.evaluator.run()
        self.assertEqual(len(violations), 0)
        self.assertIsNotNone(
            re.search('All Tests API Queries are below the allowed',
                      self.evaluator.stream.getvalue()))

    def test_run_w_violations(self):
        evaluator = QueryCountEvaluator(
            10,
            self.make([
                {
                    "id": "test-case-1",
                    "queries": [
                        {
                            "method": "post",
                            "path": "path/1",
                            "total": 120
                        }
                    ],
                    "total": 120
                },
                {
                    "id": "test-case-2",
                    "queries": [
                        {
                            "method": "get",
                            "path": "path/2",
                            "total": 60
                        }
                    ],
                    "total": 60
                },
                {
                    "id": "test-3",
                    "queries": [
                        {
                            "method": "put",
                            "path": "path/3",
                            "total": 5
                        }
                    ],
                    "total": 5
                }
            ]),
            self.make([
                {
                    "id": "test-case-1",
                    "queries": [
                        {
                            "method": "post",
                            "path": "path/1",
                            "total": 100
                        }
                    ],
                    "total": 100
                },
                {
                    "id": "test-case-2",
                    "queries": [
                        {
                            "method": "get",
                            "path": "path/2",
                            "total": 50
                        }
                    ],
                    "total": 50
                },
                {
                    "id": "test-3",
                    "queries": [
                        {
                            "method": "put",
                            "path": "path/3",
                            "total": 5
                        }
                    ],
                    "total": 5
                }
            ]),
            StringIO()
        )

        violations = evaluator.run()
        self.assertEqual(len(violations), 2)
        self.assertIsNotNone(
            re.search(r'calls that exceeded threshold',
                      evaluator.stream.getvalue())
        )
        self.assertIsNotNone(
            re.search(r'In test case test-case-1',
                      evaluator.stream.getvalue())
        )
        self.assertIsNotNone(
            re.search(r'In test case test-case-2',
                      evaluator.stream.getvalue())
        )
        self.assertIsNone(
            re.search(r'In test case test-3',
                      evaluator.stream.getvalue())
        )
