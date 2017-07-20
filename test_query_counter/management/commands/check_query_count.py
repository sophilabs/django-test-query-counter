from django.core.management import BaseCommand, CommandError

from test_query_counter.apps import RequestQueryCountConfig
from test_query_counter.query_count import QueryCountEvaluator


class Command(BaseCommand):

    INCREASE_THRESHOLD = 10  # Threshold in percentage

    help = 'Checks if the API query_count has increased since the last run. ' \
           'Query count is measured per test case, and per API call.'

    CURRENT_QUERY_COUNT = 'reports/query_count.json'

    def add_arguments(self, parser):
        super().add_arguments(parser)
        parser.add_argument('--last-count-file',
                            dest='last_count_file',
                            help='JSON summary file to compare against.',
                            required=True)

        summary_path = RequestQueryCountConfig.get_setting('SUMMARY_PATH')
        parser.add_argument('--query-count-file',
                            dest='query_count_file',
                            help='JSON summary file for current run.',
                            default=summary_path)

        help_msg = 'Threshold tolerance, which is computed in percentage. ' \
                   'Defaults to {}%%'.format(self.INCREASE_THRESHOLD)
        parser.add_argument('--query-count-threhold',
                            dest='query_count_threshold',
                            type=float, default=self.INCREASE_THRESHOLD,
                            help=help_msg)

    def handle(self, *args, **options):
        with open(options['query_count_file']) as current_file, \
                open(options['last_count_file']) as last_file:
            violations = QueryCountEvaluator(options['query_count_threshold'],
                                             current_file, last_file).run()

            if violations:
                raise CommandError('There was at least one test with an API '
                                   'call excedding the allowed threshold.')
