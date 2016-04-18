import mock
import unittest
from contextlib import nested

from exporters.export_formatter.json_export_formatter import JsonExportFormatter
from exporters.records.base_record import BaseRecord
from exporters.writers.gstorage_writer import GStorageWriter

from .utils import meta


class GStorageWriterTest(unittest.TestCase):
    def test_write(self):
        data = [
            {'name': 'Roberto', 'birthday': '12/05/1987'},
            {'name': 'Claudia', 'birthday': '21/12/1985'},
        ]
        items_to_write = [BaseRecord(d) for d in data]
        options = {
            'name': 'exporters.writers.gstorage_writer.GStorageWriter',
            'options': {
                'project': 'some-project-666',
                'bucket': 'bucket-777',
                'credentials': {
                    "type": "service_account",
                    "private_key_id": "xxx",
                    "private_key": "yyy",
                },
                'filebase': 'tests/',
            }
        }

        with mock.patch('gcloud.storage.Client.from_service_account_json') as mocked:
            writer = GStorageWriter(
                options, meta(), export_formatter=JsonExportFormatter(dict()))
            writer.write_batch(items_to_write)
            writer.flush()
            writer.close()
            mocked.assert_has_calls([('().bucket().blob().upload_from_file',
                                      (mock.ANY,))])

    def test_init_from_resource(self):
        options = {
            'name': 'exporters.writers.gstorage_writer.GStorageWriter',
            'options': {
                'project': 'some-project-666',
                'bucket': 'bucket-777',
                'filebase': 'tests/',
            }
        }
        env = {'EXPORTERS_GSTORAGE_CREDS_RESOURCE': 'a:b'}
        with nested(mock.patch.dict('os.environ', env),
                    mock.patch('pkg_resources.resource_string', return_value='{}'),
                    mock.patch('gcloud.storage.Client.from_service_account_json')):
            GStorageWriter(options, meta(), export_formatter=JsonExportFormatter(dict()))

    def test_init_fails_with_bad_resource(self):
        options = {
            'name': 'exporters.writers.gstorage_writer.GStorageWriter',
            'options': {
                'project': 'some-project-666',
                'bucket': 'bucket-777',
                'filebase': 'tests/',
            }
        }
        env = {'EXPORTERS_GSTORAGE_CREDS_RESOURCE': 'a:b'}
        with nested(self.assertRaisesRegexp(ImportError, 'No module named a'),
                    mock.patch.dict('os.environ', env)):
            GStorageWriter(options, meta(), export_formatter=JsonExportFormatter(dict()))
