"""
 Imports to make sure the installer generator pulls these classes. they are used
 with dynamic loads making them invisible.

 These are all the current integrations as of May 1 2025.
"""


try:
    from csvpath.managers.paths.paths_listener import PathsListener
    PathsListener()
    from csvpath.managers.integrations.webhook.webhook_results_listener import WebhookResultsListener
    WebhookResultsListener()
    from csvpath.managers.integrations.scripts.scripts_results_listener import ScriptsResultsListener
    ScriptsResultsListener()
    from csvpath.managers.integrations.sql.sql_file_listener import SqlFileListener
    SqlFileListener()
    from csvpath.managers.integrations.sql.sql_paths_listener import SqlPathsListener
    SqlPathsListener()
    from csvpath.managers.integrations.sql.sql_result_listener import SqlResultListener
    SqlResultListener()
    from csvpath.managers.integrations.sql.sql_results_listener import SqlResultsListener
    SqlResultsListener()
    from csvpath.managers.integrations.sqlite.sqlite_result_listener import SqliteResultListener
    SqliteResultListener()
    from csvpath.managers.integrations.sqlite.sqlite_results_listener import SqliteResultsListener
    SqliteResultsListener()
    from csvpath.managers.files.files_listener import FilesListener
    FilesListener()
    from csvpath.managers.paths.paths_listener import PathsListener
    PathsListener()
    from csvpath.managers.integrations.otlp.otlp_result_listener import OpenTelemetryResultListener
    OpenTelemetryResultListener()
    from csvpath.managers.integrations.otlp.otlp_results_listener import OpenTelemetryResultsListener
    OpenTelemetryResultsListener()
    from csvpath.managers.integrations.otlp.otlp_error_listener import OpenTelemetryErrorListener
    OpenTelemetryErrorListener()
    from csvpath.managers.integrations.sftpplus.sftpplus_listener import SftpPlusListener
    SftpPlusListener()
    from csvpath.managers.integrations.ckan.ckan_listener import CkanListener
    CkanListener()
    #from csvpath.managers.integrations.ol.file_listener_ol import OpenLineageFileListener
    #OpenLineageFileListener()
    #from csvpath.managers.integrations.ol.paths_listener_ol import OpenLineagePathsListener
    #OpenLineagePathsListener()
    #from csvpath.managers.integrations.ol.result_listener_ol import OpenLineageResultListener
    #OpenLineageResultListener()
    #from csvpath.managers.integrations.ol.results_listener_ol import OpenLineageResultsListener
    #OpenLineageResultsListener()
    from csvpath.managers.integrations.slack.sender import SlackSender
    SlackSender()
    from csvpath.managers.integrations.sftp.sftp_sender import SftpSender
    SftpSender()
    #
    # data readers for backends
    #
    from csvpath.util.s3.s3_data_reader import S3DataReader
    S3DataReader(None)
    from csvpath.util.sftp.sftp_data_reader import SftpDataReader
    SftpDataReader(None)
    from csvpath.util.azure.azure_data_reader import AzureDataReader
    AzureDataReader(None)
    from csvpath.util.http.http_data_reader import HttpDataReader
    HttpDataReader(None)
    from csvpath.util.gcs.gcs_data_reader import GcsDataReader
    GcsDataReader(None)
    #
    # data writers for backends
    #
    from csvpath.util.s3.s3_data_writer import S3DataWriter
    S3DataWriter(path=None)
    from csvpath.util.sftp.sftp_data_writer import SftpDataWriter
    SftpDataWriter(path=None)
    from csvpath.util.azure.azure_data_writer import AzureDataWriter
    AzureDataWriter(path=None)
    from csvpath.util.gcs.gcs_data_writer import GcsDataWriter
    GcsDataWriter(path=None)
    #
    # readers for results files
    #
    from csvpath.managers.results.readers.file_errors_reader import FileErrorsReader
    FileErrorsReader()
    from csvpath.managers.results.readers.file_printouts_reader import FilePrintoutsReader
    FilePrintoutsReader()
    from csvpath.managers.results.readers.file_lines_reader import FileLinesReader
    FileLinesReader()
    from csvpath.managers.results.readers.file_unmatched_reader import FileUnmatchedReader
    FileUnmatchedReader()
except Exception: # pylint: disable=W0718
    ...

__version__ = "0.0.1"
