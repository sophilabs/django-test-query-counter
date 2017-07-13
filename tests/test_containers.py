from django.test import TestCase

from request_query_count.query_count import (TestCaseQueryContainer,
                                             TestResultQueryContainer)


class QueryCountContainersTestCase(TestCase):

    def test_case_add(self):
        container = TestCaseQueryContainer()
        self.assertEqual(container.total, 0)

        container.add(
            'get',
            'request_path',
            [
                {'sql': 'SELECT * FROM some_table', 'time': 0.02},
                {'sql': 'SELECT * FROM some_other_table', 'time': 0.01}
            ]
        )
        self.assertEqual(container.total, 2)

        container.add(
            'post',
            'request_path',
            [
                {'sql': 'SELECT * FROM some_table_3', 'time': 0.02},
            ]
        )
        self.assertEqual(container.total, 3)

    def test_case_empty_json(self):
        self.assertEqual(TestCaseQueryContainer().get_json(False), {
            'total': 0,
            'queries': []
        })

    def test_case_non_empty_json(self):
        container = TestCaseQueryContainer()
        container.add(
            'options',
            'request_path',
            [
                {'sql': 'SELECT * FROM some_table', 'time': 0.02},
            ]
        )

        self.assertEqual(container.get_json(detail=False), {
            'total': 1,
            'queries': [
                {
                    'method': 'options',
                    'path': 'request_path',
                    'total': 1
                }
            ]
        })

        self.assertEqual(container.get_json(detail=True), {
            'total': 1,
            'queries': [
                {
                    'method': 'options',
                    'path': 'request_path',
                    'total': 1,
                    'queries': [
                        {'sql': 'SELECT * FROM some_table', 'time': 0.02}
                    ]
                }
            ]
        })

    def test_case_merge(self):
        container = TestCaseQueryContainer()
        container.add(
            'delete',
            'request_path',
            [
                {'sql': 'SELECT * FROM some_table', 'time': 0.02},
            ]
        )
        container_2 = TestCaseQueryContainer()
        container_2.add(
            'delete',
            'request_path',
            [
                {'sql': 'SELECT * FROM some_othertable', 'time': 0.05},
            ]
        )

        container.merge(container_2)
        self.assertEqual(container.total, 2)
        self.assertEqual(
            len(container.queries_by_api_method.keys()),
            1
        )

    def test_result_empty(self):
        container = TestResultQueryContainer()
        self.assertEqual(container.total, 0)

    def test_result_add(self):
        result_container = TestResultQueryContainer()
        test_case_container = TestCaseQueryContainer()
        test_case_container.add(
            'delete',
            'some_path',
            [
                {'sql': 'SELECT * FROM a_table', 'time': 0.02},
            ]
        )
        result_container.add('some.test.test_function', test_case_container)
        self.assertEqual(result_container.total, 1)

        test_case_container = TestCaseQueryContainer()
        test_case_container.add(
            'patch',
            'other_path',
            [
                {'sql': 'SELECT * FROM a_table', 'time': 0.02},
            ]
        )
        result_container.add('some.test.test_other', test_case_container)
        self.assertEqual(result_container.total, 2)

    def test_result_empty_json(self):
        container = TestResultQueryContainer()
        self.assertEqual(container.get_json(detail=True), {
            'total': 0,
            'test_cases': []
        })

    def test_result_single_json(self):
        result_container = TestResultQueryContainer()
        test_case_container = TestCaseQueryContainer()
        test_case_container.add(
            'delete',
            'some_path',
            [
                {'sql': 'SELECT * FROM a_table', 'time': 0.02},
            ]
        )
        result_container.add('some.test.test_function', test_case_container)

        json_obj = result_container.get_json(detail=False)

        self.assertEqual(json_obj['total'], 1)
        self.assertEqual(len(json_obj['test_cases']), 1)
        self.assertEqual(
            json_obj['test_cases'][0]['id'],
            'some.test.test_function'
        )
