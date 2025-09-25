
#
# file operations interface
#
from csvpath.util.s3.s3_nos import S3Do
from csvpath.util.s3.s3_data_reader import S3DataReader
from csvpath.util.s3.s3_data_writer import S3DataWriter
from csvpath.util.s3.s3_xlsx_data_reader import S3XlsxDataReader
from csvpath.util.sftp.sftp_nos import SftpDo
from csvpath.util.sftp.sftp_data_reader import SftpDataReader
from csvpath.util.sftp.sftp_data_writer import SftpDataWriter
from csvpath.util.sftp.sftp_xlsx_data_reader import SftpXlsxDataReader
from csvpath.util.azure.azure_nos import AzureDo
from csvpath.util.azure.azure_data_reader import AzureDataReader
from csvpath.util.azure.azure_data_writer import AzureDataWriter
from csvpath.util.azure.azure_xlsx_data_reader import AzureXlsxDataReader
from csvpath.util.gcs.gcs_nos import GcsDo
from csvpath.util.gcs.gcs_data_reader import GcsDataReader
from csvpath.util.gcs.gcs_data_writer import GcsDataWriter
from csvpath.util.gcs.gcs_xlsx_data_reader import GcsXlsxDataReader

#
# files readers facade
#
from csvpath.managers.results.readers.file_errors_reader import FileErrorsReader
from csvpath.managers.results.readers.file_printouts_reader import FilePrintoutsReader
from csvpath.managers.results.readers.file_lines_reader import FileLinesReader
from csvpath.managers.results.readers.file_unmatched_reader import FileUnmatchedReader

#
# integrations
#
from csvpath.managers.integrations.webhook.webhook_results_listener import WebhookResultsListener
from csvpath.managers.integrations.scripts.scripts_results_listener import ScriptsResultsListener
from csvpath.managers.integrations.sql.sql_file_listener import SqlFileListener
from csvpath.managers.integrations.sql.sql_paths_listener import SqlPathsListener
from csvpath.managers.integrations.sql.sql_result_listener import SqlResultListener
from csvpath.managers.integrations.sql.sql_results_listener import SqlResultsListener
from csvpath.managers.integrations.sqlite.sqlite_results_listener import SqliteResultsListener
from csvpath.managers.integrations.sqlite.sqlite_result_listener import SqliteResultListener
from csvpath.managers.files.files_listener import FilesListener
from csvpath.managers.paths.paths_listener import PathsListener
from csvpath.managers.integrations.otlp.otlp_result_listener import OpenTelemetryResultListener
from csvpath.managers.integrations.otlp.otlp_results_listener import OpenTelemetryResultsListener
from csvpath.managers.integrations.otlp.otlp_error_listener import OpenTelemetryErrorListener
from csvpath.managers.integrations.otlp.otlp_paths_listener import OpenTelemetryPathsListener
from csvpath.managers.integrations.otlp.otlp_file_listener import OpenTelemetryFileListener
from csvpath.managers.integrations.sftp.sftp_sender import SftpSender
from csvpath.managers.integrations.sftpplus.sftpplus_listener import SftpPlusListener
from csvpath.managers.integrations.ckan.ckan_listener import CkanListener
"""
from csvpath.managers.integrations.ol.file_listener_ol import OpenLineageFileListener
from csvpath.managers.integrations.ol.paths_listener_ol import OpenLineagePathsListener
from csvpath.managers.integrations.ol.result_listener_ol import OpenLineageResultListener
from csvpath.managers.integrations.ol.results_listener_ol import OpenLineageResultsListener
from csvpath.managers.integrations.slack.sender import SlackSender
"""

#
# these files need to be referenced so they are found by PyInstaller
#
class Hidden:

    def __init__(self, skip=True) -> None:
        if skip:
            return
        #
        # backends
        #
        try:
            S3Do()
        except Exception:
            ...
        try:
            S3DataReader()
        except Exception:
            ...
        try:
            S3DataWriter()
        except Exception:
            ...
        try:
            S3XlsxDataReader()
        except Exception:
            ...
        try:
            SftpDo()
        except Exception:
            ...
        try:
            SftpDataReader()
        except Exception:
            ...
        try:
            SftpDataWriter()
        except Exception:
            ...
        try:
            SftpXlsxDataReader()
        except Exception:
            ...
        try:
            AzureDo()
        except Exception:
            ...
        try:
            AzureDataReader()
        except Exception:
            ...
        try:
            AzureDataWriter()
        except Exception:
            ...
        try:
            AzureXlsxDataReader()
        except Exception:
            ...
        try:
            GcsDo()
        except Exception:
            ...
        try:
            GcsDataReader()
        except Exception:
            ...
        try:
            GcsDataWriter()
        except Exception:
            ...
        try:
            GcsXlsxDataReader()
        except Exception:
            ...
        #
        # results readers
        #
        try:
            FileErrorsReader()
        except Exception:
            ...
        try:
            FilePrintoutsReader()
        except Exception:
            ...
        try:
            FileLinesReader()
        except Exception:
            ...
        try:
            FileUnmatchedReader()
        except Exception:
            ...
        #
        # integrations
        #
        try:
            WebhookResultsListener()
        except Exception:
            ...
        try:
            ScriptsResultsListener()
        except Exception:
            ...
        try:
            SqlFileListener()
        except Exception:
            ...
        try:
            SqlPathsListener()
        except Exception:
            ...
        try:
            SqlResultListener()
        except Exception:
            ...
        try:
            SqlResultsListener()
        except Exception:
            ...
        try:
            SqliteResultsListener()
        except Exception:
            ...
        try:
            SqliteResultListener()
        except Exception:
            ...
        try:
            FilesListener()
        except Exception:
            ...
        try:
            PathsListener()
        except Exception:
            ...
        try:
            OpenTelemetryResultListener()
        except Exception:
            ...
        try:
            OpenTelemetryResultsListener()
        except Exception:
            ...
        try:
            OpenTelemetryErrorListener()
        except Exception:
            ...
        try:
            OpenTelemetryPathsListener()
        except Exception:
            ...
        try:
            OpenTelemetryFileListener()
        except Exception:
            ...
        try:
            SftpSender()
        except Exception:
            ...
        try:
            SftpPlusListener()
        except Exception:
            ...
        try:
            CkanListener()
        except Exception:
            ...
        #
        #
        # OpenLineage has a dependency on numpy that is apparently also hidden.
        # planning to test to see if we can do OL w/o numpy; otherwise, we'll need
        # to explicitly add it.
        #
        try:
            OpenLineageFileListener()
        except Exception:
            ...
        try:
            OpenLineagePathsListener()
        except Exception:
            ...
        try:
            OpenLineageResultListener()
        except Exception:
            ...
        try:
            OpenLineageResultsListener()
        except Exception:
            ...
        try:
            SlackSender()
        except Exception:
            ...


