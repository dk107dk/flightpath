## Reload Ops Files

FlightPath Data gives you a window into your operations. The helper windows on the right-hand side show the three sets of operational files:
* Registered files
* Loaded csvpath files
* Run results

These may also be referred to as named-files, named-paths, and the archive.

The windows show files stored on one of the five backends supported by CsvPath Framework: the local filesystem, S3, Azure, Google Cloud Storage, and SFTP. Each window can be on any backend you like.

## Registered Files

The window on the top right shows your registered data files. When data files arrive they are registered under a name. For example, files containing orders from EU countries might be registered under the name `orders`. Files with orders from the US might also be registered under the name `orders` or you might use a different name to organize the US orders under.

Within the named-file, in our example `orders`, each registered file has its own path and a set of versions. The named-file as a whole always points to the most recently arrived `orders` data file. To work with other data files or other versions of data files with the same filename, you use references. A reference is like a very simple query that helps you select one or more files.

## Loaded Csvpath Files

The second window on the right shows the sets of csvpath statements that are ready to use in validating or upgrading data files. When you validate data files you apply one or more csvpath statements to each file. These sets of csvpath statements may be referred to as named-paths or groups.

When files arrive you can automatically validate them by pairing a named-file with a group in a run. Run results:
* Tell you if your data is valid
* Select valid or invalid data for further processing
* Modify data to upgrade it to canonical form
* Store data immutably
* Make cleaned, valid data and metadata available downstream

Named-paths groups are central to these operations.

## Run Results

The window at the bottom right is a view into your archive. The archive is an immutable store of run results. Each run generates selected data, errors, printouts, variables, and metadata. All of these outputs are available programmatically and over the FlightPath Server JSON API to downstream data consumers using references to the individual assets. Runs can also trigger webhooks, export data to SFTP, call scripts, and do other event-based processing.



