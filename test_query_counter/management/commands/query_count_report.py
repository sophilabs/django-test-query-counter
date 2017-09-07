from django.core.management import BaseCommand
from test_query_counter.apps import RequestQueryCountConfig
from test_query_counter.report import Reporter


class Command(BaseCommand):

    help = 'Generates an HTML Report file with the query report'

    CURRENT_QUERY_COUNT = 'reports/query_count_detail.json'

    def add_arguments(self, parser):
        super().add_arguments(parser)
        summary_path = RequestQueryCountConfig.get_setting('SUMMARY_PATH')
        parser.add_argument(dest='query_count_file',
                            help='JSON summary file for current run.',
                            default=summary_path)
        parser.add_argument('--output-dir', '-o',
                            dest='output',
                            help='Output directory to generate report',
                            default='reports')

    def handle(self, *args, **options):
        with open(options['query_count_file']) as current_file:
            Reporter.process_file(current_file, options['output'])
