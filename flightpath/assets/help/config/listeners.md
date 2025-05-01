## Integrations and listeners

CsvPath Framework comes with a number of pre-integrated connections to popular DataOps tools. They include:
* S3, Azure, GCS
* SFTP and SFTPPlus
* CKAN
* Slack
* OpenTelemetry platforms like DataDog and New Relic
* OpenLineage platforms like Marquez
* MySQL, Postgres, and Sqlite
* Webhooks platforms like IFTTT and Zapier

And more.

All of the integrations work in one of two ways. They are either:
* A storage backend
* An event-driven metadata consumer

You configure the storage backends in the `inputs` and `results` config.ini sections. The `listener` section is for setting up the metadata consumers.

The metadata consumer listeners are already in your generated `config.ini` file. You activate them by adding their names to the `groups` key. The key is called `groups` because it is a list of the names of sets of listeners. Each metadata consumer has a different listener or listeners -- up to a possible six. CsvPath Framework also consumes the same events, but, as you might guess, that is less configurable.

The `groups` key takes a comma separated list of names. The current list is:
* webhook -- listeners that send events to webhooks
* scripts -- for running local scripts as part of runs
* sql -- listeners that send metadata to a MySQL, Postgres, or Sqlite instance
* sqlite -- for sending data to a local Sqlite file
* default -- additional metadata capture to the inputs directories by CsvPath Framework
* otlp -- OpenTelemetry
* sftp -- SFTP as an additional transfer on a csvpath-by-csvpath level
* sftpplus -- for automated external file processing through an SFTPPlus server
* ckan -- for shipping essentially all run metadata and data results to a CKAN server
* marquez -- OpenLineage
* slack -- for sending metadata alerts via a secure Slack webhook

Most of these integrations are activated on a csvpath-by-csvpath basis. That means they may override settings or stand appart from Framework-wide or named-paths-based configuration options. They represent a finer degree of control over specific integration use cases.



