import json
import os
from sys import maxsize, stderr

from django.db import DEFAULT_DB_ALIAS, connections
from django.test.utils import CaptureQueriesContext
from django_jenkins.runner import CITestSuiteRunner
from rest_framework.test import APIClient, APITestCase, APITransactionTestCase


def skip_query_count():
    """
    Unconditionally skip a test query count.
    """
    def decorator(test_item):
        test_item.__querycount_skip__ = True
        return test_item

    return decorator


class TestResultQueryContainer(object):
    """Stores all the queries from a Test Run, contained in a TestResult"""
    def __init__(self):
        self.queries_by_testcase = dict()
        self.total = 0

    def add(self, test_case_id, queries):
        """
        Merge the queries from a test case
        :param test_case_id: identifier for test case (This is usually the
            full name of the test method, including the module and class name)
        :param queries: TestCaseQueries for this test case
        """
        existing_query_container = self.queries_by_testcase.get(
            test_case_id,
            TestCaseQueryContainer()
        )
        existing_query_container.merge(queries)
        self.queries_by_testcase[test_case_id] = existing_query_container
        self.total += existing_query_container.total

    @classmethod
    def test_case_json(cls, test_case_id, query_container, detail):
        representation = query_container.get_json(detail)
        representation['id'] = test_case_id
        return representation

    def get_json(self, detail):
        return {
            'total': self.total,
            'test_cases': [
                self.test_case_json(test_case_id, queries, detail)
                for test_case_id, queries in self.queries_by_testcase.items()
            ]
        }


class TestCaseQueryContainer(object):
    """Stores queries by API method for a particular test case"""
    def __init__(self):
        self.queries_by_api_method = dict()
        self.total = 0

    def add_by_key(self, api_method_key, queries):
        """
        Appends queries to a certain api method
        :param api_method_key: tuple (method, path)
        :param queries: list of queries
        """
        existing_queries = self.queries_by_api_method.get(api_method_key, [])
        self.queries_by_api_method[api_method_key] = queries + existing_queries
        self.total += len(queries)

    def add(self, method, path, queries):
        """Agregates the queries to the captured queries dict"""
        key = (method, path)
        self.add_by_key(key, queries)

    def merge(self, test_case_container):
        """
        Merges the queries from another test case container in this object
        :param test_case_container: an existing test Container
        """
        for key, queries in test_case_container.queries_by_api_method.items():
            self.add_by_key(key, queries)

    @classmethod
    def api_call_json(cls, api_call, queries, detail):
        """
        Returns a json representation of a single API Call
        :param api_call: API call tuple (method, path)
        :param queries: list of queries
        :param detail: if True, the list of queries is returned
        :return: Dictionary
        """
        method, path = api_call
        result = {
            'method': method,
            'path': path,
            'total': len(queries),
        }
        if detail:
            result['queries'] = queries
        return result

    def get_json(self, detail):
        """Returns a JSON representation of the object"""
        return {
            'total': self.total,
            'queries': [
                self.api_call_json(api_call, queries, detail)
                for api_call, queries in self.queries_by_api_method.items()
            ]
        }


class QueryCountAPIClient(APIClient):
    """
    Makes the API Client to capture queries. Agregates queries for URL and Path
    """

    def __init__(self, *args, **kwargs):
        self.api_queries = TestCaseQueryContainer()
        super().__init__(*args, **kwargs)

    @property
    def connection(self):
        """
        Default connection
        """
        return connections[DEFAULT_DB_ALIAS]

    # Overloaded APIClient methods

    def get(self, path, data=None, **extra):
        with CaptureQueriesContext(self.connection) as context:
            response = super().get(path, data, **extra)
            self.api_queries.add('get', path, context.captured_queries)
            return response

    def post(self, path, data=None, **extra):
        with CaptureQueriesContext(self.connection) as context:
            response = super().post(path, data, **extra)
            self.api_queries.add('post', path, context.captured_queries)
            return response

    def put(self, path, data=None, **extra):
        with CaptureQueriesContext(self.connection) as context:
            response = super().put(path, data, **extra)
            self.api_queries.add('put', path, context.captured_queries)
            return response

    def patch(self, path, data=None, **extra):
        with CaptureQueriesContext(self.connection) as context:
            response = super().patch(path, data, **extra)
            self.api_queries.add('patch', path, context.captured_queries)
            return response

    def delete(self, path, data=None, **extra):
        with CaptureQueriesContext(self.connection) as context:
            response = super().delete(path, data, **extra)
            self.api_queries.add('delete', path, context.captured_queries)
            return response

    def options(self, path, data=None, **extra):
        with CaptureQueriesContext(self.connection) as context:
            response = super().options(path, data, **extra)
            self.api_queries.add('options', path, context.captured_queries)
            return response


class _QueryCountTestCaseMixin(object):
    def count_queries_test_method(self, run_method, *args, **kwargs):
        test_method = getattr(self, self._testMethodName)
        if (getattr(self.__class__, "__querycount_skip__", False) or
                getattr(test_method, "__querycount_skip__", False)):
            # Skipped test: don't store queries
            return run_method(*args, **kwargs)

        result = run_method(*args, **kwargs)

        if result:
            all_queries = getattr(result, 'queries',
                                  TestResultQueryContainer())
            all_queries.add(self.id(), self.client.api_queries)
            setattr(result, 'queries', all_queries)

        return result


class APIQueryCountTransactionTestCase(APITransactionTestCase,
                                       _QueryCountTestCaseMixin):
    """
    Derives APITransactionTestCase and counts Query Count per API, per test
    """
    client_class = QueryCountAPIClient

    def run(self, *args, **kwargs):
        return self.count_queries_test_method(super().run, *args, **kwargs)


class APIQueryCountTestCase(APITestCase, _QueryCountTestCaseMixin):
    """
    Derives APITestCase and counts Query Count per API, per test
    """
    client_class = QueryCountAPIClient

    def run(self, *args, **kwargs):
        return self.count_queries_test_method(super().run, *args, **kwargs)


class QueryCountCITestSuiteRunner(CITestSuiteRunner):
    SUMMARY_FILE = 'query_count.json'
    DETAIL_FILE = 'query_count_detail.json'

    def run_suite(self, *args, **kwargs):
        """
        Same as run_suite but, dumps the JSON in the output_dir
        """
        test_result = super().run_suite(*args, **kwargs)

        filename = os.path.join(self.output_dir, self.SUMMARY_FILE)
        with open(filename, 'w') as json_file:
            json.dump(test_result.queries.get_json(detail=False), json_file,
                      ensure_ascii=False, indent=4, sort_keys=True)

        filename_detailed = os.path.join(self.output_dir, self.DETAIL_FILE)
        with open(filename_detailed, 'w') as json_file:
            json.dump(test_result.queries.get_json(detail=True), json_file,
                      ensure_ascii=False, indent=4, sort_keys=True)

        return test_result


class Violation(object):
    def __init__(self, test_case_id, method, path, threshold, total):
        self.test_case_id = test_case_id
        self.method = method
        self.path = path
        self.threshold = threshold
        self.total = total


class QueryCountEvaluator(object):
    def __init__(self, threshold, current_file, last_file, stream=stderr):
        """
        Initializes the Evaluator, which writes t
        :param threshold: Threshold in percentage (e.g. 10)
        :param current_file: stream with the about-to-commit API Calls result
        :param last_file: stream with the last "accepted" API calls to compare
        :param stream: steam to write into (default: stderr)
        """
        self.threshold = threshold
        self.current = json.load(current_file)
        self.last = json.load(last_file)
        self.stream = stream

    @classmethod
    def default_test_case_element(cls, test_case_id):
        return {
            'id': test_case_id,
            'queries': [],
            'total': 0
        }

    def list_violations(self):
        last_test_cases = {
            test_case['id']: test_case
            for test_case in self.last['test_cases']
        }

        for element in self.current['test_cases']:
            test_case_id = element['id']
            last_test_cases_queries = last_test_cases.get(
                test_case_id,
                self.default_test_case_element(test_case_id)
            )
            for violation in self.compare_test_cases(
                    test_case_id,
                    element['queries'],
                    last_test_cases_queries['queries']):
                yield violation

    def run(self):
        """
        Main method. Compares to JSON files and prints in the stream the
        list of API Calls (Violations) that ocurred between the current run
        and the last run.
        :return: a list of the violations ocurred
        """
        violations = list(self.list_violations())
        if any(violations):
            self.stream.write('There are test cases with API '
                              'calls that exceeded threshold:\n\n')

        for violation in violations:
            msg = '\tIn test case {}, {} {}. Expected at most {} queries but' \
                  ' got {} queries' \
                  '\n'.format(violation.test_case_id, violation.method,
                              violation.path, violation.threshold,
                              violation.total)
            self.stream.write(msg)

        if not any(violations):
            self.stream.write('All Tests API Queries are below the allowed '
                              'threshold.\n')

        self.stream.flush()

        return violations

    def compare_test_cases(self, test_case_id, current_queries, last_queries):
        """
        Compares the queries from a test case
        :param test_case_id: the name of the test case. Usually includes the
             class and the method name
        :param current_queries: API calls query list for the current run
        :param last_queries: API calls query for the last run
        :return: a list of Violation objects for any API Call that exceeded
            threshold
        """
        last_queries_dict = {
            (element['method'], element['path']): element['total']
            for element in last_queries
        }

        def get_last_queries(query_element):
            key = (query_element['method'], query_element['path'])
            return last_queries_dict.get(key, maxsize)

        def get_threshold(query_element):
            max_factor = (self.threshold / 100.0 + 1)
            return round(get_last_queries(query_element) * max_factor)

        def violates_threshold(query_element):
            return query_element['total'] > get_threshold(query_element)

        return (Violation(test_case_id, element['method'], element['path'],
                          get_threshold(element), element['total'])
                for element in current_queries
                if violates_threshold(element))
