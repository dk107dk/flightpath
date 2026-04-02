"""
Imports to make sure the installer generator pulls these classes. they are used
with dynamic loads making them invisible.

These are all the current integrations as of May 1 2025.
"""

try:
    from csvpath.managers.paths.paths_listener import PathsListener  # noqa

    from csvpath.managers.integrations.webhook.webhook_results_listener import (  # noqa
        WebhookResultsListener,  # noqa
    )  # noqa
    from csvpath.managers.integrations.scripts.scripts_results_listener import (  # noqa
        ScriptsResultsListener,  # noqa
    )  # noqa

    from csvpath.managers.integrations.sql.sql_file_listener import SqlFileListener  # noqa

    from csvpath.managers.integrations.sql.sql_paths_listener import SqlPathsListener  # noqa

    from csvpath.managers.integrations.sql.sql_result_listener import SqlResultListener  # noqa

    from csvpath.managers.integrations.sql.sql_results_listener import (  # noqa
        SqlResultsListener,  # noqa
    )  # noqa

    from csvpath.managers.integrations.sqlite.sqlite_result_listener import (  # noqa
        SqliteResultListener,  # noqa
    )  # noqa

    from csvpath.managers.integrations.sqlite.sqlite_results_listener import (  # noqa
        SqliteResultsListener,  # noqa
    )  # noqa

    from csvpath.managers.files.files_listener import FilesListener  # noqa

    from csvpath.managers.integrations.otlp.otlp_result_listener import (  # noqa
        OpenTelemetryResultListener,  # noqa
    )  # noqa

    from csvpath.managers.integrations.otlp.otlp_results_listener import (  # noqa
        OpenTelemetryResultsListener,  # noqa
    )  # noqa

    from csvpath.managers.integrations.otlp.otlp_error_listener import (  # noqa
        OpenTelemetryErrorListener,  # noqa
    )  # noqa

    from csvpath.managers.integrations.sftpplus.sftpplus_listener import (  # noqa
        SftpPlusListener,  # noqa
    )  # noqa

    from csvpath.managers.integrations.ckan.ckan_listener import CkanListener  # noqa

    from csvpath.managers.integrations.slack.sender import SlackSender  # noqa

    from csvpath.managers.integrations.sftp.sftp_sender import SftpSender  # noqa

    #
    # data readers for backends
    #
    from csvpath.util.s3.s3_data_reader import S3DataReader  # noqa

    from csvpath.util.sftp.sftp_data_reader import SftpDataReader  # noqa

    from csvpath.util.azure.azure_data_reader import AzureDataReader  # noqa

    from csvpath.util.http.http_data_reader import HttpDataReader  # noqa

    from csvpath.util.gcs.gcs_data_reader import GcsDataReader  # noqa

    #
    # data writers for backends
    #
    from csvpath.util.s3.s3_data_writer import S3DataWriter  # noqa

    from csvpath.util.sftp.sftp_data_writer import SftpDataWriter  # noqa

    from csvpath.util.azure.azure_data_writer import AzureDataWriter  # noqa

    from csvpath.util.gcs.gcs_data_writer import GcsDataWriter  # noqa

    #
    # readers for results files
    #
    from csvpath.managers.results.readers.file_errors_reader import FileErrorsReader  # noqa

    from csvpath.managers.results.readers.file_printouts_reader import (  # noqa
        FilePrintoutsReader,  # noqa
    )  # noqa

    from csvpath.managers.results.readers.file_lines_reader import FileLinesReader  # noqa

    from csvpath.managers.results.readers.file_unmatched_reader import (  # noqa
        FileUnmatchedReader,  # noqa
    )  # noqa
except Exception:
    pass

__version__ = "0.0.1"
