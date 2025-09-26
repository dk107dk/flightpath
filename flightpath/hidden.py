import traceback


#
# these files need to be referenced so they are found by PyInstaller
# we do it with hiddenimports in the spec file too, but it has been a
# challenge. very possibly we can take the backends out of this class
# but it's not certain and now isn't the time to dig more.
#
class Hidden:

    def __init__(self, skip=True) -> None:
        try:
            import paramiko
            import boto3
            import botocore
            import azure.storage.blob
            import google.cloud.storage
        except ImportError:
            print(traceback.format_exc())
        #
        # internal backends
        #
        try:
            from csvpath.util.s3.s3_nos import S3Do
            from csvpath.util.s3.s3_data_reader import S3DataReader
            from csvpath.util.s3.s3_data_writer import S3DataWriter
            from csvpath.util.s3.s3_xlsx_data_reader import S3XlsxDataReader
            from csvpath.util.s3.s3_utils import S3Utils
            from csvpath.util.sftp.sftp_nos import SftpDo
            from csvpath.util.sftp.sftp_data_reader import SftpDataReader
            from csvpath.util.sftp.sftp_data_writer import SftpDataWriter
            from csvpath.util.sftp.sftp_xlsx_data_reader import SftpXlsxDataReader
            from csvpath.util.sftp.sftp_config import SftpConfig
            from csvpath.util.azure.azure_nos import AzureDo
            from csvpath.util.azure.azure_utils import AzureUtility
            from csvpath.util.azure.azure_data_reader import AzureDataReader
            from csvpath.util.azure.azure_data_writer import AzureDataWriter
            from csvpath.util.azure.azure_xlsx_data_reader import AzureXlsxDataReader
            from csvpath.util.gcs.gcs_nos import GcsDo
            from csvpath.util.gcs.gcs_utils import GcsUtility
            from csvpath.util.gcs.gcs_data_reader import GcsDataReader
            from csvpath.util.gcs.gcs_data_writer import GcsDataWriter
            from csvpath.util.gcs.gcs_xlsx_data_reader import GcsXlsxDataReader
        except ImportError:
            print(traceback.format_exc())
        #
        # results readers
        #
        try:
            from csvpath.managers.results.readers.file_errors_reader import FileErrorsReader
            from csvpath.managers.results.readers.file_printouts_reader import FilePrintoutsReader
            from csvpath.managers.results.readers.file_lines_reader import FileLinesReader
            from csvpath.managers.results.readers.file_unmatched_reader import FileUnmatchedReader
        except ImportError:
            print(traceback.format_exc())
        #
        # integrations
        #
        try:
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
            from csvpath.managers.integrations.ol.file_listener_ol import OpenLineageFileListener
            from csvpath.managers.integrations.ol.paths_listener_ol import OpenLineagePathsListener
            from csvpath.managers.integrations.ol.result_listener_ol import OpenLineageResultListener
            from csvpath.managers.integrations.ol.results_listener_ol import OpenLineageResultsListener
            from csvpath.managers.integrations.slack.sender import SlackSender
        except ImportError:
            print(traceback.format_exc())


