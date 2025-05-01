## Results

The `results` section identifies two data publishing locations:

* The `archive` - the trusted publishing space your well-identified, valid, upgraded, and immutable data is made available
* A local `transfers` directory where copies can be directed after the data is sent to the archive

The archive is the key location for downstream data consumers. It is the internal source of truth. Data in the archive is considered known-good -- or in some cases quantifiably known-bad. The archive provides history, metadata, chain of custody, and a privileged location for discovery, retention, and access control.

You should not, however, limit your thinking to a single archive. The archive can be thought of as an effective tool for namespacing. And you can have as many fully separate archives as fits your use case. Moreover, your separate archives can be federated in metadata tools including OpenTelemetry enabled platforms (e.g. Grafana or Splunk), an OpenLineage platform like Marquez, or in a metadata database using the MySQL or Postgres integrations. The archive concept is concise, flexible, and powerful.

The archive config key is simply a path. If you are placing your archive on a local or mounted network disk, it is just a file system location. Alternatively, each archive can be domiciled on one of:
* AWS S3
* Azure Cloud Storage
* Google Cloud Storage
* SFTP

There are also options to transfer files through the transfer directory, to arbitrary SFTP servers, or to a CKAN server, but those do not provide the full archive capability and are not substitutes.


