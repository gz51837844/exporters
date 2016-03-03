from collections import Counter

from dropbox import files
from dropbox.files import CommitInfo

from exporters.default_retries import retry_long
from exporters.writers.filebase_base_writer import FilebaseBaseWriter


class DropboxWriter(FilebaseBaseWriter):
    """
    Writes items to dropbox folder.
    options available

        - access_token (str)
            Oauth access token for Dropbox api.

        - filebase (str)
            Base path to store the items in the share.

    """
    supported_options = {
        'access_token': {'type': basestring, 'env_fallback': 'EXPORTERS_DROPBOXWRITER_TOKEN'},
    }

    def __init__(self, options, *args, **kw):
        import dropbox
        super(DropboxWriter, self).__init__(options, *args, **kw)
        access_token = self.read_option('access_token')
        self.logger.info('DroboxWriter has been initiated.'
                         'Writing to folder {}'.format(self.filebase))
        self.writer_metadata['files_counter'] = Counter()
        self.client = dropbox.Dropbox(access_token)

    def write(self, dump_path, group_key=None):
        if group_key is None:
            group_key = []
        self._write_file(dump_path, group_key)

    @retry_long
    def _write_file(self, dump_path, group_key, file_name=None):
        filebase_path, file_name = self.create_filebase_name(group_key, file_name=file_name)
        with open(dump_path, 'r') as f:
            session_id = self.client.files_upload_session_start('')
            current_offset = 0
            while True:
                data = f.read(2**20)
                if not data:
                    break
                self.client.files_upload_session_append(data, session_id.session_id, current_offset)
                current_offset += len(data)
            cursor = files.UploadSessionCursor(session_id.session_id, current_offset)
            self.client.files_upload_session_finish('', cursor, CommitInfo(path='{}/{}'.format(filebase_path, file_name)))
        self.writer_metadata['files_counter'][filebase_path] += 1

    def get_file_suffix(self, path, prefix):
        number_of_keys = self.writer_metadata['files_counter'].get(path, 0)
        suffix = '{}'.format(str(number_of_keys))
        return suffix
