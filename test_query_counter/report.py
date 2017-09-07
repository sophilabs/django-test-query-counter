import json
import shutil
from contextlib import ExitStack
from os import makedirs, path


class Reporter(object):
    @classmethod
    def ensure_dir(cls, output_dir):
        makedirs(output_dir, exist_ok=True)

    @classmethod
    def write_index(cls, query_count_file, output_dir):
        output_index = path.join(output_dir, 'index.html')

        with ExitStack() as stack:
            output = stack.enter_context(
                open(output_index, encoding='utf-8', mode='w')
            )
            template_path = path.join(path.dirname(__file__),
                                      'templates', 'report-index.html')
            template_file = stack.enter_context(
                open(template_path, encoding='utf-8')
            )
            report = json.dumps(json.load(query_count_file))
            formatted_file = template_file.read().format(report=report)
            output.write(formatted_file)

    @classmethod
    def write_assets(cls, output_dir):
        shutil.copyfile(
            path.join(path.dirname(__file__), 'static', 'app.js'),
            path.join(output_dir, 'app.js')
        )

    @classmethod
    def process_file(cls, query_count_file, output_dir):
        cls.ensure_dir(output_dir)
        cls.write_index(query_count_file, output_dir)
        cls.write_assets(output_dir)
